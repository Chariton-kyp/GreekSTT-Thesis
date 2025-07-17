import { animate, style, transition, trigger } from '@angular/animations';
import { CommonModule } from '@angular/common';
import { Component, computed, DestroyRef, effect, inject, OnDestroy, OnInit, signal, ViewChild } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { Subject, Subscription } from 'rxjs';

import { ConfirmationService, MessageService } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { DatePickerModule } from 'primeng/datepicker';
import { DialogModule } from 'primeng/dialog';
import { Menu, MenuModule } from 'primeng/menu';
import { ProgressBarModule } from 'primeng/progressbar';
import { SelectModule } from 'primeng/select';
import { SelectButtonModule } from 'primeng/selectbutton';
import { TextareaModule } from 'primeng/textarea';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';

import { ApiService } from '../../../core/services/api.service';
import { AuthService } from '../../../core/services/auth.service';
import { DateService } from '../../../core/services/date.service';
import { NotificationService } from '../../../core/services/notification.service';
import { TranscriptionService } from '../../../core/services/transcription.service';
import { WebSocketService } from '../../../core/services/websocket.service';

import { Transcription, TranscriptionStatus } from '../../../core/models/transcription.model';

interface AudioRecorder {
  start(): Promise<void>;
  stop(): Promise<Blob>;
  isRecording: boolean;
  stream?: MediaStream;
  analyser?: AnalyserNode;
  audioContext?: AudioContext;
}

interface WaveformBar {
  height: number;
  opacity: number;
  id: number;
}

interface AudioDevice {
  deviceId: string;
  label: string;
  kind: string;
  isDefault?: boolean;
}

interface AudioVisualizationData {
  volume: number;
  frequency: Uint8Array;
  averageVolume: number;
  isActive: boolean;
}

interface UrlPreview {
  thumbnail?: string;
  title?: string;
  duration?: string;
  platform?: string;
  isValid?: boolean;
  uploader?: string;
  viewCount?: number;
  uploadDate?: string;
}

interface SortOption {
  label: string;
  value: string;
}

type TranscriptionMethod = 'upload' | 'url' | 'record' | null;

@Component({
  selector: 'app-transcription-home',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    ToastModule,
    ButtonModule,
    SelectModule,
    SelectButtonModule,
    DatePickerModule,
    TooltipModule,
    ProgressBarModule,
    MenuModule,
    TextareaModule,
    ConfirmDialogModule,
    DialogModule
  ],
  templateUrl: './transcription-home.component.html',
  styleUrls: ['./transcription-home.component.scss'],
  providers: [MessageService, ConfirmationService],
  animations: [
    trigger('slideDown', [
      transition(':enter', [
        style({ height: '0', opacity: 0, overflow: 'hidden' }),
        animate('300ms ease-out', style({ height: '*', opacity: 1 }))
      ]),
      transition(':leave', [
        animate('300ms ease-in', style({ height: '0', opacity: 0 }))
      ])
    ]),
    trigger('filterPanel', [
      transition(':enter', [
        style({ height: 0, opacity: 0 }),
        animate('200ms ease-out', style({ height: '*', opacity: 1 }))
      ]),
      transition(':leave', [
        animate('200ms ease-in', style({ height: 0, opacity: 0 }))
      ])
    ])
  ]
})
export class TranscriptionHomeComponent implements OnInit, OnDestroy {
  private router = inject(Router);
  private transcriptionService = inject(TranscriptionService);
  protected authService = inject(AuthService);
  private notificationService = inject(NotificationService);
  private messageService = inject(MessageService);
  private apiService = inject(ApiService);
  private dateService = inject(DateService);
  private confirmationService = inject(ConfirmationService);
  private wsService = inject(WebSocketService);
  private destroyRef = inject(DestroyRef);
  
  Math = Math;

  showOnboarding = signal(false);

  selectedFile = signal<File | null>(null);
  isDragOver = signal(false);
  isUploading = signal(false);
  uploadProgress = signal(0);
  fileValidationError = signal<string | null>(null);
  dragDepth = signal(0);

  urlInput = signal('');
  isUrlValid = signal(false);
  isValidatingUrl = signal(false);
  urlError = signal<string | null>(null);
  urlPreview = signal<UrlPreview | null>(null);
  isLoadingPreview = signal(false);

  isRecording = signal(false);
  recordingTime = signal(0);
  recordedAudio = signal<string | null>(null);
  recordingTimer?: any;
  audioRecorder?: AudioRecorder;
  activeBars = signal<WaveformBar[]>([]);
  
  availableAudioDevices = signal<AudioDevice[]>([]);
  selectedAudioDevice = signal<string>('default');
  isLoadingDevices = signal(false);
  devicePermissionGranted = signal(false);
  
  audioVisualization = signal<AudioVisualizationData>({
    volume: 0,
    frequency: new Uint8Array(32),
    averageVolume: 0,
    isActive: false
  });
  visualizationAnimationId?: number;

  isAudioPlaying = signal(false);
  isAudioMuted = signal(false);
  currentAudioTime = signal(0);
  audioDuration = signal(0);
  audioVolume = signal(1);
  private audioProgressInterval: any = null;
  private audioReadyToPlay = signal(false);
  private simulatedProgressInterval: any = null;
  private audioActuallyPlaying = signal(false);
  audioProgress = computed(() => {
    const duration = this.audioDuration();
    const current = this.currentAudioTime();
    
    if (!isFinite(duration) || duration <= 0) return 0;
    if (!isFinite(current) || current < 0) return 0;
    
    const progress = (current / duration) * 100;
    return Math.min(100, Math.max(0, progress));
  });

  recentTranscriptions = signal<Transcription[]>([]);
  currentPage = signal(1);
  hasMorePages = signal(false);
  isLoading = signal(false);
  totalTranscriptions = signal(0);
  
  isFiltering = signal(false);
  
  private filterDebounceTimer?: any;
  
  sortBy = signal<string>('created_at_desc');
  dateFilter = signal<Date[] | null>(null);
  statusFilter = signal<string>('all');
  
  totalPages = computed(() => {
    const total = this.totalTranscriptions();
    const itemsPerPage = 5;
    return Math.ceil(total / itemsPerPage);
  });

  sortOptions: SortOption[] = [
    { label: 'Νεότερα πρώτα', value: 'created_at_desc' },
    { label: 'Παλαιότερα πρώτα', value: 'created_at_asc' },
    { label: 'Όνομα Α-Ω', value: 'title_asc' },
    { label: 'Όνομα Ω-Α', value: 'title_desc' },
    { label: 'Διάρκεια (μικρή-μεγάλη)', value: 'duration_asc' },
    { label: 'Διάρκεια (μεγάλη-μικρή)', value: 'duration_desc' }
  ];

  statusFilterOptions = [
    { label: 'Όλες', value: 'all' },
    { label: 'Ολοκληρωμένες', value: 'completed' },
    { label: 'Επεξεργασία', value: 'processing' },
    { label: 'Σφάλμα', value: 'failed' },
    { label: 'Αναμονή', value: 'pending' }
  ];

  private readonly acceptedTypes = '.mp3,.wav,.m4a,.mp4,.mov,.avi,.mkv,.webm,.ogg,.flac,.aac,.opus,.wma,.wmv';
  private readonly maxFileSize = 8 * 1024 * 1024 * 1024;
  private readonly maxRecordingTime = 6 * 60 * 60;

  private emailWarningShown = signal<boolean>(false);

  @ViewChild('menu') menu!: Menu;
  selectedTranscription: Transcription | null = null;
  menuItems: any[] = [];
  
  showRetryDialog = signal<boolean>(false);
  retryTranscription_data = signal<Transcription | null>(null);
  isRetrying = signal<boolean>(false);
  
  showFilters = signal<boolean>(false);

  selectedModel = signal<'whisper' | 'wav2vec2' | 'both'>('whisper');

  private mapModelName(modelName: string): string {
    const modelMapping: { [key: string]: string } = {
      'whisper': 'whisper-large-v3',
      'wav2vec2': 'wav2vec2-greek',
      'both': 'both'
    };
    return modelMapping[modelName] || 'whisper-large-v3';
  }

  private wsSubscriptions: Subscription[] = [];
  private destroy$ = new Subject<void>();

  constructor() {
    effect(() => {
      const isAuthenticated = this.authService.isAuthenticated();
      const isEmailVerified = this.authService.isEmailVerified();
      const isInitialized = this.authService.isInitialized();
      
      console.log('Email verification effect:', {
        isAuthenticated,
        isEmailVerified, 
        isInitialized,
        warningShown: this.emailWarningShown()
      });
      
      if (isInitialized && isAuthenticated && !isEmailVerified && !this.emailWarningShown()) {
        this.emailWarningShown.set(true);
        setTimeout(() => {
          this.notificationService.warning(
            'Παρακαλούμε επιβεβαιώστε το email σας για να μπορείτε να ανεβάσετε αρχεία.'
          );
        }, 1000);
      }
      
      if (isEmailVerified) {
        this.emailWarningShown.set(false);
      }
    });
  }

  ngOnInit() {
    this.setupWebSocketListeners();
    this.loadRecentTranscriptions();
    this.checkFirstTimeUser();
    this.initializeAudioDevices();
  }

  private checkFirstTimeUser() {
    const hasSeenOnboarding = localStorage.getItem('greekstt-research_onboarding_completed');
    const hasTranscriptions = this.recentTranscriptions().length > 0;
    
    if (!hasSeenOnboarding && !hasTranscriptions) {
      this.showOnboarding.set(true);
    }
  }

  ngOnDestroy() {
    this.stopRecording();
    if (this.recordingTimer) {
      clearInterval(this.recordingTimer);
    }
    
    if (this.visualizationAnimationId) {
      cancelAnimationFrame(this.visualizationAnimationId);
    }
    
    this.stopSmoothProgressTracking();
    this.stopSimulatedProgress();
    
    if (this.filterDebounceTimer) {
      clearTimeout(this.filterDebounceTimer);
    }
    
    // Clean up WebSocket subscriptions
    this.wsSubscriptions.forEach(sub => sub.unsubscribe());
    this.wsSubscriptions = [];
    
    const audioUrl = this.recordedAudio();
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
    
    this.wsSubscriptions.forEach(sub => sub.unsubscribe());
    this.wsSubscriptions = [];
    this.destroy$.next();
    this.destroy$.complete();
  }

  onDragEnter(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.dragDepth.set(this.dragDepth() + 1);
    
    if (this.dragDepth() === 1) {
      this.isDragOver.set(true);
    }
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    
    const items = event.dataTransfer?.items;
    if (items && items.length > 0) {
      const item = items[0];
      const isValidType = this.isValidFileType(item.type);
      event.dataTransfer!.dropEffect = isValidType ? 'copy' : 'none';
    }
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.dragDepth.set(this.dragDepth() - 1);
    
    if (this.dragDepth() === 0) {
      this.isDragOver.set(false);
    }
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver.set(false);
    this.dragDepth.set(0);

    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.handleFileSelection(files[0]);
    }
  }

  private isValidFileType(mimeType: string): boolean {
    const validTypes = [
      'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav', 'audio/wave',
      'audio/x-m4a', 'audio/m4a', 'audio/mp4', 'audio/x-mp4', 'audio/mp4a-latm',
      'audio/flac', 'audio/x-flac', 'audio/ogg', 'audio/webm',
      'audio/x-ms-wma', 'audio/wma', 'audio/aac', 'audio/x-aac', 'audio/aacp',
      'audio/opus', 'audio/x-opus',
      'video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo',
      'video/x-matroska', 'video/mkv', 'video/x-ms-wmv', 'video/wmv', 'video/webm'
    ];
    return validTypes.includes(mimeType) || mimeType.startsWith('audio/') || mimeType.startsWith('video/');
  }

  onFileSelected(event: any) {
    const file = event.target.files?.[0];
    if (file) {
      this.handleFileSelection(file);
    }
  }

  private handleFileSelection(file: File) {
    console.log('=== TranscriptionHome: File selection started ===');
    console.log('File details:', {
      name: file.name,
      type: file.type,
      size: file.size,
      extension: file.name.split('.').pop()?.toLowerCase()
    });

    this.fileValidationError.set(null);

    const validationResult = this.validateFile(file);
    console.log('Validation result:', validationResult);
    
    if (!validationResult.isValid) {
      console.log('❌ File validation failed:', validationResult.error);
      this.fileValidationError.set(validationResult.error!);
      this.notificationService.error(validationResult.error!);
      return;
    }

    console.log('✅ File validation passed');
    this.selectedFile.set(file);
    this.showFilePreview(file);
  }

  private validateFile(file: File): { isValid: boolean; error?: string } {
    console.log('Validating file type...');
    const isValidMimeType = this.isValidFileType(file.type);
    const isValidExt = this.isValidFileExtension(file.name);
    
    console.log('MIME type validation:', { 
      mimeType: file.type, 
      isValid: isValidMimeType 
    });
    console.log('Extension validation:', { 
      extension: file.name.split('.').pop()?.toLowerCase(), 
      isValid: isValidExt 
    });
    
    if (!isValidMimeType && !isValidExt) {
      console.log('❌ Both MIME type and extension validation failed');
      return {
        isValid: false,
        error: 'Μη υποστηριζόμενος τύπος αρχείου. Υποστηρίζονται: MP3, WAV, M4A, FLAC, OGG, WebM, WMA, AAC, Opus, MP4, MOV, AVI, MKV, WMV'
      };
    }

    if (file.size > this.maxFileSize) {
      return {
        isValid: false,
        error: `Το αρχείο είναι πολύ μεγάλο (${this.formatFileSize(file.size)}). Μέγιστο μέγεθος: 8GB`
      };
    }

    if (file.size > 1024 * 1024 * 1024) {
      this.notificationService.warning('Μεγάλο αρχείο - η επεξεργασία μπορεί να διαρκέσει περισσότερο');
    }

    if (file.size < 1024) {
      return {
        isValid: false,
        error: 'Το αρχείο είναι πολύ μικρό. Ελάχιστο μέγεθος: 1KB'
      };
    }

    return { isValid: true };
  }

  private showFilePreview(file: File) {
    this.notificationService.info(
      `Αρχείο επιλέχθηκε: ${file.name} (${this.formatFileSize(file.size)})`
    );
  }

  private isValidFileExtension(filename: string): boolean {
    const ext = filename.toLowerCase().split('.').pop();
    const validExtensions = ['mp3', 'wav', 'm4a', 'flac', 'ogg', 'webm', 'wma', 'aac', 'opus', 'mp4', 'mov', 'avi', 'mkv', 'wmv'];
    return validExtensions.includes(ext || '');
  }

  uploadFile() {
    const file = this.selectedFile();
    if (!file) return;

    if (!this.authService.isEmailVerified()) {
      this.notificationService.error('Παρακαλούμε επιβεβαιώστε το email σας πρώτα');
      return;
    }

    this.isUploading.set(true);
    
    // Ensure model is never null/undefined and map to backend model name
    const currentModel = this.selectedModel() || 'whisper';
    const mappedModel = this.mapModelName(currentModel);
    console.log('Upload: Selected model =', currentModel, '-> Mapped =', mappedModel);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', file.name.replace(/\.[^/.]+$/, ''));
    formData.append('language', 'el');
    formData.append('ai_model', mappedModel);
    formData.append('enable_comparison', currentModel === 'both' ? 'true' : 'false');

    // Call transcription service with progress tracking
    this.transcriptionService.uploadAndTranscribe(
      formData,
      (progress) => this.uploadProgress.set(progress.progress)
    ).subscribe({
      next: (result) => {
        if (result) {
          // Enhanced success message with model info
          const modelName = currentModel === 'both' ? 'Σύγκριση μοντέλων' : 
                           currentModel === 'whisper' ? 'Whisper' : 'Wav2Vec2';
          
          this.notificationService.success(
            `🎉 Επιτυχία! Το αρχείο "${file.name}" ανέβηκε και η επεξεργασία ξεκίνησε με το μοντέλο ${modelName}. ` +
            `Θα ενημερωθείτε όταν η μεταγραφή ολοκληρωθεί!`,
            'Μεταφόρτωση Επιτυχής',
            { life: 8000 }
          );
          
          // Log detailed success info
          console.log('Upload successful:', {
            file: file.name,
            size: file.size,
            model: currentModel,
            transcriptionId: result.transcription?.id,
            message: result.message
          });
          
          // Reset file selection and refresh transcriptions list instead of navigating
          this.selectedFile.set(null);
          // Reset to first page to show the new transcription at the top
          this.currentPage.set(1);
          this.loadRecentTranscriptions();
          // Start auto-refresh to monitor progress
          this.joinTranscriptionRooms();
        }
      },
      error: (error: any) => {
        console.error('Upload error:', error);
        
        // Extract error message from different possible formats
        let errorMessage = 'Σφάλμα κατά τη μεταφόρτωση';
        if (error?.error?.error) {
          errorMessage = error.error.error;
        } else if (error?.message) {
          errorMessage = error.message;
        } else if (typeof error === 'string') {
          errorMessage = error;
        }
        
        this.notificationService.error(
          `❌ Αποτυχία μεταφόρτωσης: ${errorMessage}. Παρακαλούμε δοκιμάστε ξανά.`,
          'Σφάλμα Μεταφόρτωσης',
          { life: 10000 }
        );
        this.isUploading.set(false);
      },
      complete: () => {
        this.isUploading.set(false);
      }
    });
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  }

  // Enhanced URL Section Methods
  async onUrlInput() {
    const url = this.urlInput().trim();
    this.urlError.set(null);
    this.urlPreview.set(null);
    
    if (url.length < 10) {
      this.isUrlValid.set(false);
      return;
    }

    const isValidFormat = this.validateUrlFormat(url);
    this.isUrlValid.set(isValidFormat);
    
    if (isValidFormat) {
      // Debounce the preview loading
      setTimeout(() => {
        if (this.urlInput().trim() === url) {
          this.loadUrlPreview(url);
        }
      }, 500);
    }
  }

  private async loadUrlPreview(url: string) {
    this.isLoadingPreview.set(true);
    
    try {
      const preview = await this.generateUrlPreview(url);
      this.urlPreview.set(preview);
    } catch (error) {
      console.error('Error loading URL preview:', error);
      this.urlError.set('Δεν ήταν δυνατή η φόρτωση προεπισκόπησης');
    } finally {
      this.isLoadingPreview.set(false);
    }
  }

  private async generateUrlPreview(url: string): Promise<UrlPreview> {
    try {
      // Call backend API to get real metadata
      const response = await this.apiService.post<any>('/transcriptions/validate-url', {
        url: url
      }).toPromise();

      if (response?.success && response?.metadata) {
        const metadata = response.metadata;
        
        // Show success notification
        if (response.message) {
          this.notificationService.success(
            response.message,
            'URL Validation',
            { life: 4000 }
          );
        }
        
        return {
          platform: metadata.platform || 'unknown',
          title: metadata.title || 'Unknown Video',
          duration: metadata.duration_string || '00:00',
          thumbnail: metadata.thumbnail || `/assets/icons/platforms/${metadata.platform || 'unknown'}.svg`,
          isValid: true,
          uploader: metadata.uploader,
          viewCount: metadata.view_count,
          uploadDate: metadata.upload_date
        };
      } else {
        throw new Error(response?.message || 'Failed to get video metadata');
      }

    } catch (error: any) {
      console.error('URL validation error:', error);
      
      // Extract platform information for fallback display
      try {
        const urlObj = new URL(url);
        const hostname = urlObj.hostname.toLowerCase();
        
        let platform = 'unknown';
        if (hostname.includes('youtube.com') || hostname.includes('youtu.be')) {
          platform = 'youtube';
        } else if (hostname.includes('facebook.com') || hostname.includes('fb.watch')) {
          platform = 'facebook';
        } else if (hostname.includes('tiktok.com')) {
          platform = 'tiktok';
        } else if (hostname.includes('vimeo.com')) {
          platform = 'vimeo';
        } else if (hostname.includes('instagram.com')) {
          platform = 'instagram';
        }
      } catch (urlError) {
        // Invalid URL
      }

      // Return error state with platform info
      throw new Error(error.error?.message || error.message || 'Failed to process URL. Make sure the URL is valid and from a supported platform.');
    }
  }

  private validateUrlFormat(url: string): boolean {
    try {
      const urlObj = new URL(url);
      const supportedDomains = [
        'youtube.com', 'youtu.be', 'vimeo.com'
      ];
      
      return supportedDomains.some(domain => 
        urlObj.hostname.includes(domain) || urlObj.hostname.includes(`www.${domain}`)
      );
    } catch {
      return false;
    }
  }

  isValidUrl(): boolean {
    return this.isUrlValid() && this.urlInput().trim().length > 0;
  }

  transcribeUrl() {
    const url = this.urlInput().trim();
    if (!this.isValidUrl()) return;

    if (!this.authService.isEmailVerified()) {
      this.notificationService.error('Παρακαλούμε επιβεβαιώστε το email σας πρώτα');
      return;
    }

    this.isValidatingUrl.set(true);
    
    // Ensure model is never null/undefined and map to backend model name
    const currentModel = this.selectedModel() || 'whisper';
    const mappedModel = this.mapModelName(currentModel);
    console.log('URL: Selected model =', currentModel, '-> Mapped =', mappedModel);
    
    this.transcriptionService.transcribeFromUrl({
      url: url,
      language: 'el',
      title: `Μεταγραφή από ${new URL(url).hostname}`,
      ai_model: mappedModel,
      enable_comparison: currentModel === 'both'
    }).subscribe({
      next: (result) => {
        this.notificationService.success('Η μεταγραφή από URL ξεκίνησε επιτυχώς!');
        // Reset URL input and refresh transcriptions list instead of navigating
        this.urlInput.set('');
        this.urlPreview.set(null);
        // Reset to first page to show the new transcription at the top
        this.currentPage.set(1);
        this.loadRecentTranscriptions();
        // Start auto-refresh to monitor progress
        this.joinTranscriptionRooms();
      },
      error: (error: any) => {
        console.error('URL transcription error:', error);
        this.urlError.set(error.message || 'Σφάλμα κατά τη μεταγραφή από URL');
        this.isValidatingUrl.set(false);
      },
      complete: () => {
        this.isValidatingUrl.set(false);
      }
    });
  }

  // Audio Device Management Methods
  private async initializeAudioDevices() {
    try {
      this.isLoadingDevices.set(true);
      
      // Request permission to access audio devices
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { echoCancellation: true, noiseSuppression: true } 
      });
      
      // Stop the stream immediately - we just needed permission
      stream.getTracks().forEach(track => track.stop());
      
      this.devicePermissionGranted.set(true);
      await this.loadAudioDevices();
      
    } catch (error) {
      console.warn('Failed to get audio device permission:', error);
      this.devicePermissionGranted.set(false);
      this.notificationService.warning('Δεν έχετε δώσει άδεια για πρόσβαση στο μικρόφωνο');
    } finally {
      this.isLoadingDevices.set(false);
    }
  }

  private async loadAudioDevices() {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const audioInputs = devices
        .filter(device => device.kind === 'audioinput')
        .map((device, index) => ({
          deviceId: device.deviceId,
          label: device.label || `Μικρόφωνο ${index + 1}`,
          kind: device.kind,
          isDefault: device.deviceId === 'default'
        }));

      this.availableAudioDevices.set(audioInputs);
      
      // Set first device as selected if none selected
      if (audioInputs.length > 0 && this.selectedAudioDevice() === 'default') {
        this.selectedAudioDevice.set(audioInputs[0].deviceId);
      }
      
    } catch (error) {
      console.error('Failed to enumerate audio devices:', error);
      this.notificationService.error('Αποτυχία φόρτωσης συσκευών ήχου');
    }
  }

  async requestMicrophonePermission() {
    await this.initializeAudioDevices();
  }

  onAudioDeviceChange(deviceId: string) {
    this.selectedAudioDevice.set(deviceId);
    
    // If currently recording, restart with new device
    if (this.isRecording()) {
      this.stopRecording().then(() => {
        setTimeout(() => this.startRecording(), 100);
      });
    }
  }

  // Audio Visualization Methods
  private initializeAudioVisualization(stream: MediaStream) {
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const analyser = audioContext.createAnalyser();
      const microphone = audioContext.createMediaStreamSource(stream);
      
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.8;
      microphone.connect(analyser);

      // Update recorder with audio context and analyser
      if (this.audioRecorder) {
        this.audioRecorder.audioContext = audioContext;
        this.audioRecorder.analyser = analyser;
      }

      // Start visualization immediately
      this.startVisualizationLoop(analyser);
      
    } catch (error) {
      console.error('Failed to initialize audio visualization:', error);
    }
  }

  private startVisualizationLoop(analyser: AnalyserNode) {
    const bufferLength = analyser.frequencyBinCount;
    const frequencyData = new Uint8Array(bufferLength);
    const timeDomainData = new Uint8Array(analyser.fftSize);

    const animate = () => {
      
      if (!this.isRecording()) {
        this.audioVisualization.update(prev => ({
          ...prev,
          isActive: false,
          volume: 0,
          averageVolume: 0
        }));
        // Clear bars when not recording
        this.activeBars.set([]);
        return;
      }

      // Get time domain data for real amplitude detection
      analyser.getByteTimeDomainData(timeDomainData);
      analyser.getByteFrequencyData(frequencyData);
      
      // Calculate RMS (Root Mean Square) for accurate volume detection
      let sum = 0;
      for (let i = 0; i < timeDomainData.length; i++) {
        const amplitude = (timeDomainData[i] - 128) / 128; // Convert to -1 to 1 range
        sum += amplitude * amplitude;
      }
      const rms = Math.sqrt(sum / timeDomainData.length);
      
      // Calculate frequency average
      const frequencySum = frequencyData.reduce((a, b) => a + b, 0);
      const frequencyAverage = frequencySum / bufferLength;
      
      // Set threshold for detecting actual sound (much more sensitive)
      const soundThreshold = 0.002; // Very low threshold for high sensitivity
      const hasSound = rms > soundThreshold || frequencyAverage > 10;
      
      // Update visualization data
      this.audioVisualization.update(prev => ({
        volume: rms,
        frequency: frequencyData.slice(0, 32),
        averageVolume: frequencyAverage / 255,
        isActive: hasSound
      }));

      // Always generate bars during recording for testing - we'll add sound detection later
      this.generateWaveformBars(frequencyData.slice(0, 12));

      this.visualizationAnimationId = requestAnimationFrame(animate);
    };

    // Start the animation loop immediately
    animate();
  }

  private generateWaveformBars(frequencyData: Uint8Array) {
    const bars: WaveformBar[] = Array.from(frequencyData, (value, index) => {
      // Normalize and apply logarithmic scaling for better visual representation
      const normalizedValue = Math.max(value / 255, 0.05); // Minimum for subtle presence
      const scaledHeight = Math.pow(normalizedValue, 0.6); // Smooth scaling
      
      return {
        id: index,
        height: Math.max(0.1, scaledHeight * 0.8), // 10% to 80% height
        opacity: Math.max(0.2, normalizedValue * 0.6) // 20% to 60% opacity for transparency
      };
    });

    this.activeBars.set(bars);
  }

  // Recording Section Methods
  async toggleRecording() {
    if (this.isRecording()) {
      await this.stopRecording();
    } else {
      await this.startRecording();
    }
  }

  submitRecording() {
    const file = this.recordedAudio();
    if (!file) return;

    // Convert the blob URL back to a file for upload
    fetch(file)
      .then(res => res.blob())
      .then(blob => {
        const audioFile = new File([blob], `recording-${Date.now()}.webm`, {
          type: 'audio/webm'
        });

        // Ensure model is never null/undefined
        const currentModel = this.selectedModel() || 'whisper';
        console.log('Recording: Selected model =', currentModel);
        
        const formData = new FormData();
        formData.append('file', audioFile);
        formData.append('title', `Ηχογράφηση ${new Date().toLocaleString('el-GR')}`);
        formData.append('language', 'el');
        formData.append('ai_model', currentModel);
        formData.append('enable_comparison', currentModel === 'both' ? 'true' : 'false');

        this.transcriptionService.uploadAndTranscribe(formData).subscribe({
          next: (result) => {
            if (result) {
              this.notificationService.success('Η ηχογράφηση ολοκληρώθηκε και η μεταγραφή ξεκίνησε!');
              // Reset recording state and refresh transcriptions list instead of navigating
              this.resetRecording();
              // Reset to first page to show the new transcription at the top
              this.currentPage.set(1);
              this.loadRecentTranscriptions();
              // Start auto-refresh to monitor progress
              this.joinTranscriptionRooms();
            }
          },
          error: (error: any) => {
            console.error('Recording upload error:', error);
            this.notificationService.error('Σφάλμα κατά τη μεταφόρτωση της ηχογράφησης');
          }
        });
      })
      .catch(error => {
        console.error('Error converting recording:', error);
        this.notificationService.error('Σφάλμα κατά την επεξεργασία της ηχογράφησης');
      });
  }

  deleteRecording() {
    this.resetRecording();
    this.notificationService.info('Η ηχογράφηση διαγράφηκε');
  }

  private async startRecording() {
    if (!this.authService.isEmailVerified()) {
      this.notificationService.error('Παρακαλούμε επιβεβαιώστε το email σας πρώτα');
      return;
    }

    try {
      // Use selected audio device
      const constraints: MediaStreamConstraints = {
        audio: {
          deviceId: this.selectedAudioDevice() !== 'default' 
            ? { exact: this.selectedAudioDevice() }
            : undefined,
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        }
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);

      // Check for best supported audio format for better browser compatibility
      let mimeType = 'audio/webm;codecs=opus';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        // Fallback for Safari and other browsers
        const alternatives = [
          'audio/webm',
          'audio/mp4',
          'audio/mp4;codecs=mp4a.40.2',
          'audio/mpeg',
          'audio/wav'
        ];
        
        for (const type of alternatives) {
          if (MediaRecorder.isTypeSupported(type)) {
            mimeType = type;
            break;
          }
        }
      }

      console.log('Using audio format:', mimeType);
      const mediaRecorder = new MediaRecorder(stream, { mimeType });

      const audioChunks: Blob[] = [];

      this.audioRecorder = {
        start: async () => {
          mediaRecorder.start(100); // Record in 100ms chunks for visualization
        },
        stop: async () => {
          return new Promise((resolve) => {
            mediaRecorder.onstop = () => {
              const audioBlob = new Blob(audioChunks, { type: mimeType });
              resolve(audioBlob);
            };
            mediaRecorder.stop();
            stream.getTracks().forEach(track => track.stop());
          });
        },
        isRecording: true,
        stream
      };

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
        }
      };

      await this.audioRecorder.start();
      this.isRecording.set(true);
      this.startRecordingTimer();
      
      // Initialize audio visualization AFTER recording starts
      this.initializeAudioVisualization(stream);

    } catch (error) {
      console.error('Recording error:', error);
      this.notificationService.error('Δεν ήταν δυνατή η πρόσβαση στο μικρόφωνο');
    }
  }

  private async stopRecording() {
    if (!this.audioRecorder || !this.isRecording()) return;

    try {
      const audioBlob = await this.audioRecorder.stop();
      this.isRecording.set(false);
      
      if (this.recordingTimer) {
        clearInterval(this.recordingTimer);
      }

      // Clean up previous audio URL to prevent memory leaks
      const previousAudioUrl = this.recordedAudio();
      if (previousAudioUrl) {
        URL.revokeObjectURL(previousAudioUrl);
      }

      // Validate that we have a valid audio blob
      if (audioBlob.size === 0) {
        throw new Error('Η ηχογράφηση είναι κενή');
      }

      // Convert blob to URL for playback
      const audioUrl = URL.createObjectURL(audioBlob);
      this.recordedAudio.set(audioUrl);

      // Preload the audio immediately after recording
      this.preloadAudio(audioUrl);

      this.notificationService.success('Η ηχογράφηση ολοκληρώθηκε! Μπορείτε να την ακούσετε και να την στείλετε για μεταγραφή.');

    } catch (error: any) {
      console.error('Stop recording error:', error);
      this.notificationService.error(`Σφάλμα κατά τη διακοπή της ηχογράφησης: ${error.message}`);
    }
  }

  private startRecordingTimer() {
    this.recordingTime.set(0);
    this.recordingTimer = setInterval(() => {
      const time = this.recordingTime() + 1;
      this.recordingTime.set(time);
      
      // Stop recording at max time
      if (time >= this.maxRecordingTime) {
        this.stopRecording();
        this.notificationService.warning('Η μέγιστη διάρκεια ηχογράφησης είναι 6 ώρες');
      }
    }, 1000);
  }

  formatRecordingTime(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  // Custom Audio Player Methods
  onAudioLoadedMetadata(event: Event): void {
    const audio = event.target as HTMLAudioElement;
    
    // Immediately try to set duration if available
    if (audio.duration && isFinite(audio.duration) && audio.duration > 0) {
      this.audioDuration.set(audio.duration);
      this.currentAudioTime.set(audio.currentTime || 0);
    }
    
    // Always ensure audio is ready for immediate playback
    if (audio.readyState >= 2) { // HAVE_CURRENT_DATA or higher
      // Audio has enough data to start playing
      this.currentAudioTime.set(audio.currentTime || 0);
    }
  }

  onAudioTimeUpdate(event: Event): void {
    const audio = event.target as HTMLAudioElement;
    const currentTime = audio.currentTime || 0;
    this.currentAudioTime.set(currentTime);
    
    // Ensure we have valid duration
    if (audio.duration && isFinite(audio.duration) && audio.duration > 0 && this.audioDuration() <= 0) {
      this.audioDuration.set(audio.duration);
    }
  }

  onAudioLoadStart(event: Event): void {
    // Reset state when new audio starts loading
    this.audioDuration.set(0);
    this.currentAudioTime.set(0);
    this.isAudioPlaying.set(false);
    this.audioReadyToPlay.set(false);
  }

  onAudioCanPlay(event: Event): void {
    const audio = event.target as HTMLAudioElement;
    this.audioReadyToPlay.set(true);
    
    // Set duration if available
    if (audio.duration && isFinite(audio.duration) && audio.duration > 0) {
      this.audioDuration.set(audio.duration);
    }
  }

  onAudioCanPlayThrough(event: Event): void {
    const audio = event.target as HTMLAudioElement;
    this.audioReadyToPlay.set(true);
    
    // Ensure duration is set
    if (audio.duration && isFinite(audio.duration) && audio.duration > 0) {
      this.audioDuration.set(audio.duration);
    }
  }

  onAudioSeeking(event: Event): void {
    // Called when seeking starts
  }

  onAudioSeeked(event: Event): void {
    // Called when seeking completes
    const audio = event.target as HTMLAudioElement;
    this.currentAudioTime.set(audio.currentTime);
  }

  onAudioProgress(event: Event): void {
    // Called when browser is downloading the audio
    const audio = event.target as HTMLAudioElement;
    if (audio.buffered.length > 0) {
      const bufferedEnd = audio.buffered.end(audio.buffered.length - 1);
      const duration = audio.duration;
      if (duration > 0) {
        const bufferedPercent = (bufferedEnd / duration) * 100;
        console.log(`Audio buffered: ${bufferedPercent.toFixed(1)}%`);
      }
    }
  }

  onAudioPlay(event: Event): void {
    // Audio is actually playing now
    this.audioActuallyPlaying.set(true);
    this.isAudioPlaying.set(true);
    
    // Stop simulated progress and start real tracking
    this.stopSimulatedProgress();
    this.startSmoothProgressTracking(event.target as HTMLAudioElement);
  }

  onAudioPause(event: Event): void {
    this.isAudioPlaying.set(false);
    this.audioActuallyPlaying.set(false);
    this.stopSmoothProgressTracking();
    this.stopSimulatedProgress();
  }

  onAudioEnded(event: Event): void {
    this.isAudioPlaying.set(false);
    this.audioActuallyPlaying.set(false);
    this.stopSmoothProgressTracking();
    this.stopSimulatedProgress();
    const audio = event.target as HTMLAudioElement;
    audio.currentTime = 0;
    this.currentAudioTime.set(0);
  }

  onAudioError(event: Event): void {
    console.error('Audio error:', event);
    this.isAudioPlaying.set(false);
    this.notificationService.error('Σφάλμα κατά την αναπαραγωγή του ήχου');
  }

  toggleAudioPlayback(audio: HTMLAudioElement): void {
    if (this.isAudioPlaying()) {
      audio.pause();
      return;
    }

    // Immediately show visual feedback
    this.isAudioPlaying.set(true);
    this.audioActuallyPlaying.set(false);
    
    // Start simulated progress for instant UI feedback
    this.startSimulatedProgress(audio);
    
    // Aggressive play strategy
    const forcePlay = () => {
      // Try multiple times with increasing delays
      const attempts = [0, 10, 50, 100, 200];
      let attemptIndex = 0;
      
      const tryPlay = () => {
        if (attemptIndex >= attempts.length) {
          console.error('Failed to play after all attempts');
          this.isAudioPlaying.set(false);
          this.audioActuallyPlaying.set(false);
          this.stopSimulatedProgress();
          this.notificationService.error('Αποτυχία αναπαραγωγής ήχου');
          return;
        }
        
        const delay = attempts[attemptIndex];
        attemptIndex++;
        
        setTimeout(() => {
          if (!this.audioActuallyPlaying()) {
            audio.play().then(() => {
              console.log(`Play succeeded on attempt ${attemptIndex}`);
            }).catch(() => {
              tryPlay(); // Try next attempt
            });
          }
        }, delay);
      };
      
      tryPlay();
    };

    // Start aggressive play attempts
    forcePlay();
    
    // Also try standard approach in parallel
    if (audio.readyState >= 2) {
      audio.play().catch(() => {
        // Will be handled by forcePlay
      });
    } else {
      audio.load();
    }
  }

  seekAudio(event: MouseEvent, audio: HTMLAudioElement): void {
    const progressContainer = event.currentTarget as HTMLElement;
    const rect = progressContainer.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const percentage = clickX / rect.width;
    
    const duration = this.audioDuration();
    if (duration > 0) {
      const newTime = percentage * duration;
      audio.currentTime = newTime;
      this.currentAudioTime.set(newTime);
    }
  }

  toggleMute(audio: HTMLAudioElement): void {
    audio.muted = !audio.muted;
    this.isAudioMuted.set(audio.muted);
  }

  changeVolume(event: Event, audio: HTMLAudioElement): void {
    const input = event.target as HTMLInputElement;
    const volume = parseFloat(input.value) / 100; // Convert from 0-100 to 0-1
    audio.volume = volume;
    this.audioVolume.set(volume);
    
    // Unmute if volume is being changed while muted
    if (audio.muted && volume > 0) {
      audio.muted = false;
      this.isAudioMuted.set(false);
    }
  }

  private startSmoothProgressTracking(audio: HTMLAudioElement): void {
    // Clear any existing intervals
    this.stopSmoothProgressTracking();
    this.stopSimulatedProgress();
    
    // Sync with actual audio time (don't reset to 0)
    this.currentAudioTime.set(audio.currentTime || 0);
    
    // Set duration if available
    if (audio.duration && isFinite(audio.duration) && audio.duration > 0) {
      this.audioDuration.set(audio.duration);
    }
    
    // Start a high-frequency interval for smooth progress
    this.audioProgressInterval = setInterval(() => {
      if (audio && !audio.paused && !audio.ended) {
        this.currentAudioTime.set(audio.currentTime);
        
        // Update duration if it wasn't properly set before
        if (audio.duration && isFinite(audio.duration) && audio.duration > 0 && this.audioDuration() <= 0) {
          this.audioDuration.set(audio.duration);
        }
      } else if (audio && audio.paused) {
        // Update final position when paused
        this.currentAudioTime.set(audio.currentTime);
      }
    }, 16); // Update every 16ms (~60fps) for even smoother animation
  }

  private stopSmoothProgressTracking(): void {
    if (this.audioProgressInterval) {
      clearInterval(this.audioProgressInterval);
      this.audioProgressInterval = null;
    }
  }

  private startSimulatedProgress(audio: HTMLAudioElement): void {
    // Stop any existing intervals
    this.stopSimulatedProgress();
    this.stopSmoothProgressTracking();
    
    // Force reset to zero for visual feedback
    this.currentAudioTime.set(0);
    
    // Try to get duration from audio or use a reasonable default
    let estimatedDuration = 10; // Default 10 seconds if unknown
    if (audio.duration && isFinite(audio.duration) && audio.duration > 0) {
      this.audioDuration.set(audio.duration);
      estimatedDuration = audio.duration;
    } else if (this.recordingTime() > 0) {
      // Use recording time as estimate
      estimatedDuration = this.recordingTime();
      this.audioDuration.set(estimatedDuration);
    }
    
    // Log for debugging
    console.log('Starting simulated progress, duration:', estimatedDuration);
    
    // Start simulated progress immediately
    const startTime = Date.now();
    let lastUpdate = startTime;
    
    this.simulatedProgressInterval = setInterval(() => {
      // Only continue simulating if audio hasn't actually started playing
      if (!this.audioActuallyPlaying()) {
        const now = Date.now();
        const elapsed = (now - startTime) / 1000;
        
        // Update the current time with elapsed time
        this.currentAudioTime.set(elapsed);
        
        // Log progress every second
        if (now - lastUpdate > 1000) {
          console.log('Simulated progress:', elapsed.toFixed(2), 'seconds');
          lastUpdate = now;
        }
        
        // Don't simulate beyond the estimated duration
        if (elapsed >= estimatedDuration) {
          this.stopSimulatedProgress();
        }
      } else {
        // Audio is actually playing, stop simulation
        console.log('Audio started playing, stopping simulation');
        this.stopSimulatedProgress();
      }
    }, 16); // Update every 16ms for smooth animation
  }

  private stopSimulatedProgress(): void {
    if (this.simulatedProgressInterval) {
      clearInterval(this.simulatedProgressInterval);
      this.simulatedProgressInterval = null;
    }
  }

  formatTime(seconds: number): string {
    if (isNaN(seconds) || !isFinite(seconds)) return '0:00';
    
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  resetRecording() {
    // Clean up blob URL before clearing
    const audioUrl = this.recordedAudio();
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
    
    this.recordedAudio.set(null);
    this.recordingTime.set(0);
  }

  private preloadAudio(audioUrl: string): void {
    // Create a hidden audio element for preloading
    const preloadAudio = new Audio();
    preloadAudio.src = audioUrl;
    preloadAudio.preload = 'auto';
    
    // Force browser to start downloading the audio
    preloadAudio.load();
    
    // Optionally, attempt to decode audio data for faster playback
    preloadAudio.addEventListener('canplaythrough', () => {
      console.log('Audio preloaded and ready');
      this.audioReadyToPlay.set(true);
    }, { once: true });
  }

  // Auto-refresh methods
  private setupWebSocketListeners(): void {
    console.log('Setting up WebSocket listeners for transcription updates...');
    
    // Ensure WebSocket is connected
    if (!this.wsService.getConnectionStatus()) {
      this.wsService.autoConnect();
    }
    
    // Monitor WebSocket connection status
    this.wsService.isConnected$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((isConnected) => {
        console.log('WebSocket connection status changed:', isConnected);
        if (isConnected) {
          // When reconnected, rejoin rooms for active transcriptions
          this.joinTranscriptionRooms();
        }
      });

    // Listen for transcription progress updates
    this.wsService.progressUpdates$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((data) => {
        console.log('WebSocket: Progress update', data);
        
        // Update the specific transcription in our list
        const transcriptions = this.recentTranscriptions();
        const index = transcriptions.findIndex(t => t.id === data.transcription_id);
        
        if (index >= 0) {
          // Update progress percentage if available
          if (data.percentage !== undefined) {
            transcriptions[index] = {
              ...transcriptions[index],
              status: TranscriptionStatus.PROCESSING
            };
            this.recentTranscriptions.set([...transcriptions]);
          }
        }
      });

    // Listen for transcription completion
    this.wsService.completionEvents$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((data) => {
        console.log('WebSocket: Transcription completed', data);
        // Reset to first page to show the completed transcription at the top
        this.currentPage.set(1);
        // Reload to get the complete transcription with text
        this.loadRecentTranscriptions();
      });

    // Listen for transcription errors
    this.wsService.errorEvents$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((data) => {
        console.log('WebSocket: Transcription error', data);
        
        // Update the specific transcription status
        const transcriptions = this.recentTranscriptions();
        const index = transcriptions.findIndex(t => t.id === data.transcription_id);
        
        if (index >= 0) {
          transcriptions[index] = {
            ...transcriptions[index],
            status: TranscriptionStatus.FAILED,
            errorMessage: data.message
          };
          this.recentTranscriptions.set([...transcriptions]);
          
          // Show error notification to user
          this.notificationService.error(
            `Σφάλμα μεταγραφής: ${data.message}`,
            'Σφάλμα'
          );
        }
        
        // Reload transcriptions to ensure sync with backend
        setTimeout(() => {
          this.loadRecentTranscriptions();
        }, 1000);
      });

    // Note: transcription_created events would need to be added to WebSocketService if needed
    // For now, we rely on the completion events to refresh the list
    // this.wsService.completionEvents$
    //   .pipe(takeUntilDestroyed(this.destroyRef))
    //   .subscribe((data) => {
    //     console.log('WebSocket: New transcription created', data);
    //     // Reload the list to include new transcription
    //     this.loadRecentTranscriptions();
    //   });
  }

  private joinTranscriptionRooms(): void {
    // Join room for each active transcription to get real-time updates
    const processingTranscriptions = this.recentTranscriptions().filter(
      t => t.status === TranscriptionStatus.PROCESSING || t.status === TranscriptionStatus.PENDING
    );

    processingTranscriptions.forEach(transcription => {
      this.wsService.joinTranscriptionRoom(transcription.id).catch((err: any) => {
        console.warn(`Failed to join room for transcription ${transcription.id}:`, err);
      });
    });
  }
  
  private checkTranscriptionStatusSync(transcriptions: Transcription[]): void {
    // Check if any transcriptions were processing/pending in our local state
    // but have a different status from the server
    const previousTranscriptions = this.recentTranscriptions();
    
    transcriptions.forEach(serverTranscription => {
      const localTranscription = previousTranscriptions.find(t => t.id === serverTranscription.id);
      
      if (localTranscription && localTranscription.status !== serverTranscription.status) {
        console.log(`Status mismatch detected for transcription ${serverTranscription.id}:`,
          `Local: ${localTranscription.status}, Server: ${serverTranscription.status}`);
        
        // If server says failed but we thought it was processing, show notification
        if (serverTranscription.status === TranscriptionStatus.FAILED &&
            (localTranscription.status === TranscriptionStatus.PROCESSING ||
             localTranscription.status === TranscriptionStatus.PENDING)) {
          // Only show notification if we haven't already shown it via websocket
          if (!serverTranscription.errorMessage?.includes('WebSocket')) {
            this.notificationService.error(
              `Η μεταγραφή "${serverTranscription.title}" απέτυχε: ${serverTranscription.errorMessage || 'Άγνωστο σφάλμα'}`,
              'Σφάλμα μεταγραφής'
            );
          }
        }
      }
    });
  }

  private getCurrentFilters(): any {
    // Parse sort value - handle multi-part field names like 'created_at_desc'
    const sortValue = this.sortBy();
    const parts = sortValue.split('_');
    
    // Last part is order (asc/desc), everything else is the field name
    const order = parts[parts.length - 1];
    const field = parts.slice(0, -1).join('_');
    
    // Build filters object
    const filters: any = {
      sort: field,
      order: order as 'asc' | 'desc'
    };
    
    // Add status filter if not 'all'
    if (this.statusFilter() !== 'all') {
      filters.status = this.statusFilter();
    }
    
    // Add date range filter if selected
    const dateRange = this.dateFilter();
    if (dateRange && dateRange.length === 2) {
      // Use DateService for consistent timezone handling
      const dateRangeForApi = this.dateService.formatDateRangeForApi(
        dateRange[0],
        dateRange[1]
      );
      
      if (dateRangeForApi.start_date) {
        filters.start_date = dateRangeForApi.start_date;
      }
      if (dateRangeForApi.end_date) {
        filters.end_date = dateRangeForApi.end_date;
      }
    }
    
    return filters;
  }

  // Recent Transcriptions Methods
  loadRecentTranscriptions(isUserAction = false) {
    // Clear any existing debounce timer
    if (this.filterDebounceTimer) {
      clearTimeout(this.filterDebounceTimer);
    }

    const performLoad = () => {
      // For user actions (filtering), use gentle loading that doesn't hide content
      if (isUserAction) {
        this.isFiltering.set(true);
      } else {
        // For initial load, use regular loading
        this.isLoading.set(true);
      }
      
      const filters = this.getCurrentFilters();
      const itemsPerPage = 5;
      
      this.transcriptionService.getTranscriptions(
        this.currentPage(),
        itemsPerPage,
        filters
      ).subscribe({
        next: (response) => {
          // Get transcriptions from service's signal (already updated by service)
          const transcriptions = this.transcriptionService.transcriptions();
          const data = response.data || response;
          const pagination = data.pagination || {};
          
          // Set transcriptions directly from service signal
          this.recentTranscriptions.set(transcriptions);
          
          // Use proper pagination data from backend
          this.hasMorePages.set(pagination.has_next || this.currentPage() * itemsPerPage < transcriptions.length);
          this.totalTranscriptions.set(pagination.total || transcriptions.length);
          
          // Clear both loading states
          this.isLoading.set(false);
          this.isFiltering.set(false);
          
          // Check if we need to start auto-refresh
          const hasProcessing = transcriptions.some((t: Transcription) => 
            t.status === TranscriptionStatus.PROCESSING || 
            t.status === TranscriptionStatus.PENDING
          );
          
          if (hasProcessing) {
            console.log('Found processing transcriptions, starting auto-refresh');
            this.joinTranscriptionRooms();
          }
          
          // Check for status sync issues
          this.checkTranscriptionStatusSync(transcriptions);
        },
        error: (error) => {
          console.error('Error loading transcriptions:', error);
          // Show empty state when API fails
          this.recentTranscriptions.set([]);
          this.hasMorePages.set(false);
          this.totalTranscriptions.set(0);
          this.isLoading.set(false);
          this.isFiltering.set(false);
        }
      });
    };

    // For user actions, add a small debounce to prevent too rapid requests
    if (isUserAction) {
      this.filterDebounceTimer = setTimeout(performLoad, 300);
    } else {
      performLoad();
    }
  }

  refreshTranscriptions() {
    this.currentPage.set(1);
    this.loadRecentTranscriptions();
  }

  nextPage() {
    if (this.hasMorePages()) {
      this.currentPage.set(this.currentPage() + 1);
      this.loadRecentTranscriptions();
    }
  }

  previousPage() {
    if (this.currentPage() > 1) {
      this.currentPage.set(this.currentPage() - 1);
      this.loadRecentTranscriptions();
    }
  }

  viewTranscription(id: string) {
    this.router.navigate(['/app/transcriptions', id]);
  }

  formatDuration(seconds: number): string {
    if (!seconds) return '-';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  formatDate(date: Date | string | undefined): string {
    return this.dateService.formatForDisplay(date, { format: 'medium' });
  }

  getStatusClass(status: TranscriptionStatus): string {
    switch (status) {
      case TranscriptionStatus.COMPLETED:
        return 'success';
      case TranscriptionStatus.FAILED:
        return 'error';
      case TranscriptionStatus.PROCESSING:
        return 'processing';
      case TranscriptionStatus.PENDING:
        return 'warning';
      default:
        return 'warning';
    }
  }

  getStatusText(status: TranscriptionStatus): string {
    switch (status) {
      case TranscriptionStatus.COMPLETED:
        return 'Μεταγράφηκε';
      case TranscriptionStatus.FAILED:
        return 'Σφάλμα';
      case TranscriptionStatus.PROCESSING:
        return 'Επεξεργασία';
      case TranscriptionStatus.PENDING:
        return 'Αναμονή';
      default:
        return 'Άγνωστο';
    }
  }

  // Show menu for download/share options only
  showTranscriptionMenu(event: Event, transcription: Transcription) {
    event.stopPropagation();
    this.selectedTranscription = transcription;
    this.menuItems = this.buildTranscriptionMenu(transcription);
  }

  // Build menu with download, share, and action options based on status
  private buildTranscriptionMenu(transcription: Transcription): any[] {
    const items = [];

    // Download and share section (only for completed transcriptions)
    if (transcription.status === TranscriptionStatus.COMPLETED) {
      items.push({
        label: 'Λήψη',
        icon: 'pi pi-download',
        items: [
          {
            label: 'TXT (Κείμενο)',
            icon: 'pi pi-file-o',
            command: () => this.downloadTranscription(transcription, 'txt')
          },
          {
            label: 'SRT (Υπότιτλοι)',
            icon: 'pi pi-video',
            command: () => this.downloadTranscription(transcription, 'srt')
          },
          {
            label: 'DOCX (Word)',
            icon: 'pi pi-file-word',
            command: () => this.downloadTranscription(transcription, 'docx')
          },
          {
            label: 'PDF (Έγγραφο)',
            icon: 'pi pi-file-pdf',
            command: () => this.downloadTranscription(transcription, 'pdf')
          }
        ]
      });

      // Share section
      items.push({
        label: 'Κοινοποίηση',
        icon: 'pi pi-share-alt',
        items: [
          {
            label: 'Αντιγραφή κειμένου',
            icon: 'pi pi-copy',
            command: () => this.copyTranscriptionText(transcription)
          },
          {
            label: 'Αντιγραφή συνδέσμου',
            icon: 'pi pi-link',
            command: () => this.copyTranscriptionLink(transcription)
          },
          {
            label: 'Κοινοποίηση',
            icon: 'pi pi-send',
            command: () => this.shareTranscription(transcription)
          }
        ]
      });
    }

    // Retry section (for failed transcriptions)
    if (transcription.status === TranscriptionStatus.FAILED) {
      items.push({
        label: 'Επανάληψη',
        icon: 'pi pi-refresh',
        command: () => this.retryTranscription(transcription)
      });

      // Show error details option
      items.push({
        label: 'Προβολή Σφάλματος',
        icon: 'pi pi-exclamation-triangle',
        command: () => this.showErrorDetails(transcription)
      });
    }

    // Processing details (for processing/pending transcriptions)
    if (transcription.status === TranscriptionStatus.PROCESSING || transcription.status === TranscriptionStatus.PENDING) {
      items.push({
        label: 'Λεπτομέρειες Επεξεργασίας',
        icon: 'pi pi-info-circle',
        command: () => this.showProcessingDetails(transcription)
      });

      // Cancel option for pending transcriptions
      if (transcription.status === TranscriptionStatus.PENDING) {
        items.push({
          label: 'Ακύρωση',
          icon: 'pi pi-times',
          command: () => this.cancelTranscription(transcription)
        });
      }
    }

    // Always show view option (if applicable)
    if (transcription.status === TranscriptionStatus.COMPLETED) {
      if (items.length > 0) {
        items.push({ separator: true });
      }
      items.push({
        label: 'Προβολή',
        icon: 'pi pi-eye',
        command: () => this.viewTranscription(transcription.id)
      });
    }

    return items;
  }

  // Confirm delete with user confirmation
  confirmDelete(transcriptionId: string, title: string): void {
    this.confirmationService.confirm({
      message: `Είστε βέβαιοι ότι θέλετε να διαγράψετε τη μεταγραφή "${title}";`,
      header: 'Επιβεβαίωση Διαγραφής',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'Διαγραφή',
      rejectLabel: 'Ακύρωση',
      acceptButtonStyleClass: 'p-button-danger',
      rejectButtonStyleClass: 'p-button-secondary p-button-outlined',
      accept: () => {
        console.log('Delete confirmed, calling service...');
        this.transcriptionService.deleteTranscription(transcriptionId).subscribe({
          next: () => {
            console.log('Delete successful');
            this.notificationService.success('Η μεταγραφή διαγράφηκε επιτυχώς');
            this.loadRecentTranscriptions();
          },
          error: (error: any) => {
            console.error('Delete error:', error);
            this.notificationService.error('Σφάλμα κατά τη διαγραφή');
          }
        });
      }
    });
  }

  // Download transcription
  downloadTranscription(transcription: Transcription, format: 'txt' | 'srt' | 'docx' | 'pdf'): void {
    this.transcriptionService.downloadTranscription(transcription.id, format).subscribe({
      next: (blob: Blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${transcription.title || 'transcription'}.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      },
      error: (error) => {
        console.error('Download error:', error);
        this.notificationService.error('Σφάλμα κατά τη λήψη');
      }
    });
  }

  // Open retry dialog
  retryTranscription(transcription: Transcription): void {
    this.retryTranscription_data.set(transcription);
    this.showRetryDialog.set(true);
  }

  // Confirm and execute retry
  confirmRetry(): void {
    const transcription = this.retryTranscription_data();
    if (!transcription) return;

    this.isRetrying.set(true);
    
    this.transcriptionService.retryTranscription(transcription.id).subscribe({
      next: (updatedTranscription) => {
        this.isRetrying.set(false);
        this.showRetryDialog.set(false);
        this.retryTranscription_data.set(null);
        
        this.notificationService.success(
          `🔄 Η επανάληψη της μεταγραφής "${transcription.title}" ξεκίνησε επιτυχώς!`,
          'Επανάληψη Ξεκίνησε',
          { life: 6000 }
        );
        // Reset to first page to show the retried transcription at the top
        this.currentPage.set(1);
        this.loadRecentTranscriptions();
        // Start auto-refresh to monitor progress
        this.joinTranscriptionRooms();
      },
      error: (error: any) => {
        this.isRetrying.set(false);
        console.error('Retry error:', error);
        const errorMessage = error?.error?.message || error?.message || 'Σφάλμα κατά την επανάληψη';
        this.notificationService.error(
          `❌ Αποτυχία επανάληψης: ${errorMessage}`,
          'Σφάλμα Επανάληψης',
          { life: 8000 }
        );
      }
    });
  }

  // Cancel retry dialog
  cancelRetry(): void {
    this.showRetryDialog.set(false);
    this.retryTranscription_data.set(null);
    this.isRetrying.set(false);
  }

  // Delete transcription
  deleteTranscription(transcription: Transcription): void {
    console.log('Delete called for:', transcription.id, transcription.title);
    const title = transcription.title || transcription.file_name || transcription.audio_file?.filename || 'Αυτή τη μεταγραφή';
    
    if (confirm(`Είστε βέβαιοι ότι θέλετε να διαγράψετε τη μεταγραφή "${title}"?`)) {
      console.log('Delete confirmed, calling service...');
      this.transcriptionService.deleteTranscription(transcription.id).subscribe({
        next: () => {
          console.log('Delete successful');
          this.notificationService.success('Η μεταγραφή διαγράφηκε επιτυχώς');
          this.loadRecentTranscriptions();
        },
        error: (error) => {
          console.error('Delete error:', error);
          this.notificationService.error('Σφάλμα κατά τη διαγραφή');
        }
      });
    }
  }

  // Copy transcription text to clipboard
  copyTranscriptionText(transcription: Transcription): void {
    if (transcription.text) {
      navigator.clipboard.writeText(transcription.text).then(() => {
        this.notificationService.success('Το κείμενο αντιγράφηκε στο πρόχειρο!');
      }).catch(() => {
        this.notificationService.error('Αποτυχία αντιγραφής στο πρόχειρο');
      });
    } else {
      this.notificationService.warning('Δεν υπάρχει κείμενο για αντιγραφή');
    }
  }

  // Copy transcription link to clipboard
  copyTranscriptionLink(transcription: Transcription): void {
    const url = `${window.location.origin}/app/transcriptions/${transcription.id}`;
    navigator.clipboard.writeText(url).then(() => {
      this.notificationService.success('Ο σύνδεσμος αντιγράφηκε στο πρόχειρο!');
    }).catch(() => {
      this.notificationService.error('Αποτυχία αντιγραφής συνδέσμου');
    });
  }

  // Share transcription using Web Share API or fallback
  shareTranscription(transcription: Transcription): void {
    const shareData = {
      title: transcription.title || 'Μεταγραφή',
      text: `Δείτε αυτή τη μεταγραφή: ${transcription.title}`,
      url: `${window.location.origin}/app/transcriptions/${transcription.id}`
    };

    if (navigator.share) {
      navigator.share(shareData).catch(() => {
        this.copyTranscriptionLink(transcription);
      });
    } else {
      this.copyTranscriptionLink(transcription);
    }
  }

  // Show processing details
  showProcessingDetails(transcription: Transcription): void {
    let message = `Μεταγραφή σε επεξεργασία:\n\n`;
    message += `📋 Τίτλος: ${transcription.title}\n`;
    message += `⏱️ Ξεκίνησε: ${transcription.startedAt ? new Date(transcription.startedAt).toLocaleString('el-GR') : 'Άγνωστο'}\n`;
    message += `🎵 Διάρκεια: ${transcription.duration_seconds ? this.formatDuration(transcription.duration_seconds) : 'Άγνωστη'}\n`;
    message += `🤖 Μοντέλο: ${this.getModelDisplayName(transcription.model_used)}\n`;
    
    this.notificationService.info(message);
  }

  // Show error details for failed transcriptions
  showErrorDetails(transcription: Transcription): void {
    const errorMessage = transcription.errorMessage || 'Δεν υπάρχουν λεπτομέρειες σφάλματος';
    
    this.confirmationService.confirm({
      message: `Σφάλμα μεταγραφής:\n\n${errorMessage}\n\nΘέλετε να επαναλάβετε τη μεταγραφή;`,
      header: 'Λεπτομέρειες Σφάλματος',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'Επανάληψη',
      rejectLabel: 'Κλείσιμο',
      acceptButtonStyleClass: 'p-button-warning',
      rejectButtonStyleClass: 'p-button-secondary p-button-outlined',
      accept: () => {
        this.retryTranscription(transcription);
      }
    });
  }

  // Cancel pending transcription
  cancelTranscription(transcription: Transcription): void {
    this.confirmationService.confirm({
      message: `Είστε βέβαιοι ότι θέλετε να ακυρώσετε τη μεταγραφή "${transcription.title}";`,
      header: 'Ακύρωση Μεταγραφής',
      icon: 'pi pi-question-circle',
      acceptLabel: 'Ακύρωση',
      rejectLabel: 'Επιστροφή',
      acceptButtonStyleClass: 'p-button-warning',
      rejectButtonStyleClass: 'p-button-secondary p-button-outlined',
      accept: () => {
        // For now, we'll use delete since there might not be a specific cancel endpoint
        this.transcriptionService.deleteTranscription(transcription.id).subscribe({
          next: () => {
            this.notificationService.success('Η μεταγραφή ακυρώθηκε επιτυχώς');
            this.loadRecentTranscriptions();
          },
          error: (error: any) => {
            console.error('Cancel error:', error);
            this.notificationService.error('Σφάλμα κατά την ακύρωση');
          }
        });
      }
    });
  }

  // Filtering and Sorting Methods
  onSortChange(sortValue: string): void {
    this.sortBy.set(sortValue);
    this.loadRecentTranscriptions(true); // true = user action
  }

  onStatusFilterChange(status: string): void {
    this.statusFilter.set(status);
    this.currentPage.set(1); // Reset to first page
    this.loadRecentTranscriptions(true); // true = user action
  }

  onDateFilterChange(dates: Date[] | null): void {
    this.dateFilter.set(dates);
    this.currentPage.set(1); // Reset to first page
    this.loadRecentTranscriptions(true); // true = user action
  }

  clearFilters(): void {
    this.statusFilter.set('all');
    this.dateFilter.set(null);
    this.sortBy.set('created_at_desc');
    this.currentPage.set(1);
    this.loadRecentTranscriptions(true); // true = user action
  }
  
  toggleFilters(): void {
    this.showFilters.update(show => !show);
  }

  // Onboarding Methods
  startOnboarding(): void {
    this.showOnboarding.set(true);
  }

  skipOnboarding(): void {
    this.showOnboarding.set(false);
  }

  completeOnboarding(): void {
    this.showOnboarding.set(false);
    // Optionally save to localStorage that user has seen onboarding
    localStorage.setItem('greekstt-research_onboarding_completed', 'true');
  }

  /**
   * Map database model names to Greek display names
   */
  getModelDisplayName(modelUsed: string | undefined): string {
    if (!modelUsed) return 'Άγνωστο';
    
    switch (modelUsed) {
      case 'whisper':
      case 'faster-whisper':
        return 'Whisper-Large-3';
      case 'wav2vec2':
        return 'wav2vec2-Greek';
      case 'both':
        return 'Σύγκριση Μοντέλων';
      default:
        return modelUsed; // Return as-is if unknown
    }
  }
}