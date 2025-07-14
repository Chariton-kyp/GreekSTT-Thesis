import { HttpEventType } from '@angular/common/http';
import { Injectable, signal, computed, inject } from '@angular/core';

import { firstValueFrom, tap, catchError } from 'rxjs';

import { ApiService } from './api.service';
import { LoadingService } from './loading.service';
import { NotificationService } from './notification.service';
import { ChunkedUploadService } from './chunked-upload.service';
import { environment } from '../../../environments/environment';
import { UploadedFile, UploadResponse } from '../models/api-response.model';

export interface FileValidationResult {
  valid: boolean;
  error?: string;
}

export interface FileUploadProgress {
  fileId: string;
  filename: string;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
}

@Injectable({
  providedIn: 'root'
})
export class FileService {
  private readonly api = inject(ApiService);
  private readonly loading = inject(LoadingService);
  private readonly notification = inject(NotificationService);
  private readonly chunkedUpload = inject(ChunkedUploadService);

  // Private writable signals
  private _uploadProgress = signal<number>(0);
  private _isUploading = signal<boolean>(false);
  private _uploadError = signal<string | null>(null);
  private _uploadedFiles = signal<UploadedFile[]>([]);
  private _currentUploads = signal<Map<string, FileUploadProgress>>(new Map());

  // Public readonly signals
  readonly uploadProgress = this._uploadProgress.asReadonly();
  readonly isUploading = this._isUploading.asReadonly();
  readonly uploadError = this._uploadError.asReadonly();
  readonly uploadedFiles = this._uploadedFiles.asReadonly();
  readonly currentUploads = this._currentUploads.asReadonly();

  // Computed signals
  readonly hasFiles = computed(() => this.uploadedFiles().length > 0);
  readonly canUploadMore = computed(() => !this.isUploading() && this.uploadedFiles().length < 10);
  readonly activeUploadsCount = computed(() => {
    const uploads = this.currentUploads();
    return Array.from(uploads.values()).filter(upload => 
      upload.status === 'uploading' || upload.status === 'processing'
    ).length;
  });

  constructor() {}

  /**
   * Upload single file
   */
  async uploadFile(file: File): Promise<UploadedFile> {
    // Validate file
    const validation = this.validateFile(file);
    if (!validation.valid) {
      throw new Error(validation.error);
    }

    const fileId = this.generateFileId();
    this._isUploading.set(true);
    this._uploadError.set(null);
    this._uploadProgress.set(0);

    // Add to current uploads
    this.addUploadProgress(fileId, file.name, 0, 'uploading');

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Use upload observable for progress tracking
      const upload$ = this.api.upload<UploadResponse>('/audio/upload', formData);
      
      let uploadedFile: UploadedFile | null = null;
      
      await firstValueFrom(
        upload$.pipe(
          tap(event => {
            if (event.type === HttpEventType.UploadProgress && event.total) {
              const progress = Math.round(100 * event.loaded / event.total);
              this._uploadProgress.set(progress);
              this.updateUploadProgress(fileId, progress, 'uploading');
              this.loading.updateUploadProgress(progress);
            } else if (event.type === HttpEventType.Response && event.body) {
              this.updateUploadProgress(fileId, 100, 'completed');
              // Backend merges data dict into response, so audio_file is directly on response body
              uploadedFile = event.body.audio_file || event.body.file || null;
              const audioFile = event.body.audio_file || event.body.file;
              if (audioFile) {
                this._uploadedFiles.update(files => [...files, audioFile]);
              }
            }
          })
        )
      );

      if (!uploadedFile) {
        throw new Error('Upload failed - no file returned');
      }

      this.notification.uploadSuccess(file.name);
      this.removeUploadProgress(fileId);
      return uploadedFile;

    } catch (error: any) {
      const errorMessage = this.getErrorMessage(error);
      this._uploadError.set(errorMessage);
      this.updateUploadProgress(fileId, 0, 'error', errorMessage);
      this.notification.uploadError(errorMessage);
      throw error;
    } finally {
      this._isUploading.set(false);
      this._uploadProgress.set(0);
      this.loading.hideUpload();
    }
  }

  /**
   * Upload multiple files
   */
  async uploadFiles(files: File[]): Promise<UploadedFile[]> {
    const results: UploadedFile[] = [];
    const errors: string[] = [];

    for (const file of files) {
      try {
        const uploadedFile = await this.uploadFile(file);
        results.push(uploadedFile);
      } catch (error: any) {
        errors.push(`${file.name}: ${this.getErrorMessage(error)}`);
      }
    }

    if (errors.length > 0) {
      this.notification.validationError(errors);
    }

    return results;
  }

  /**
   * Validate file before upload
   */
  validateFile(file: File): FileValidationResult {
    // Check file size
    if (file.size > environment.maxFileSize) {
      return {
        valid: false,
        error: `Το αρχείο είναι πολύ μεγάλο. Μέγιστο μέγεθος: ${this.formatFileSize(environment.maxFileSize)}`
      };
    }

    // Check file format
    const extension = this.getFileExtension(file.name);
    const supportedFormats = [
      ...environment.supportedFormats.audio,
      ...environment.supportedFormats.video
    ];

    if (!supportedFormats.includes(extension)) {
      return {
        valid: false,
        error: `Μη υποστηριζόμενος τύπος αρχείου. Υποστηριζόμενοι τύποι: ${supportedFormats.join(', ')}`
      };
    }

    // Check if file is audio or video
    const isAudio = environment.supportedFormats.audio.includes(extension);
    const isVideo = environment.supportedFormats.video.includes(extension);

    if (!isAudio && !isVideo) {
      return {
        valid: false,
        error: 'Το αρχείο πρέπει να είναι ήχος ή βίντεο'
      };
    }

    // Additional checks
    if (file.size === 0) {
      return {
        valid: false,
        error: 'Το αρχείο είναι κενό'
      };
    }

    return { valid: true };
  }

  /**
   * Remove uploaded file
   */
  removeFile(fileId: string): void {
    this._uploadedFiles.update(files => 
      files.filter(f => f.id !== fileId)
    );
  }

  /**
   * Clear all uploaded files
   */
  clearFiles(): void {
    this._uploadedFiles.set([]);
  }

  /**
   * Get file by ID
   */
  getFile(fileId: string): UploadedFile | undefined {
    return this.uploadedFiles().find(f => f.id === fileId);
  }



  /**
   * Download file
   */
  async downloadFile(fileId: string, filename?: string): Promise<void> {
    try {
      this.loading.show('download', 'Λήψη αρχείου...');
      
      const blob = await firstValueFrom(
        this.api.download(`/audio/${fileId}/download`)
      );

      this.downloadBlob(blob, filename || `file-${fileId}`);
      this.notification.success('Επιτυχής λήψη', 'Το αρχείο λήφθηκε επιτυχώς');
    } catch (error: any) {
      this.notification.error('Σφάλμα λήψης', this.getErrorMessage(error));
    } finally {
      this.loading.hide('download');
    }
  }

  /**
   * Get file extension
   */
  private getFileExtension(filename: string): string {
    return '.' + filename.split('.').pop()?.toLowerCase() || '';
  }

  /**
   * Format file size for display
   */
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * Get file type (audio/video)
   */
  getFileType(filename: string): 'audio' | 'video' | 'unknown' {
    const extension = this.getFileExtension(filename);
    
    if (environment.supportedFormats.audio.includes(extension)) {
      return 'audio';
    }
    
    if (environment.supportedFormats.video.includes(extension)) {
      return 'video';
    }
    
    return 'unknown';
  }

  /**
   * Check if file type is supported
   */
  isFileTypeSupported(filename: string): boolean {
    return this.getFileType(filename) !== 'unknown';
  }

  /**
   * Generate unique file ID
   */
  private generateFileId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  /**
   * Add upload progress tracking
   */
  private addUploadProgress(fileId: string, filename: string, progress: number, status: FileUploadProgress['status']): void {
    this._currentUploads.update(uploads => {
      const newUploads = new Map(uploads);
      newUploads.set(fileId, { fileId, filename, progress, status });
      return newUploads;
    });
  }

  /**
   * Update upload progress
   */
  private updateUploadProgress(fileId: string, progress: number, status: FileUploadProgress['status'], error?: string): void {
    this._currentUploads.update(uploads => {
      const newUploads = new Map(uploads);
      const existing = newUploads.get(fileId);
      if (existing) {
        newUploads.set(fileId, {
          ...existing,
          progress,
          status,
          error
        });
      }
      return newUploads;
    });
  }

  /**
   * Remove upload progress tracking
   */
  private removeUploadProgress(fileId: string): void {
    this._currentUploads.update(uploads => {
      const newUploads = new Map(uploads);
      newUploads.delete(fileId);
      return newUploads;
    });
  }

  /**
   * Download blob as file
   */
  private downloadBlob(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  /**
   * Extract error message
   */
  private getErrorMessage(error: any): string {
    if (error?.details?.message) {
      return error.details.message;
    }
    if (error?.message) {
      return error.message;
    }
    return 'Παρουσιάστηκε ένα σφάλμα';
  }
}