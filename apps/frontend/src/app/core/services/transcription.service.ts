import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpEvent, HttpEventType } from '@angular/common/http';
import { Observable, BehaviorSubject, interval, EMPTY, Subject, of } from 'rxjs';
import { map, catchError, takeWhile, switchMap, tap, filter, takeUntil } from 'rxjs/operators';

import { ApiService } from './api.service';
import { NotificationService } from './notification.service';
import { WebSocketService } from './websocket.service';
import { 
  Transcription, 
  TranscriptionRequest, 
  TranscriptionStatus,
  TranscriptionListResponse,
  CreateTranscriptionResponse,
  FileUploadResponse,
  TranscriptionSegment
} from '../models/transcription.model';

export interface UploadProgress {
  fileName: string;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  message?: string;
}

@Injectable({
  providedIn: 'root'
})
export class TranscriptionService {
  private readonly apiService = inject(ApiService);
  private readonly notificationService = inject(NotificationService);
  private readonly wsService = inject(WebSocketService);

  private transcriptionSubscriptions = new Map<string, Subject<void>>();
  private readonly _transcriptions = signal<Transcription[]>([]);
  private readonly _currentTranscription = signal<Transcription | null>(null);
  private readonly _isLoading = signal<boolean>(false);
  private readonly _uploadProgress = signal<UploadProgress | null>(null);
  private readonly _paginationTotal = signal<number>(0);

  readonly transcriptions = this._transcriptions.asReadonly();
  readonly currentTranscription = this._currentTranscription.asReadonly();
  readonly isLoading = this._isLoading.asReadonly();
  readonly uploadProgress = this._uploadProgress.asReadonly();
  readonly paginationTotal = this._paginationTotal.asReadonly();

  readonly totalTranscriptions = computed(() => this.transcriptions()?.length || 0);
  readonly completedTranscriptions = computed(() => 
    this.transcriptions()?.filter(t => t.status === TranscriptionStatus.COMPLETED).length || 0
  );
  readonly processingTranscriptions = computed(() => 
    this.transcriptions()?.filter(t => t.status === TranscriptionStatus.PROCESSING).length || 0
  );

  private pollingSubject = new BehaviorSubject<boolean>(false);

  /**
   * Get all transcriptions with optional filtering and pagination
   */
  getTranscriptions(page: number = 1, perPage: number = 20, filters?: any): Observable<TranscriptionListResponse> {
    this._isLoading.set(true);
    
    const params = this.apiService.buildPaginationParams(page, perPage, filters);
    
    return this.apiService.get<TranscriptionListResponse>('/transcriptions', { params }).pipe(
      tap(response => {
        const data = response.data || response;
        const transcriptions = data.transcriptions || data || [];
        const pagination = data.pagination || {};
        this._transcriptions.set(transcriptions);
        this._paginationTotal.set(pagination.total || 0);
        this._isLoading.set(false);
      }),
      map(response => response),
      catchError(error => {
        this._isLoading.set(false);
        this._transcriptions.set([]);
        this._paginationTotal.set(0);
        throw error;
      })
    );
  }

  /**
   * Get a specific transcription by ID
   */
  getTranscription(id: string): Observable<Transcription> {
    this._isLoading.set(true);
    
    return this.apiService.get<Transcription>(`/transcriptions/${id}`).pipe(
      tap(transcription => {
        this._currentTranscription.set(transcription);
        this._isLoading.set(false);
      }),
      catchError(error => {
        this._isLoading.set(false);
        throw error;
      })
    );
  }

  /**
   * Upload audio file and create transcription - supports both File+Request and FormData interfaces
   */
  uploadAndTranscribe(
    fileOrFormData: File | FormData, 
    transcriptionRequestOrProgressCallback?: TranscriptionRequest | ((progress: UploadProgress) => void)
  ): Observable<CreateTranscriptionResponse> {
    let formData: FormData;
    let fileName: string;
    let progressCallback: ((progress: UploadProgress) => void) | undefined;

    // Handle different method signatures
    if (fileOrFormData instanceof FormData) {
      // New unified interface: uploadAndTranscribe(formData, progressCallback?)
      formData = fileOrFormData;
      fileName = 'file';
      progressCallback = transcriptionRequestOrProgressCallback as ((progress: UploadProgress) => void) | undefined;
      
      // Try to extract filename from FormData if possible
      const fileEntry = formData.get('file');
      if (fileEntry instanceof File) {
        fileName = fileEntry.name;
      }
    } else {
      // Legacy interface: uploadAndTranscribe(file, transcriptionRequest)
      const file = fileOrFormData;
      const transcriptionRequest = transcriptionRequestOrProgressCallback as TranscriptionRequest;
      fileName = file.name;
      
      // Create FormData from file and request
      formData = new FormData();
      formData.append('file', file);
      formData.append('title', transcriptionRequest.title);
      formData.append('description', transcriptionRequest.description || '');
      formData.append('language', transcriptionRequest.language);
      formData.append('template_id', transcriptionRequest.template_id?.toString() || '');
      formData.append('ai_model', transcriptionRequest.ai_model);
    }

    const initialProgress: UploadProgress = {
      fileName,
      progress: 0,
      status: 'uploading',
      message: 'Ανέβασμα αρχείου...'
    };
    
    this._uploadProgress.set(initialProgress);
    progressCallback?.(initialProgress);

    // Use unified endpoint - model selection is handled by backend based on FormData
    const endpoint = '/transcriptions/';

    // Upload with progress tracking
    return this.apiService.upload<CreateTranscriptionResponse>(endpoint, formData).pipe(
      map(event => {
        if (event.type === HttpEventType.UploadProgress && event.total) {
          const progress = Math.round((event.loaded / event.total) * 100);
          const progressUpdate: UploadProgress = {
            fileName,
            progress,
            status: 'uploading',
            message: `Ανέβασμα... ${progress}%`
          };
          
          this._uploadProgress.set(progressUpdate);
          progressCallback?.(progressUpdate);
          return null as any;
        } else if (event.type === HttpEventType.Response) {
          const completedProgress: UploadProgress = {
            fileName,
            progress: 100,
            status: 'processing',
            message: 'Επεξεργασία...'
          };
          
          this._uploadProgress.set(completedProgress);
          progressCallback?.(completedProgress);
          
          // Start WebSocket-based progress tracking
          this.startWebSocketProgressTracking(event.body!.transcription.id);
          
          return event.body!;
        }
        return null as any;
      }),
      catchError(error => {
        const errorProgress: UploadProgress = {
          fileName,
          progress: 0,
          status: 'error',
          message: 'Σφάλμα κατά το ανέβασμα'
        };
        
        this._uploadProgress.set(errorProgress);
        progressCallback?.(errorProgress);
        throw error;
      })
    );
  }

  /**
   * Transcribe from URL (YouTube, video URLs, etc.)
   */
  transcribeFromUrl(params: {
    url: string;
    title: string;
    description?: string;
    language: string;
    template_id?: number;
    ai_model?: string;
    model?: string;
    enable_comparison?: boolean;
  }): Observable<CreateTranscriptionResponse> {
    // Reset upload progress for URL transcription
    this._uploadProgress.set({
      fileName: params.title || 'URL Transcription',
      progress: 0,
      status: 'processing',
      message: 'Λήψη και επεξεργασία URL...'
    });

    // Create request payload
    const requestData = {
      url: params.url,
      title: params.title,
      description: params.description || '',
      language: params.language,
      template_id: params.template_id?.toString() || '',
      ai_model: params.ai_model || params.model || 'whisper-large-v3',
      model: params.model || params.ai_model || 'whisper-large-v3',
      enable_comparison: params.enable_comparison || false
    };

    // Use unified endpoint - model selection is handled by backend based on request data
    const endpoint = '/transcriptions/from-url';

    return this.apiService.post<CreateTranscriptionResponse>(endpoint, requestData).pipe(
      tap(response => {
        // Update progress to processing
        this._uploadProgress.set({
          fileName: params.title || 'URL Transcription',
          progress: 50,
          status: 'processing',
          message: 'Επεξεργασία URL...'
        });
        
        // Start WebSocket-based progress tracking
        this.startWebSocketProgressTracking(response.transcription.id);
      }),
      catchError(error => {
        this._uploadProgress.set({
          fileName: params.title || 'URL Transcription',
          progress: 0,
          status: 'error',
          message: 'Σφάλμα κατά την επεξεργασία URL'
        });
        throw error;
      })
    );
  }

  /**
   * Update transcription
   */
  updateTranscription(id: string, updates: Partial<Transcription>): Observable<Transcription> {
    return this.apiService.put<Transcription>(`/transcriptions/${id}`, updates).pipe(
      tap(updatedTranscription => {
        // Update in the list
        const current = this._transcriptions();
        const index = current.findIndex(t => t.id === id);
        if (index >= 0) {
          const updated = [...current];
          updated[index] = updatedTranscription;
          this._transcriptions.set(updated);
        }
        
        // Update current if it's the same transcription
        if (this._currentTranscription()?.id === id) {
          this._currentTranscription.set(updatedTranscription);
        }
        
        // Update successful
      }),
      catchError(error => {
        throw error;
      })
    );
  }


  /**
   * Download transcription in specified format with options
   */
  downloadTranscription(
    id: string, 
    format: 'txt' | 'srt' | 'docx' | 'pdf' | 'json' = 'txt',
    options?: {
      includeTimestamps?: boolean;
      includeSpeakers?: boolean;
      includeConfidence?: boolean;
    }
  ): Observable<Blob> {
    let url = `/transcriptions/${id}/download?format=${format}`;
    
    if (options) {
      if (options.includeTimestamps !== undefined) {
        url += `&includeTimestamps=${options.includeTimestamps}`;
      }
      if (options.includeSpeakers !== undefined) {
        url += `&includeSpeakers=${options.includeSpeakers}`;
      }
      if (options.includeConfidence !== undefined) {
        url += `&includeConfidence=${options.includeConfidence}`;
      }
    }
    
    return this.apiService.download(url).pipe(
      catchError(error => {
        throw error;
      })
    );
  }


  /**
   * Get transcription segments
   */
  getTranscriptionSegments(id: string): Observable<any[]> {
    return this.apiService.get<any[]>(`/transcriptions/${id}/segments`).pipe(
      catchError(error => {
        throw error;
      })
    );
  }

  /**
   * Update specific segment
   */
  updateSegment(transcriptionId: string, segmentIndex: number, text: string): Observable<any> {
    return this.apiService.put<any>(`/transcriptions/${transcriptionId}/segments/${segmentIndex}`, {
      text
    }).pipe(
      catchError(error => {
        throw error;
      })
    );
  }

  /**
   * Retry failed transcription
   */
  retryTranscription(id: string): Observable<Transcription> {
    return this.apiService.post<Transcription>(`/transcriptions/${id}/retry`, {}).pipe(
      tap(transcription => {
        // Update in the list
        const current = this._transcriptions();
        const index = current.findIndex(t => t.id === id);
        if (index >= 0) {
          const updated = [...current];
          updated[index] = transcription;
          this._transcriptions.set(updated);
        }
        
        // Update current if it's the same transcription
        if (this._currentTranscription()?.id === id) {
          this._currentTranscription.set(transcription);
        }
      }),
      catchError(error => {
        throw error;
      })
    );
  }

  /**
   * Delete transcription
   */
  deleteTranscription(id: string): Observable<any> {
    return this.apiService.delete(`/transcriptions/${id}`).pipe(
      tap(() => {
        // Remove from the list
        const current = this._transcriptions();
        const updated = current.filter(t => t.id !== id);
        this._transcriptions.set(updated);
        this._paginationTotal.set(Math.max(0, this._paginationTotal() - 1));
        
        // Clear current if it's the deleted transcription
        if (this._currentTranscription()?.id === id) {
          this._currentTranscription.set(null);
        }
      }),
      catchError(error => {
        throw error;
      })
    );
  }

  /**
   * Get available templates
   */
  getTemplates(): Observable<any[]> {
    return this.apiService.get<any[]>('/templates').pipe(
      catchError(error => {
        throw error;
      })
    );
  }

  /**
   * Update transcription segments
   */
  updateSegments(transcriptionId: string, segments: TranscriptionSegment[]): Observable<any> {
    return this.apiService.put(`/transcriptions/${transcriptionId}/segments`, { segments }).pipe(
      tap(() => {
        this.notificationService.success('Τα τμήματα ενημερώθηκαν επιτυχώς');
      }),
      catchError(error => {
        this.notificationService.error('Σφάλμα κατά την ενημέρωση των τμημάτων');
        throw error;
      })
    );
  }

  createShareLink(transcriptionId: string): Observable<{ link: string; expiresAt: string }> {
    return this.apiService.post<{ link: string; expiresAt: string }>(`/transcriptions/${transcriptionId}/share`, {}).pipe(
      catchError(error => {
        this.notificationService.error('Σφάλμα κατά τη δημιουργία συνδέσμου κοινοποίησης');
        throw error;
      })
    );
  }


  /**
   * Start WebSocket-based real-time progress tracking
   */
  private startWebSocketProgressTracking(transcriptionId: string): void {
    // Clean up any existing subscriptions for this transcription
    this.cleanupTranscriptionSubscriptions(transcriptionId);
    
    // Create destroy subject for this transcription
    const destroy$ = new Subject<void>();
    this.transcriptionSubscriptions.set(transcriptionId, destroy$);


    // Ensure WebSocket is connected
    if (!this.wsService.getConnectionStatus()) {
      this.wsService.autoConnect();
    }

    // Subscribe to error events IMMEDIATELY (before room joining to catch early errors)
    this.wsService.getErrorEvents(transcriptionId).pipe(
      takeUntil(destroy$),
      tap(error => {
        this._uploadProgress.set({
          fileName: this._uploadProgress()?.fileName || '',
          progress: 0,
          status: 'error',
          message: error.message || 'Σφάλμα κατά την επεξεργασία'
        });
        
        // Refresh transcriptions list to show error state
        this.getTranscriptions().subscribe();
        
        // Clean up subscriptions after error
        this.cleanupTranscriptionSubscriptions(transcriptionId);
      })
    ).subscribe({
      error: (err) => {}
    });

    // Join transcription room for real-time updates
    this.wsService.joinTranscriptionRoom(transcriptionId).then(() => {
      
      // Subscribe to progress updates
      this.wsService.getProgressUpdates(transcriptionId).pipe(
        takeUntil(destroy$),
        tap(progress => {
          this._uploadProgress.set({
            fileName: this._uploadProgress()?.fileName || '',
            progress: progress.percentage,
            status: this.mapStageToProgressStatus(progress.stage),
            message: progress.message
          });
        })
      ).subscribe({
        error: (err) => {}
      });

      // Subscribe to completion events
      this.wsService.getCompletionEvents(transcriptionId).pipe(
        takeUntil(destroy$),
        tap(completion => {
          this._uploadProgress.set({
            fileName: this._uploadProgress()?.fileName || '',
            progress: 100,
            status: 'completed',
            message: completion.message
          });
          
          // Refresh transcriptions list
          this.getTranscriptions().subscribe();
          
          // Clean up subscriptions after completion
          this.cleanupTranscriptionSubscriptions(transcriptionId);
        })
      ).subscribe({
        error: (err) => {}
      });
      
    }).catch(error => {
      this.startPollingForTranscription(transcriptionId);
    });
  }

  /**
   * Clean up WebSocket subscriptions for a specific transcription
   */
  private cleanupTranscriptionSubscriptions(transcriptionId: string): void {
    const destroy$ = this.transcriptionSubscriptions.get(transcriptionId);
    if (destroy$) {
      destroy$.next();
      destroy$.complete();
      this.transcriptionSubscriptions.delete(transcriptionId);
    }
  }

  /**
   * Map WebSocket stage to progress status
   */
  private mapStageToProgressStatus(stage: string): 'uploading' | 'processing' | 'completed' | 'error' {
    switch (stage) {
      case 'completed':
        return 'completed';
      case 'error':
      case 'failed':
        return 'error';
      case 'initializing':
      case 'preprocessing':
      case 'ai_processing':
      case 'transcribing':
      case 'finalizing':
        return 'processing';
      default:
        return 'processing';
    }
  }

  /**
   * Fallback: Start polling for transcription status updates (legacy)
   */
  private startPollingForTranscription(transcriptionId: string): void {
    this.pollingSubject.next(true);
    
    interval(2000).pipe(
      switchMap(() => {
        if (!this.pollingSubject.value) {
          return EMPTY;
        }
        return this.apiService.get<Transcription>(`/transcriptions/${transcriptionId}`);
      }),
      takeWhile(transcription => {
        const shouldContinue = transcription.status === TranscriptionStatus.PROCESSING || 
                             transcription.status === TranscriptionStatus.PENDING;
        
        if (!shouldContinue) {
          // Update progress to completed
          this._uploadProgress.set({
            fileName: this._uploadProgress()?.fileName || '',
            progress: 100,
            status: transcription.status === TranscriptionStatus.COMPLETED ? 'completed' : 'error',
            message: transcription.status === TranscriptionStatus.COMPLETED ? 
              'Η μεταγραφή ολοκληρώθηκε!' : 'Σφάλμα κατά την επεξεργασία'
          });
          
          // Stop polling
          this.pollingSubject.next(false);
          
          // Refresh transcriptions list
          this.getTranscriptions().subscribe();
        }
        
        return shouldContinue;
      }),
      catchError(error => {
        this.pollingSubject.next(false);
        this._uploadProgress.set({
          fileName: this._uploadProgress()?.fileName || '',
          progress: 0,
          status: 'error',
          message: 'Σφάλμα κατά τον έλεγχο κατάστασης'
        });
        return EMPTY;
      })
    ).subscribe();
  }

  /**
   * Stop polling for status updates
   */
  stopPolling(): void {
    this.pollingSubject.next(false);
  }

  /**
   * Clear upload progress
   */
  clearUploadProgress(): void {
    this._uploadProgress.set(null);
  }

  /**
   * Clear current transcription
   */
  clearCurrentTranscription(): void {
    this._currentTranscription.set(null);
  }

  /**
   * Validate file for upload
   */
  validateFile(file: File): { valid: boolean; error?: string } {
    const maxSize = 8 * 1024 * 1024 * 1024;

    if (file.size > maxSize) {
      return { valid: false, error: 'Το αρχείο είναι πολύ μεγάλο. Μέγιστο μέγεθος: 8GB' };
    }

    // Simplified validation - PrimeNG handles file type checking
    // This is mainly for backend compatibility and edge case validation
    const allowedExtensions = [
      '.mp3', '.wav', '.m4a', '.flac', '.ogg', '.webm', '.wma', '.aac', '.opus',
      '.mp4', '.mov', '.avi', '.mkv', '.wmv'
    ];

    const fileName = file.name.toLowerCase();
    const hasValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext));
    
    if (!hasValidExtension) {
      return { 
        valid: false, 
        error: 'Μη υποστηριζόμενος τύπος αρχείου. Υποστηριζόμενα: MP3, WAV, M4A, FLAC, OGG, WebM, WMA, AAC, Opus, MP4, MOV, AVI, MKV, WMV' 
      };
    }

    return { valid: true };
  }

  /**
   * Format time in seconds to MM:SS format
   */
  formatTime(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  }

  /**
   * Format duration in seconds to human readable format
   */
  formatDuration(seconds: number): string {
    if (seconds < 60) {
      return `${Math.round(seconds)}δ`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = Math.round(seconds % 60);
      return `${minutes}λ ${remainingSeconds}δ`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}ω ${minutes}λ`;
    }
  }

  /**
   * Copy text to clipboard
   */
  async copyToClipboard(text: string): Promise<boolean> {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (err) {
      // Fallback for older browsers
      const textarea = document.createElement('textarea');
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      return true;
    }
  }


  /**
   * Export transcription with advanced options
   */
  async exportTranscription(id: string, options: {
    format: string;
    includeTimestamps?: boolean;
    includeSpeakers?: boolean;
    includeConfidence?: boolean;
    [key: string]: any;
  }): Promise<Blob> {
    const response = await this.apiService.execute(
      () => this.apiService.post<Blob>(
        `/transcriptions/${id}/export`,
        options,
        { responseType: 'blob' }
      )
    );
    return response;
  }

  /**
   * Reprocess transcription with different model
   */
  async reprocessTranscription(id: string, model: string): Promise<Transcription> {
    const response = await this.apiService.execute(
      () => this.apiService.post<Transcription>(
        `/transcriptions/${id}/reprocess`,
        { model }
      )
    );
    return response;
  }

  async shareTranscription(id: string, options?: {
    expiresInDays?: number;
    allowDownload?: boolean;
    [key: string]: any;
  }): Promise<{ link: string; expiresAt: string }> {
    const response = await this.apiService.execute(
      () => this.apiService.post<{ link: string; expiresAt: string }>(
        `/transcriptions/${id}/share`,
        options || {}
      )
    );
    return response;
  }

  /**
   * Bulk update all segments for a transcription
   */
  async updateAllSegments(id: string, segments: any[]): Promise<void> {
    await this.apiService.execute(
      () => this.apiService.put(
        `/transcriptions/${id}/segments`,
        { segments }
      )
    );
  }

  /**
   * Bulk operations for transcriptions
   */
  async bulkUpdateSegments(transcriptionIds: string[], segmentUpdates: any): Promise<void> {
    await this.apiService.execute(
      () => this.apiService.post(
        `/transcriptions/bulk/segments/update`,
        { transcription_ids: transcriptionIds, updates: segmentUpdates }
      )
    );
  }

  async bulkDeleteTranscriptions(transcriptionIds: string[]): Promise<void> {
    await this.apiService.execute(
      () => this.apiService.post(
        `/transcriptions/bulk/delete`,
        { transcription_ids: transcriptionIds }
      )
    );
  }

  async bulkUpdateStatus(transcriptionIds: string[], status: string): Promise<void> {
    await this.apiService.execute(
      () => this.apiService.post(
        `/transcriptions/bulk/status/update`,
        { transcription_ids: transcriptionIds, status }
      )
    );
  }

  async bulkExportTranscriptions(transcriptionIds: string[], format: string): Promise<Blob> {
    const response = await this.apiService.execute(
      () => this.apiService.post<Blob>(
        `/transcriptions/bulk/export`,
        { transcription_ids: transcriptionIds, format },
        { responseType: 'blob' }
      )
    );
    return response;
  }

  async bulkReprocessTranscriptions(transcriptionIds: string[], model: string): Promise<void> {
    await this.apiService.execute(
      () => this.apiService.post(
        `/transcriptions/bulk/reprocess`,
        { transcription_ids: transcriptionIds, model }
      )
    );
  }


  /**
   * Get supported formats for transcriptions
   */
  async getSupportedFormats(): Promise<string[]> {
    const response = await this.apiService.execute(
      () => this.apiService.get<{ formats: string[] }>('/transcriptions/formats'),
      { silentRequest: true }
    );
    return response.formats || [];
  }

  /**
   * Get available AI models
   */
  async getAvailableModels(): Promise<any[]> {
    const response = await this.apiService.execute(
      () => this.apiService.get<{ models: any[] }>('/transcriptions/ai-models'),
      { silentRequest: true }
    );
    return response.models || [];
  }

  /**
   * Validate URL for video transcription
   */
  async validateUrl(url: string): Promise<{ valid: boolean; info?: any }> {
    const response = await this.apiService.execute(
      () => this.apiService.post<{ valid: boolean; info?: any }>(
        '/transcriptions/validate-url',
        { url }
      )
    );
    return response;
  }

  /**
   * Get batch transcription status
   */
  async getBatchStatus(batchId: string): Promise<any> {
    const response = await this.apiService.execute(
      () => this.apiService.get(`/transcriptions/batch/${batchId}/status`),
      { silentRequest: true }
    );
    return response;
  }

  /**
   * Evaluate transcription with ground truth text
   */
  evaluateTranscription(transcriptionId: string, groundTruth: string, notes?: string): Observable<any> {
    return this.apiService.post(`/transcriptions/${transcriptionId}/evaluate`, {
      ground_truth: groundTruth,
      notes: notes || ''
    }).pipe(
      tap((response: any) => {
        try {
          
          // Update current transcription if it matches - handle direct response format
          const current = this._currentTranscription();
          if (current && current.id === transcriptionId && response?.transcription) {
            this._currentTranscription.set({
              ...current,
              ...response.transcription
            });
          }
          
          // Update transcriptions list
          if (response?.transcription) {
            const transcriptions = this._transcriptions();
            const index = transcriptions.findIndex(t => t.id === transcriptionId);
            if (index !== -1) {
              const updated = [...transcriptions];
              updated[index] = { ...updated[index], ...response.transcription };
              this._transcriptions.set(updated);
            }
          }
        } catch (error) {
          // Don't throw - let the response continue to the component
        }
      })
    );
  }

  /**
   * Get WER/CER evaluation results for a transcription
   */
  getWerCerResults(transcriptionId: string): Observable<any> {
    return this.apiService.get(`/transcriptions/${transcriptionId}/wer-cer`).pipe(
      catchError(error => {
        throw error;
      })
    );
  }
}