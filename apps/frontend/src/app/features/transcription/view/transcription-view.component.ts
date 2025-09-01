import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, ElementRef, inject, OnDestroy, OnInit, signal, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { switchMap } from 'rxjs/operators';

import { ConfirmationService } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { CheckboxModule } from 'primeng/checkbox';
import { ChipModule } from 'primeng/chip';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { DialogModule } from 'primeng/dialog';
import { DividerModule } from 'primeng/divider';
import { MenuModule } from 'primeng/menu';
import { MessageModule } from 'primeng/message';
import { ProgressBarModule } from 'primeng/progressbar';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { RippleModule } from 'primeng/ripple';
import { SelectButtonModule } from 'primeng/selectbutton';
import { SkeletonModule } from 'primeng/skeleton';
import { SliderModule } from 'primeng/slider';
import { SplitButtonModule } from 'primeng/splitbutton';
import { TabViewModule } from 'primeng/tabview';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';

import { ComparisonChartData, ComparisonChartsComponent } from '../../../shared/components/comparison-charts/comparison-charts.component';
import { StatusBadgeComponent } from '../../../shared/components/status-badge/status-badge.component';
import { DurationPipe } from '../../../shared/pipes/duration.pipe';
import { FileSizePipe } from '../../../shared/pipes/file-size.pipe';
import { GreekDatePipe } from '../../../shared/pipes/greek-date.pipe';

import { FileUploadModule } from 'primeng/fileupload';
import { SelectModule } from 'primeng/select';
import { TextareaModule } from 'primeng/textarea';
import { Transcription, TranscriptionSegment, TranscriptionStatus } from '../../../core/models/transcription.model';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../core/services/notification.service';
import { TranscriptionService } from '../../../core/services/transcription.service';
import { ComparisonWERResult, WERResult } from '../../../core/models/wer-result.model';

@Component({
  selector: 'app-transcription-view',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ButtonModule,
    CardModule,
    TagModule,
    ChipModule,
    TooltipModule,
    MenuModule,
    SelectButtonModule,
    TabViewModule,
    SplitButtonModule,
    MessageModule,
    ProgressSpinnerModule,
    DividerModule,
    ProgressBarModule,
    DialogModule,
    CheckboxModule,
    RippleModule,
    SkeletonModule,
    ConfirmDialogModule,
    SliderModule,
    StatusBadgeComponent,
    DurationPipe,
    GreekDatePipe,
    FileSizePipe,
    SelectModule,
    FileUploadModule,
    TextareaModule,
    ComparisonChartsComponent
  ],
  providers: [ConfirmationService],
  templateUrl: './transcription-view.component.html',
  styleUrls: ['./transcription-view.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class TranscriptionViewComponent implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly transcriptionService = inject(TranscriptionService);
  private readonly notificationService = inject(NotificationService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly apiService = inject(ApiService);

  // Signals from service
  readonly currentTranscription = this.transcriptionService.currentTranscription;
  readonly isLoading = this.transcriptionService.isLoading;

  // Local state
  private readonly _transcriptionId = signal<string | null>(null);
  private readonly _error = signal<string | null>(null);
  private readonly _selectedSegment = signal<TranscriptionSegment | null>(null);
  protected readonly _showTimestamps = signal<boolean>(true);
  protected readonly _fontSize = signal<'small' | 'medium' | 'large'>('medium');
  
  // Dual Model Support
  private readonly _isComparisonMode = signal<boolean>(false);
  private readonly _whisperResult = signal<any>(null);
  private readonly _wav2vecResult = signal<any>(null);
  private readonly _comparisonMetrics = signal<any>(null);
  private readonly _activeModelTab = signal<'whisper' | 'wav2vec2' | 'comparison'>('whisper');
  private readonly _transcription = signal<Transcription | null>(null);
  private readonly _viewMode = signal<'text' | 'segments'>('text');
  private readonly _audioUrl = signal<string | null>(null);
  protected readonly _selectedPlaybackSpeed = signal<number>(1);
  private readonly _segments = signal<TranscriptionSegment[]>([]);
  protected readonly _currentPlaybackTime = signal<number>(0);
  private readonly _isPlaying = signal<boolean>(false);
  private readonly _currentActiveSegment = signal<number>(-1);
  protected readonly _audioVolume = signal<number>(1.0);
  private readonly _isAudioMuted = signal<boolean>(false);
  private readonly _actualAudioDuration = signal<number>(0);
  private audioTimeUpdateInterval: any = null;
  
  // WER/CER Calculator state
  protected readonly _groundTruthText = signal<string>('');
  protected readonly _werResult = signal<WERResult | null>(null);
  protected readonly _comparisonWerResult = signal<ComparisonWERResult | null>(null);
  protected readonly _isCalculatingWER = signal<boolean>(false);
  protected readonly _showWERCalculator = signal<boolean>(false);
  
  // Comparison Charts state
  protected readonly _showCharts = signal<boolean>(false);
  protected readonly _chartData = signal<ComparisonChartData | null>(null);
  
  // Component references
  @ViewChild('audioPlayer') audioPlayerRef?: ElementRef<HTMLAudioElement>;

  // Public readonly signals
  readonly transcriptionId = this._transcriptionId.asReadonly();
  readonly error = this._error.asReadonly();
  readonly selectedSegment = this._selectedSegment.asReadonly();
  readonly showTimestamps = this._showTimestamps.asReadonly();
  readonly fontSize = this._fontSize.asReadonly();
  readonly transcription = this._transcription.asReadonly();
  readonly viewMode = this._viewMode.asReadonly();
  readonly audioUrl = this._audioUrl.asReadonly();
  readonly selectedPlaybackSpeed = this._selectedPlaybackSpeed.asReadonly();
  readonly segments = this._segments.asReadonly();
  readonly currentPlaybackTime = this._currentPlaybackTime.asReadonly();
  readonly isPlaying = this._isPlaying.asReadonly();
  readonly currentActiveSegment = this._currentActiveSegment.asReadonly();
  readonly audioVolume = this._audioVolume.asReadonly();
  readonly isAudioMuted = this._isAudioMuted.asReadonly();
  readonly actualAudioDuration = this._actualAudioDuration.asReadonly();
  
  // Computed property for effective audio duration (uses actual duration if available, falls back to DB duration)
  readonly effectiveAudioDuration = computed(() => {
    const actualDuration = this.actualAudioDuration();
    const dbDuration = this.transcription()?.duration_seconds || 0;
    
    // Use actual duration if available and valid, otherwise fall back to DB duration
    return (actualDuration > 0) ? actualDuration : dbDuration;
  });

  // WER/CER Calculator readonly signals
  readonly groundTruthText = this._groundTruthText.asReadonly();
  readonly werResult = this._werResult.asReadonly();
  readonly comparisonWerResult = this._comparisonWerResult.asReadonly();
  readonly isCalculatingWER = this._isCalculatingWER.asReadonly();
  readonly showWERCalculator = this._showWERCalculator.asReadonly();
  
  // Comparison Charts readonly signals
  readonly showCharts = this._showCharts.asReadonly();
  readonly chartData = this._chartData.asReadonly();

  // Computed signals
  readonly hasTranscription = computed(() => !!this.transcription());
  readonly isCompleted = computed(() => 
    this.transcription()?.status === TranscriptionStatus.COMPLETED
  );
  readonly isProcessing = computed(() => 
    this.transcription()?.status === TranscriptionStatus.PROCESSING ||
    this.transcription()?.status === TranscriptionStatus.PENDING
  );
  readonly isFailed = computed(() => 
    this.transcription()?.status === TranscriptionStatus.FAILED
  );
  
  // Dual Model Computed Signals
  readonly isComparisonMode = this._isComparisonMode.asReadonly();
  readonly whisperResult = this._whisperResult.asReadonly();
  readonly wav2vecResult = this._wav2vecResult.asReadonly();
  readonly comparisonMetrics = this._comparisonMetrics.asReadonly();
  readonly activeModelTab = this._activeModelTab.asReadonly();
  
  readonly hasComparisonData = computed(() => 
    !!this.whisperResult() && !!this.wav2vecResult()
  );
  
  // WER/CER Calculator computed signals
  readonly hasWERResult = computed(() => !!this.werResult());
  readonly hasComparisonWER = computed(() => !!this.comparisonWerResult());
  readonly canCalculateWER = computed(() => 
    this.isCompleted() && this.transcription()?.text && this.groundTruthText().trim().length > 0
  );
  readonly canCalculateComparisonWER = computed(() =>
    this.isComparisonMode() && this.hasComparisonData() && this.groundTruthText().trim().length > 0
  );
  
  readonly currentModelResult = computed(() => {
    const activeTab = this.activeModelTab();
    if (activeTab === 'whisper') return this.whisperResult();
    if (activeTab === 'wav2vec2') return this.wav2vecResult();
    return null;
  });

  readonly hasSegments = computed(() => {
    const segments = this.segments();
    return segments && segments.length > 0;
  });

  readonly transcriptionText = computed(() => {
    const segments = this.segments();
    if (!segments || segments.length === 0) return this.transcription()?.text || '';
    return segments.map(segment => segment.text).join(' ');
  });

  readonly transcriptionQuality = computed(() => {
    const transcription = this.transcription();
    if (!transcription) return 0;
    
    // Try multiple paths for accuracy data
    // All accuracy calculations are done in backend
    const accuracy = transcription.academic_accuracy_score ||          // Backend calculated academic accuracy
                    transcription.metadata?.['accuracy'] ||           // Backend metadata
                    transcription.processingMetadata?.['accuracy'] ||  // Backend processing metadata
                    transcription.confidence_score ||                 // Backend confidence (already as percentage)
                    0;  // No fallback - show 0 if no real data
    
    return accuracy; // No frontend calculation needed
  });

  readonly wordCount = computed(() => {
    // Use backend calculated word count
    const transcription = this.transcription();
    return transcription?.word_count || 0; // Backend calculated
  });

  readonly characterCount = computed(() => {
    // Use backend calculated character count  
    const transcription = this.transcription();
    return transcription?.character_count || this.transcriptionText().length; // Fallback to length if not available
  });

  readonly getCalculatedAccuracy = computed(() => {
    // All calculations are done in backend - just return backend values
    const transcription = this.transcription();
    if (!transcription) return 0;
    
    // Use backend calculated academic accuracy score
    return transcription.academic_accuracy_score || 0; // Backend calculated
  });

  readonly activeSegmentIndex = computed(() => {
    const currentTime = this.currentPlaybackTime();
    const segments = this.segments();
    
    if (!segments || segments.length === 0) return -1;
    
    for (let i = 0; i < segments.length; i++) {
      const segment = segments[i];
      if (currentTime >= segment.start_time && currentTime <= segment.end_time) {
        return i;
      }
    }
    return -1;
  });

  // Chart title based on mode and WER calculation status
  readonly chartTitle = computed(() => {
    const transcription = this.transcription();
    if (!transcription) return 'Γραφήματα Σύγκρισης';
    
    const hasEvaluation = transcription.has_evaluation;
    const isComparison = this.isComparisonMode() && this.hasComparisonData();
    const hasBothWER = transcription.whisper_wer !== null && transcription.wav2vec_wer !== null;
    
    // If comparison mode with both models evaluated
    if (isComparison && hasEvaluation && hasBothWER) {
      return 'Γραφήματα Σύγκρισης';
    }
    
    // If single model with WER calculated (Performance Charts)
    if (!isComparison && hasEvaluation && 
        (transcription.whisper_wer !== null || transcription.wav2vec_wer !== null)) {
      return 'Γραφήματα Απόδοσης';
    }
    
    // Default for charts without WER evaluation
    return 'Γραφήματα Σύγκρισης';
  });

  // Font size options
  readonly fontSizeOptions = [
    { label: 'Μικρό', value: 'small' as const },
    { label: 'Μεσαίο', value: 'medium' as const },
    { label: 'Μεγάλο', value: 'large' as const }
  ];

  // Export format options
  readonly exportFormats = [
    { label: 'TXT', value: 'txt', icon: 'pi pi-file-o', description: 'Απλό κείμενο' },
    { label: 'SRT', value: 'srt', icon: 'pi pi-video', description: 'Υπότιτλοι' },
    { label: 'DOCX', value: 'docx', icon: 'pi pi-file-word', description: 'Word έγγραφο' },
    { label: 'PDF', value: 'pdf', icon: 'pi pi-file-pdf', description: 'PDF έγγραφο' }
  ];

  // Playback speed options
  readonly playbackSpeeds = [
    { label: '0.5x', value: 0.5 },
    { label: '0.75x', value: 0.75 },
    { label: '1x', value: 1 },
    { label: '1.25x', value: 1.25 },
    { label: '1.5x', value: 1.5 },
    { label: '2x', value: 2 }
  ];

  // Export menu items
  readonly exportMenuItems = [
    {
      label: 'Εξαγωγή TXT',
      icon: 'pi pi-file-o',
      command: () => this.downloadTranscription('txt')
    },
    {
      label: 'Εξαγωγή SRT',
      icon: 'pi pi-video',
      command: () => this.downloadTranscription('srt')
    },
    {
      label: 'Εξαγωγή DOCX',
      icon: 'pi pi-file-word',
      command: () => this.downloadTranscription('docx')
    },
    {
      label: 'Εξαγωγή PDF',
      icon: 'pi pi-file-pdf',
      command: () => this.downloadTranscription('pdf')
    }
  ];

  // Display settings menu items - computed για να είναι reactive με submenu structure
  readonly displayMenuItems = computed(() => {
    const items: any[] = [];
    
    // View mode options μόνο αν έχουμε segments
    if (this.hasSegments()) {
      items.push({
        label: 'Εμφάνιση',
        icon: 'pi pi-eye',
        items: [
          {
            label: 'Κείμενο',
            icon: this.viewMode() === 'text' ? 'pi pi-check' : undefined,
            styleClass: this.viewMode() === 'text' ? 'menu-item-selected' : 'menu-item-view',
            command: () => this._viewMode.set('text')
          },
          {
            label: 'Τμήματα',
            icon: this.viewMode() === 'segments' ? 'pi pi-check' : undefined,
            styleClass: this.viewMode() === 'segments' ? 'menu-item-selected' : 'menu-item-view',
            command: () => this._viewMode.set('segments')
          }
        ]
      });
    }
    
    // Timestamps option μόνο για segments view
    if (this.viewMode() === 'segments') {
      // Add separator before options section
      if (this.hasSegments()) {
        items.push({ separator: true });
      }
      
      items.push({
        label: 'Επιλογές',
        icon: 'pi pi-cog',
        items: [
          {
            label: 'Χρονικές σημάνσεις',
            icon: this.showTimestamps() ? 'pi pi-check' : undefined,
            styleClass: this.showTimestamps() ? 'menu-item-selected' : 'menu-item-option',
            command: () => this._showTimestamps.set(!this.showTimestamps())
          }
        ]
      });
    }
    
    // Add separator before font size section
    if (items.length > 0) {
      items.push({ separator: true });
    }
    
    // Font size options για όλα τα views
    items.push({
      label: 'Μέγεθος κειμένου',
      icon: 'pi pi-font',
      items: [
        {
          label: 'Μικρό',
          icon: this.fontSize() === 'small' ? 'pi pi-check' : undefined,
          styleClass: this.fontSize() === 'small' ? 'menu-item-selected' : 'menu-item-size',
          command: () => this._fontSize.set('small')
        },
        {
          label: 'Μεσαίο', 
          icon: this.fontSize() === 'medium' ? 'pi pi-check' : undefined,
          styleClass: this.fontSize() === 'medium' ? 'menu-item-selected' : 'menu-item-size',
          command: () => this._fontSize.set('medium')
        },
        {
          label: 'Μεγάλο',
          icon: this.fontSize() === 'large' ? 'pi pi-check' : undefined,
          styleClass: this.fontSize() === 'large' ? 'menu-item-selected' : 'menu-item-size',
          command: () => this._fontSize.set('large')
        }
      ]
    });
    
    return items;
  });

  ngOnInit(): void {
    // Scroll to top when entering the transcription view page
    window.scrollTo(0, 0);
    
    this.route.params.pipe(
      switchMap(params => {
        const id = params['id'];
        this._transcriptionId.set(id);
        this._error.set(null);
        return this.transcriptionService.getTranscription(id);
      })
    ).subscribe({
      next: (response: any) => {
        const transcription = response.transcription || response;
        this._transcription.set(transcription);
        
        this.checkForComparisonData(transcription);
        this.loadSegments();
        
        // Load existing WER/CER evaluation if it exists
        this.loadExistingEvaluation(transcription);
        
        if (transcription.audio_file?.id) {
          this.generateAuthenticatedAudioUrl(transcription.audio_file.id);
        }
        
        // Initialize audio player with retry mechanism for video files
        setTimeout(() => {
          this.initializeEnhancedAudioPlayerWithRetry();
        }, 100);
      },
      error: (error) => {
        this._error.set('Error loading transcription');
        console.error('Error loading transcription:', error);
      }
    });
  }

  ngOnDestroy(): void {
    if (this.audioTimeUpdateInterval) {
      clearInterval(this.audioTimeUpdateInterval);
    }
    
    // Clean up object URL to prevent memory leaks
    if (this.previousObjectUrl) {
      URL.revokeObjectURL(this.previousObjectUrl);
      this.previousObjectUrl = null;
    }
  }

  goBack(): void {
    this.router.navigate(['/app/transcriptions']);
  }

  downloadTranscription(format: 'txt' | 'srt' | 'docx' | 'pdf' = 'txt'): void {
    const id = this.transcriptionId();
    if (!id) return;

    this.transcriptionService.downloadTranscription(id, format).subscribe({
      next: (blob) => {
        const transcription = this.currentTranscription();
        const fileName = `${transcription?.title || 'transcription'}.${format}`;
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      },
      error: (error) => {
        console.error('Download error:', error);
      }
    });
  }

  confirmDeleteTranscription(): void {
    const id = this.transcriptionId();
    if (!id) return;
    
    this.confirmationService.confirm({
      message: 'Είστε σίγουροι ότι θέλετε να διαγράψετε αυτή τη μεταγραφή; Αυτή η ενέργεια δεν μπορεί να αναιρεθεί.',
      header: 'Επιβεβαίωση Διαγραφής',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'Ναι, διαγραφή',
      rejectLabel: 'Ακύρωση',
      accept: () => {
        this.transcriptionService.deleteTranscription(id).subscribe({
          next: () => {
            this.notificationService.success('Η μεταγραφή διαγράφηκε επιτυχώς');
            this.router.navigate(['/app/transcriptions']);
          },
          error: (error) => {
            console.error('Failed to delete transcription:', error);
            this.notificationService.error('Αποτυχία διαγραφής μεταγραφής');
          }
        });
      }
    });
  }

  selectSegment(segment: TranscriptionSegment): void {
    this._selectedSegment.set(segment);
  }

  clearSegmentSelection(): void {
    this._selectedSegment.set(null);
  }

  toggleTimestamps(): void {
    this._showTimestamps.set(!this.showTimestamps());
  }

  changeFontSize(size: 'small' | 'medium' | 'large'): void {
    this._fontSize.set(size);
  }

  getStatusLabel(status: TranscriptionStatus | string): string {
    switch (status) {
      case TranscriptionStatus.PENDING:
      case 'pending':
        return 'Αναμονή';
      case TranscriptionStatus.PROCESSING:
      case 'processing':
        return 'Επεξεργασία';
      case TranscriptionStatus.COMPLETED:
      case 'completed':
        return 'Ολοκληρώθηκε';
      case TranscriptionStatus.FAILED:
      case 'failed':
        return 'Σφάλμα';
      default:
        return 'Άγνωστη';
    }
  }

  getStatusSeverity(status: TranscriptionStatus | string): 'success' | 'info' | 'warning' | 'danger' {
    switch (status) {
      case TranscriptionStatus.COMPLETED:
      case 'completed':
        return 'success';
      case TranscriptionStatus.PROCESSING:
      case 'processing':
        return 'info';
      case TranscriptionStatus.PENDING:
      case 'pending':
        return 'warning';
      case TranscriptionStatus.FAILED:
      case 'failed':
        return 'danger';
      default:
        return 'info';
    }
  }

  formatTimestamp(seconds: number | undefined): string {
    if (seconds === undefined || seconds === null) {
      return '00:00';
    }
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
      return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
  }

  getFontSizeClass(): string {
    switch (this.fontSize()) {
      case 'small':
        return 'text-sm';
      case 'large':
        return 'text-lg';
      default:
        return 'text-base';
    }
  }

  getProcessingProgress(): number {
    const transcription = this.transcription();
    if (!transcription) return 0;
    
    switch (transcription.status) {
      case TranscriptionStatus.PENDING:
        return 10;
      case TranscriptionStatus.PROCESSING:
        return 50;
      case TranscriptionStatus.COMPLETED:
        return 100;
      default:
        return 0;
    }
  }

  // Dual Model Support Methods
  private checkForComparisonData(transcription: any): void {
    // Check for new model-specific fields from backend redesign
    const hasWhisperText = transcription.whisper_text;
    const hasWav2vecText = transcription.wav2vec_text;
    const isBothModel = transcription.model_used === 'both';
    
    if (isBothModel && hasWhisperText && hasWav2vecText) {
      // New comparison mode with separate model results
      this._isComparisonMode.set(true);
      
      // Create result objects for compatibility with existing UI
      this._whisperResult.set({
        text: transcription.whisper_text,
        confidence: transcription.whisper_confidence,
        segments: transcription.segments?.filter((s: any) => s.model_source === 'whisper') || []
      });
      
      this._wav2vecResult.set({
        text: transcription.wav2vec_text,
        confidence: transcription.wav2vec_confidence,
        segments: transcription.segments?.filter((s: any) => s.model_source === 'wav2vec2') || []
      });
      
      if (transcription.comparison_metrics) {
        this._comparisonMetrics.set(transcription.comparison_metrics);
      }
      
      this._activeModelTab.set('comparison');
    } else if (isBothModel) {
      // Both model selected but processing may still be in progress
      this._isComparisonMode.set(true);
      this._activeModelTab.set('whisper');
    } else {
      // Single model mode
      this._isComparisonMode.set(false);
      if (transcription.model_used?.includes('whisper')) {
        this._activeModelTab.set('whisper');
      } else if (transcription.model_used?.includes('wav2vec')) {
        this._activeModelTab.set('wav2vec2');
      }
    }
  }

  switchModelTab(tab: 'whisper' | 'wav2vec2' | 'comparison'): void {
    this._activeModelTab.set(tab);
  }

  getCurrentDisplayText(): string {
    const activeTab = this.activeModelTab();
    const transcription = this.transcription();
    
    if (!this.isComparisonMode()) {
      return transcription?.text || '';
    }
    
    switch (activeTab) {
      case 'whisper':
        return this.whisperResult()?.text || transcription?.whisper_text || '';
      case 'wav2vec2':
        return this.wav2vecResult()?.text || transcription?.wav2vec_text || '';
      case 'comparison':
        return transcription?.text || '';
      default:
        return transcription?.text || '';
    }
  }

  getModelSegments(model: 'whisper' | 'wav2vec2'): TranscriptionSegment[] {
    if (!this.isComparisonMode()) {
      return this.segments();
    }
    
    const modelResult = model === 'whisper' ? this.whisperResult() : this.wav2vecResult();
    return modelResult?.segments || [];
  }


  getModelMetrics(model: 'whisper' | 'wav2vec2'): any {
    if (!this.comparisonMetrics()) return null;
    
    const metrics = this.comparisonMetrics();
    return model === 'whisper' ? metrics.whisper_metrics : metrics.wav2vec_metrics;
  }

  hasAccuracyData(): boolean {
    return !!this.comparisonMetrics();
  }

  exportTranscription(format: 'txt' | 'srt' | 'docx' | 'pdf' = 'txt'): void {
    this.downloadTranscription(format);
  }

  isSegmentActive(index: number): boolean {
    return this.activeSegmentIndex() === index;
  }

  seekToSegment(segment: TranscriptionSegment): void {
    if (this.audioPlayerRef?.nativeElement) {
      this.audioPlayerRef.nativeElement.currentTime = segment.start_time;
    }
    this._selectedSegment.set(segment);
  }

  seekToTime(time: number): void {
    const audio = this.audioPlayerRef?.nativeElement;
    if (!audio) return;
    
    // Use effective audio duration for accurate bounds checking
    const maxTime = this.effectiveAudioDuration();
    const clampedTime = Math.max(0, Math.min(time, maxTime));
    
    // Update the audio element
    audio.currentTime = clampedTime;
    
    // Immediately update the UI state to provide responsive feedback
    this._currentPlaybackTime.set(clampedTime);
    
    console.log(`Seeked to: ${clampedTime}s (max: ${maxTime}s)`);
  }

  toggleSegmentPlay(index: number): void {
    const segments = this.segments();
    if (!segments || index >= segments.length) return;
    
    const segment = segments[index];
    this.seekToSegment(segment);
    
    if (this.audioPlayerRef?.nativeElement) {
      if (this.audioPlayerRef.nativeElement.paused) {
        this.audioPlayerRef.nativeElement.play();
      } else {
        this.audioPlayerRef.nativeElement.pause();
      }
    }
  }

  playingSegment(): number {
    return this._isPlaying() ? this.activeSegmentIndex() : -1;
  }

  changePlaybackSpeed(event: any): void {
    const speed = event.value;
    this._selectedPlaybackSpeed.set(speed);
    
    if (this.audioPlayerRef?.nativeElement) {
      this.audioPlayerRef.nativeElement.playbackRate = speed;
    }
  }

  getProcessingSpeedLabel(processingTime: number | undefined): string {
    if (!processingTime) return 'N/A';
    
    const transcription = this.transcription();
    if (!transcription?.duration_seconds) return 'N/A';
    
    const ratio = transcription.duration_seconds / processingTime;
    
    if (ratio >= 10) return 'Πολύ γρήγορη';
    if (ratio >= 5) return 'Γρήγορη';
    if (ratio >= 2) return 'Μέτρια';
    return 'Αργή';
  }

  getProcessingTimeInSeconds(processingTime: number | undefined): number | undefined {
    if (!processingTime) return undefined;
    
    // If the processing time seems to be in milliseconds (very large number), convert to seconds
    // Assume if it's > 1000, it's probably in milliseconds
    if (processingTime > 1000) {
      return processingTime / 1000;
    }
    
    return processingTime;
  }

  getFormattedProcessingTime(processingTime: number | undefined): string {
    if (!processingTime) return 'N/A';
    
    const timeInSeconds = this.getProcessingTimeInSeconds(processingTime);
    if (!timeInSeconds) return 'N/A';
    
    return `${timeInSeconds.toFixed(2)}s`;
  }

  getReliableProcessingTimeInSeconds(): number | undefined {
    const transcription = this.transcription();
    if (!transcription) return undefined;

    // For comparison transcriptions, prefer the specific model times
    if (transcription.whisper_processing_time && transcription.wav2vec_processing_time) {
      // Return the faster one (average if both are similar)
      const whisperTime = transcription.whisper_processing_time;
      const wav2vecTime = transcription.wav2vec_processing_time;
      return Math.min(whisperTime, wav2vecTime);
    }

    // For single model transcriptions, use the specific model time
    if (transcription.whisper_processing_time) {
      return transcription.whisper_processing_time;
    }
    
    if (transcription.wav2vec_processing_time) {
      return transcription.wav2vec_processing_time;
    }

    // Fallback to the general processing_time only if it seems reasonable (< 300 seconds = 5 minutes)
    if (transcription.processing_time && transcription.processing_time < 300) {
      return transcription.processing_time;
    }

    // If general processing_time is too large (probably milliseconds), convert it
    if (transcription.processing_time && transcription.processing_time > 1000) {
      const converted = transcription.processing_time / 1000;
      // Only use if the converted time is reasonable (< 300 seconds)
      if (converted < 300) {
        return converted;
      }
    }

    return undefined;
  }

  getReliableProcessingTime(): string {
    const timeInSeconds = this.getReliableProcessingTimeInSeconds();
    if (!timeInSeconds) return 'N/A';
    
    return `${timeInSeconds.toFixed(2)}s`;
  }

  private initializeAudioPlayer(): void {
    if (!this.audioPlayerRef?.nativeElement) return;
    
    const audio = this.audioPlayerRef.nativeElement;
    
    audio.addEventListener('timeupdate', () => {
      this._currentPlaybackTime.set(audio.currentTime);
    });
    
    audio.addEventListener('play', () => {
      this._isPlaying.set(true);
    });
    
    audio.addEventListener('pause', () => {
      this._isPlaying.set(false);
    });
    
    audio.addEventListener('ended', () => {
      this._isPlaying.set(false);
      this._currentPlaybackTime.set(0);
    });
    
    audio.playbackRate = this.selectedPlaybackSpeed();
  }

  togglePlayAll(): void {
    const audio = this.audioPlayerRef?.nativeElement;
    if (!audio) return;
    
    if (this._isPlaying()) {
      audio.pause();
    } else {
      audio.play().catch(error => {
        console.error('Audio play failed:', error);
        this.notificationService.error('Αδυναμία αναπαραγωγής του αρχείου ήχου');
      });
    }
  }

  deleteTranscription(): void {
    const id = this.transcriptionId();
    if (!id) return;
    
    this.confirmationService.confirm({
      message: 'Είστε σίγουροι ότι θέλετε να διαγράψετε αυτή τη μεταγραφή; Αυτή η ενέργεια δεν μπορεί να αναιρεθεί.',
      header: 'Επιβεβαίωση Διαγραφής',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'Ναι, διαγραφή',
      rejectLabel: 'Ακύρωση',
      accept: () => {
        this.transcriptionService.deleteTranscription(id).subscribe({
          next: () => {
            this.notificationService.success('Η μεταγραφή διαγράφηκε επιτυχώς');
            this.router.navigate(['/app/transcriptions']);
          },
          error: (error) => {
            console.error('Failed to delete transcription:', error);
            this.notificationService.error('Αποτυχία διαγραφής μεταγραφής');
          }
        });
      }
    });
  }

  private loadSegments(): void {
    const id = this.transcriptionId();
    if (!id) return;

    this.transcriptionService.getTranscriptionSegments(id).subscribe({
      next: (response: any) => {
        const segments = response.segments || response;
        this._segments.set(segments);
        
        setTimeout(() => {
          this.initializeEnhancedAudioPlayerWithRetry();
        }, 100);
      },
      error: (error) => {
        console.error('Error loading segments:', error);
      }
    });
  }

  get activeModelTabValue(): 'whisper' | 'wav2vec2' | 'comparison' {
    return this.activeModelTab();
  }

  set activeModelTabValue(tab: 'whisper' | 'wav2vec2' | 'comparison') {
    this._activeModelTab.set(tab);
  }

  // Helper methods για template
  getActiveModelMetrics(): any {
    const activeTab = this.activeModelTab();
    if (activeTab === 'whisper' || activeTab === 'wav2vec2') {
      return this.getModelMetrics(activeTab);
    }
    return null;
  }

  hasActiveModelMetrics(): boolean {
    const activeTab = this.activeModelTab();
    return activeTab !== 'comparison' && !!this.getActiveModelMetrics();
  }

  getActiveModelWER(): string {
    const metrics = this.getActiveModelMetrics();
    return metrics?.wer || 'N/A';
  }

  getActiveModelSpeed(): string {
    const metrics = this.getActiveModelMetrics();
    return metrics?.speed || 'N/A';
  }

  // Model tab navigation methods
  setActiveModelTab(tab: 'whisper' | 'wav2vec2' | 'comparison'): void {
    this._activeModelTab.set(tab);
  }

  // Helper methods for comparison metrics
  getBetterSpeedModel(): string | null {
    const transcription = this.transcription();
    if (!transcription) return null;
    
    // Use the faster_model field from backend if available
    if (transcription.faster_model) {
      return transcription.faster_model === 'whisper' ? 'Whisper' : 'Wav2Vec2';
    }
    
    // Fallback to calculation if faster_model not available
    const whisperTime = transcription.whisper_processing_time;
    const wav2vecTime = transcription.wav2vec_processing_time;
    
    if (whisperTime && wav2vecTime) {
      return whisperTime < wav2vecTime ? 'Whisper' : 'Wav2Vec2';
    }
    return null;
  }

  getBestPerformingModelDisplay(): string {
    const transcription = this.transcription();
    if (!transcription?.best_performing_model) return 'N/A';
    
    switch (transcription.best_performing_model) {
      case 'whisper':
        return 'Whisper';
      case 'wav2vec2':
        return 'Wav2Vec2';
      case 'tie':
        return 'Ισοπαλία (100% και τα δύο)';
      default:
        return 'N/A';
    }
  }

  // WER/CER Calculator Methods
  toggleWERCalculator(): void {
    const isOpening = !this.showWERCalculator();
    this._showWERCalculator.set(isOpening);
    
    if (isOpening) {
      // When opening, reload existing evaluation data if available
      const transcription = this.transcription();
      if (transcription) {
        this.loadExistingEvaluation(transcription, false); // Don't auto-open since we're already opening
      }
    }
    // Don't clear results when closing - keep them for when user reopens
  }

  uploadGroundTruth(event: any): void {
    const file = event.files?.[0];
    if (!file) return;

    if (file.type !== 'text/plain') {
      this.notificationService.warning('Παρακαλώ ανεβάστε ένα .txt αρχείο');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      if (text) {
        this._groundTruthText.set(text.trim());
        this.notificationService.success('Το σωστό κείμενο φορτώθηκε επιτυχώς');
      }
    };
    reader.readAsText(file);
  }

  setGroundTruthText(text: string): void {
    this._groundTruthText.set(text);
  }

  calculateWER(): void {
    const transcription = this.transcription();
    const groundTruth = this.groundTruthText().trim();

    if (!transcription?.text || !groundTruth) {
      this.notificationService.warning('Απαιτείται κείμενο μεταγραφής και σωστό κείμενο');
      return;
    }

    this._isCalculatingWER.set(true);

    // Save to backend for persistence
    this.transcriptionService.evaluateTranscription(transcription.id, groundTruth).subscribe({
      next: (response: any) => {
        console.log('Evaluation response:', response);
        
        // Use the evaluation results from backend - handle both response formats
        if (response.transcription) {
          // Update the current transcription with the new evaluation data
          this._transcription.set(response.transcription);
        }
        
        // Display results based on what was calculated
        const evaluation = response.evaluation_results;
        
        let message = 'Η αξιολόγηση ολοκληρώθηκε επιτυχώς!';
        if (evaluation) {
          if (evaluation.whisper_wer !== null && evaluation.whisper_wer !== undefined && 
              evaluation.wav2vec_wer !== null && evaluation.wav2vec_wer !== undefined) {
            // Both models evaluated - comparison mode
            const bestModel = evaluation.best_model === 'whisper' ? 'Whisper' : 'Wav2Vec2';
            message = `Σύγκριση ολοκληρώθηκε! Καλύτερο: ${bestModel} - Whisper: ${evaluation.whisper_wer.toFixed(1)}%, Wav2Vec2: ${evaluation.wav2vec_wer.toFixed(1)}%`;
          } else if (evaluation.whisper_wer !== null && evaluation.whisper_wer !== undefined) {
            const accuracy = evaluation.whisper_accuracy?.toFixed(1) || '0.0'; // Use backend calculated accuracy
            message = `Whisper WER: ${evaluation.whisper_wer.toFixed(1)}% - Ακρίβεια: ${accuracy}%`;
          } else if (evaluation.wav2vec_wer !== null && evaluation.wav2vec_wer !== undefined) {
            const accuracy = evaluation.wav2vec_accuracy?.toFixed(1) || '0.0'; // Use backend calculated accuracy
            message = `Wav2Vec2 WER: ${evaluation.wav2vec_wer.toFixed(1)}% - Ακρίβεια: ${accuracy}%`;
          }
        }
        
        this.notificationService.success(message);
        
        // Update WER result signals for UI display
        this.updateWERResultsFromTranscription(response.transcription);
        
        this.updateChartsAfterWER();
      },
      error: (error: any) => {
        console.error('WER evaluation error:', error);
        this.notificationService.error('Σφάλμα κατά την αποθήκευση αξιολόγησης');
      },
      complete: () => {
        this._isCalculatingWER.set(false);
      }
    });
  }

  calculateComparisonWER(): void {
    const transcription = this.transcription();
    const groundTruth = this.groundTruthText().trim();

    if (!transcription?.whisper_text || !transcription?.wav2vec_text || !groundTruth) {
      this.notificationService.warning('Απαιτούνται αποτελέσματα από τα δύο μοντέλα και σωστό κείμενο');
      return;
    }

    this._isCalculatingWER.set(true);

    // Save to backend for persistence
    this.transcriptionService.evaluateTranscription(transcription.id, groundTruth).subscribe({
      next: (response: any) => {
        console.log('Comparison evaluation response:', response);
        
        // Use the evaluation results from backend - handle direct response format
        if (response.transcription) {
          // Update the current transcription with the new evaluation data
          this._transcription.set(response.transcription);
        }
        
        // Display results based on what was calculated
        const evaluation = response.evaluation_results;
        
        let message = 'Η συγκριτική αξιολόγηση ολοκληρώθηκε επιτυχώς!';
        if (evaluation && evaluation.best_model) {
          const bestModel = evaluation.best_model === 'whisper' ? 'Whisper' : 'Wav2Vec2';
          const whisperWer = evaluation.whisper_wer?.toFixed(1) || 'N/A';
          const wav2vecWer = evaluation.wav2vec_wer?.toFixed(1) || 'N/A';
          message = `Καλύτερο μοντέλο: ${bestModel} - Whisper WER: ${whisperWer}%, Wav2Vec2 WER: ${wav2vecWer}%`;
        }
        
        this.notificationService.success(message);
        
        // Update WER result signals for UI display
        this.updateWERResultsFromTranscription(response.transcription);
        
        this.updateChartsAfterWER();
      },
      error: (error: any) => {
        console.error('Comparison WER evaluation error:', error);
        this.notificationService.error('Σφάλμα κατά την αποθήκευση συγκριτικής αξιολόγησης');
      },
      complete: () => {
        this._isCalculatingWER.set(false);
      }
    });
  }

  public updateGroundTruthText(event: Event): void {
    const target = event.target as HTMLTextAreaElement;
    this._groundTruthText.set(target.value);
  }

  clearWERResults(): void {
    this._werResult.set(null);
    this._comparisonWerResult.set(null);
    this._groundTruthText.set('');
  }

  /**
   * Load existing WER/CER evaluation data when transcription is loaded
   */
  private loadExistingEvaluation(transcription: any, autoOpen: boolean = false): void {
    // Check if transcription has evaluation data from the server
    if (transcription.has_evaluation || transcription.evaluation_completed) {
      // Set ground truth text if available
      if (transcription.ground_truth_text) {
        this._groundTruthText.set(transcription.ground_truth_text);
      }

      // Auto-open the WER calculator only if explicitly requested
      if (autoOpen) {
        this._showWERCalculator.set(true);
      }

      // Create WER results from backend data
      if (transcription.whisper_wer !== undefined || transcription.wav2vec_wer !== undefined) {
        
        // For single model results - use backend data
        if (transcription.text && transcription.ground_truth_text) {
          const result = this.createWERFromBackend(transcription);
          if (result) {
            this._werResult.set(result);
          }
        }

        // For comparison results - use backend data
        if (transcription.whisper_text && transcription.wav2vec_text && transcription.ground_truth_text) {
          const comparisonResult = this.createComparisonWERFromBackend(transcription);
          if (comparisonResult) {
            this._comparisonWerResult.set(comparisonResult);
          }
        }
      }
    }
  }

  /**
   * Update WER result signals from updated transcription data (after evaluation)
   * All data comes from backend - no frontend calculations
   */
  private updateWERResultsFromTranscription(transcription: any): void {
    if (!transcription) return;

    try {
      // For single model results - use backend data
      if (transcription.text && transcription.ground_truth_text) {
        const result = this.createWERFromBackend(transcription);
        if (result) {
          this._werResult.set(result);
        }
      }

      // For comparison results - use backend data
      if (transcription.whisper_text && transcription.wav2vec_text && transcription.ground_truth_text) {
        const comparisonResult = this.createComparisonWERFromBackend(transcription);
        if (comparisonResult) {
          this._comparisonWerResult.set(comparisonResult);
        }
      }
    } catch (error) {
      console.warn('Error updating WER results from transcription:', error);
    }
  }

  getWERInterpretation(wer: number): any {
    // WER interpretation logic moved to backend or use static mapping
    const werPercentage = wer; // Assume wer is already percentage from backend
    
    if (werPercentage <= 5) {
      return {
        level: 'excellent',
        description: 'Εξαιρετική ακρίβεια',
        color: 'green'
      };
    } else if (werPercentage <= 15) {
      return {
        level: 'good',
        description: 'Καλή ακρίβεια',
        color: 'blue'
      };
    } else if (werPercentage <= 30) {
      return {
        level: 'fair',
        description: 'Μέτρια ακρίβεια',
        color: 'orange'
      };
    } else {
      return {
        level: 'poor',
        description: 'Χαμηλή ακρίβεια',
        color: 'red'
      };
    }
  }

  getWERResultCardHeader(): string {
    const transcription = this.transcription();
    if (!transcription) return 'Αποτελέσματα WER/CER';
    
    // Check if it's a comparison transcription with evaluation data (has both models)
    if (transcription.has_evaluation && transcription.whisper_wer !== null && transcription.wav2vec_wer !== null) {
      return 'Αποτελέσματα WER/CER (Σύγκριση Μοντέλων)';
    }
    
    const modelUsed = transcription.model_used;
    if (modelUsed?.includes('whisper') || modelUsed === 'whisper') {
      return 'Αποτελέσματα WER/CER (Whisper)';
    } else if (modelUsed?.includes('wav2vec') || modelUsed === 'wav2vec2') {
      return 'Αποτελέσματα WER/CER (Wav2Vec2)';
    }
    
    return 'Αποτελέσματα WER/CER';
  }

  formatWERResult(result: WERResult): string {
    // Simple formatting - no calculations
    return `WER: ${result.werPercentage}% | CER: ${result.cerPercentage}% | Ακρίβεια: ${result.accuracy.toFixed(1)}%`;
  }

  getGroundTruthWordCount(): number {
    // Use backend calculated ground truth word count
    const transcription = this.transcription();
    return transcription?.ground_truth_word_count || 0; // Backend calculated
  }

  getTotalErrors(werResult: any): number {
    // Backend calculated total errors
    if (!werResult) return 0;
    return werResult.totalErrors || ((werResult.substitutions || 0) + (werResult.deletions || 0) + (werResult.insertions || 0));
  }

  // ======= COMPARISON CHARTS METHODS =======

  toggleCharts(): void {
    this._showCharts.set(!this.showCharts());
    if (this.showCharts()) {
      this.updateChartData();
    }
  }

  updateChartData(): void {
    const transcription = this.transcription();
    const comparisonWER = this.comparisonWerResult();
    const werResult = this.werResult();

    if (!transcription) return;

    // Prepare chart data
    const chartData: ComparisonChartData = {};

    // Add WER results - prioritize backend data over local calculations
    if (comparisonWER) {
      chartData.comparisonWER = comparisonWER;
    } else if (werResult) {
      chartData.werResult = werResult;
      // Even for local werResult, we need to set modelUsed
      if (transcription.model_used) {
        chartData.modelUsed = (transcription.model_used?.includes('wav2vec') || transcription.model_used === 'wav2vec2') ? 'wav2vec2' : 'whisper';
        console.log('🎯 ChartData Debug (Local WER + ModelUsed):', {
          model_used_original: transcription.model_used,
          modelUsed_set: chartData.modelUsed,
          includesWav2vec: transcription.model_used?.includes('wav2vec'),
          equalsWav2vec2: transcription.model_used === 'wav2vec2',
          werResult_type: 'local'
        });
      }
    } else if (transcription.has_evaluation && transcription.model_used) {
      // Check if this is a single model transcription by looking at model_used field
      // Even if both models have evaluation data, we should respect the original model
      const werResult = this.createWERFromBackend(transcription);
      if (werResult) {
        chartData.werResult = werResult;
        // Determine which model was used for single model charts
        chartData.modelUsed = (transcription.model_used?.includes('wav2vec') || transcription.model_used === 'wav2vec2') ? 'wav2vec2' : 'whisper';
        
        // Debug logging
        console.log('🎯 ChartData Debug (Fixed Logic):', {
          model_used_original: transcription.model_used,
          modelUsed_set: chartData.modelUsed,
          includesWav2vec: transcription.model_used?.includes('wav2vec'),
          equalsWav2vec2: transcription.model_used === 'wav2vec2',
          werResult: !!werResult
        });
      }
    } else if (this.hasBackendEvaluationData(transcription)) {
      // Create comparison WER from backend data (only for true comparison transcriptions)
      chartData.comparisonWER = this.createComparisonWERFromBackend(transcription);
      console.log('📊 Using Backend Evaluation Data (Comparison)');
    }

    // Add processing times if available
    if (transcription.whisper_processing_time || transcription.wav2vec_processing_time) {
      chartData.processingTimes = {
        whisper: transcription.whisper_processing_time,
        wav2vec: transcription.wav2vec_processing_time
      };
    }

    // Add confidence scores if available
    if (transcription.whisper_confidence || transcription.wav2vec_confidence) {
      chartData.confidenceScores = {
        whisper: transcription.whisper_confidence,
        wav2vec: transcription.wav2vec_confidence
      };
    }

    // Add transcription results for potential future use
    if (transcription.whisper_text) {
      chartData.whisperResult = {
        id: transcription.id,
        text: transcription.whisper_text,
        status: transcription.status,
        confidence_score: transcription.whisper_confidence,
        processing_time: transcription.whisper_processing_time,
        created_at: transcription.created_at,
        updated_at: transcription.updated_at
      } as any;
    }

    if (transcription.wav2vec_text) {
      chartData.wav2vecResult = {
        id: transcription.id,
        text: transcription.wav2vec_text,
        status: transcription.status,
        confidence_score: transcription.wav2vec_confidence,
        processing_time: transcription.wav2vec_processing_time,
        created_at: transcription.created_at,
        updated_at: transcription.updated_at
      } as any;
    }

    this._chartData.set(chartData);
  }

  hasChartData(): boolean {
    const transcription = this.transcription();
    if (!transcription) return false;
    
    // Check for comparison mode (both models)
    const hasComparisonData = !!(transcription.whisper_text && transcription.wav2vec_text);
    const hasComparisonCharts = hasComparisonData && !!(this.comparisonWerResult() || 
             (transcription.whisper_processing_time || transcription.wav2vec_processing_time));
    
    // Check for single model with WER evaluation (Performance Charts)
    const hasSingleModelWER = !hasComparisonData && !!transcription.has_evaluation && 
      (transcription.whisper_wer !== null || transcription.wav2vec_wer !== null);
    
    // Show charts if:
    // 1. Comparison mode with data, OR
    // 2. Single model with WER calculated
    return !!(hasComparisonCharts || hasSingleModelWER);
  }

  // Called after WER calculations to update charts
  private updateChartsAfterWER(): void {
    // Auto-open charts section when WER is calculated
    if (this.hasChartData()) {
      this._showCharts.set(true);
      this.updateChartData();
    }
  }

  private hasBackendEvaluationData(transcription: any): boolean {
    return transcription.has_evaluation && 
           transcription.whisper_wer !== null && 
           transcription.wav2vec_wer !== null &&
           transcription.whisper_accuracy !== null &&
           transcription.wav2vec_accuracy !== null;
  }

  private hasSingleModelEvaluationData(transcription: any): boolean {
    if (!transcription.has_evaluation) return false;
    
    const hasWhisperData = transcription.whisper_wer !== null && transcription.whisper_accuracy !== null;
    const hasWav2vecData = transcription.wav2vec_wer !== null && transcription.wav2vec_accuracy !== null;
    
    // Return true if we have data for at least one model but not both (single model)
    return (hasWhisperData || hasWav2vecData) && !(hasWhisperData && hasWav2vecData);
  }

  private createWERFromBackend(transcription: any): WERResult | null {
    // Create WER result from backend calculated data only
    const modelUsed = transcription.model_used;
    
    if ((modelUsed?.includes('whisper') || modelUsed === 'whisper') && transcription.whisper_wer !== null) {
      return {
        wer: transcription.whisper_wer || 0, // Backend already calculates as decimal
        cer: transcription.whisper_cer || 0, // Backend already calculates as decimal
        werPercentage: transcription.whisper_wer || 0,
        cerPercentage: transcription.whisper_cer || 0,
        accuracy: transcription.whisper_accuracy || 0, // Backend calculated
        charAccuracy: transcription.whisper_char_accuracy || 0, // Backend calculated
        substitutions: transcription.whisper_substitutions || 0,
        deletions: transcription.whisper_deletions || 0,
        insertions: transcription.whisper_insertions || 0,
        diacriticErrors: transcription.whisper_diacritic_errors || 0,
        diacriticAccuracy: transcription.whisper_diacritic_accuracy || 0,
        greekCharacterAccuracy: transcription.whisper_greek_char_accuracy || 0,
        // Additional required fields
        wordCount: 0, // Would need to be calculated in backend
        correctWords: 0, // Would need to be calculated in backend
        characterCount: 0, // Would need to be calculated in backend
        charSubstitutions: 0, // Would need to be calculated in backend
        charDeletions: 0, // Would need to be calculated in backend
        charInsertions: 0, // Would need to be calculated in backend
        correctCharacters: 0, // Would need to be calculated in backend
        greekCharacterCount: 0 // Would need to be calculated in backend
      };
    } else if ((modelUsed?.includes('wav2vec') || modelUsed === 'wav2vec2') && transcription.wav2vec_wer !== null) {
      return {
        wer: transcription.wav2vec_wer || 0, // Backend already calculates as decimal
        cer: transcription.wav2vec_cer || 0, // Backend already calculates as decimal
        werPercentage: transcription.wav2vec_wer || 0,
        cerPercentage: transcription.wav2vec_cer || 0,
        accuracy: transcription.wav2vec_accuracy || 0, // Backend calculated
        charAccuracy: transcription.wav2vec_char_accuracy || 0, // Backend calculated
        substitutions: transcription.wav2vec_substitutions || 0,
        deletions: transcription.wav2vec_deletions || 0,
        insertions: transcription.wav2vec_insertions || 0,
        diacriticErrors: transcription.wav2vec_diacritic_errors || 0,
        diacriticAccuracy: transcription.wav2vec_diacritic_accuracy || 0,
        greekCharacterAccuracy: transcription.wav2vec_greek_char_accuracy || 0,
        // Additional required fields
        wordCount: 0, // Would need to be calculated in backend
        correctWords: 0, // Would need to be calculated in backend
        characterCount: 0, // Would need to be calculated in backend
        charSubstitutions: 0, // Would need to be calculated in backend
        charDeletions: 0, // Would need to be calculated in backend
        charInsertions: 0, // Would need to be calculated in backend
        correctCharacters: 0, // Would need to be calculated in backend
        greekCharacterCount: 0 // Would need to be calculated in backend
      };
    }
    
    return null;
  }

  private createComparisonWERFromBackend(transcription: any): any {
    console.log('Backend transcription data:', {
      whisper_wer: transcription.whisper_wer,
      whisper_cer: transcription.whisper_cer,
      whisper_accuracy: transcription.whisper_accuracy,
      wav2vec_wer: transcription.wav2vec_wer,
      wav2vec_cer: transcription.wav2vec_cer,
      wav2vec_accuracy: transcription.wav2vec_accuracy,
      academic_accuracy_score: transcription.academic_accuracy_score,
      best_performing_model: transcription.best_performing_model
    });

    return {
      whisperWER: {
        werPercentage: transcription.whisper_wer || 0,
        cerPercentage: transcription.whisper_cer || 0,
        accuracy: transcription.whisper_accuracy || 0, // Backend calculated as percentage
        charAccuracy: transcription.whisper_char_accuracy || 0, // Backend calculated as percentage
        substitutions: transcription.whisper_substitutions || 0, // Backend calculated substitutions
        deletions: transcription.whisper_deletions || 0, // Backend calculated deletions
        insertions: transcription.whisper_insertions || 0, // Backend calculated insertions
        diacriticErrors: transcription.whisper_diacritic_errors || 0, // Backend pre-calculated diacritic errors
        greekCharacterAccuracy: transcription.whisper_greek_char_accuracy || 0, // Backend calculated Greek char accuracy
        diacriticAccuracy: transcription.whisper_diacritic_accuracy || 0 // Backend calculated diacritic accuracy
      },
      wav2vecWER: {
        werPercentage: transcription.wav2vec_wer || 0,
        cerPercentage: transcription.wav2vec_cer || 0,
        accuracy: transcription.wav2vec_accuracy || 0, // Backend calculated as percentage
        charAccuracy: transcription.wav2vec_char_accuracy || 0, // Backend calculated as percentage
        substitutions: transcription.wav2vec_substitutions || 0, // Backend calculated substitutions
        deletions: transcription.wav2vec_deletions || 0, // Backend calculated deletions
        insertions: transcription.wav2vec_insertions || 0, // Backend calculated insertions
        diacriticErrors: transcription.wav2vec_diacritic_errors || 0, // Backend pre-calculated diacritic errors
        greekCharacterAccuracy: transcription.wav2vec_greek_char_accuracy || 0, // Backend calculated Greek char accuracy
        diacriticAccuracy: transcription.wav2vec_diacritic_accuracy || 0 // Backend calculated diacritic accuracy
      }
    };
  }

  /**
   * Generate authenticated audio URL that works with HTML audio element
   */
  private generateAuthenticatedAudioUrl(audioFileId: number): void {
    // Check if this is a large file by getting file info first
    const audioFile = this.transcription()?.audio_file;
    const fileSizeBytes = audioFile?.file_size || 0;
    const fileSizeMB = fileSizeBytes / (1024 * 1024);
    
    // For large files (>100MB), use streaming endpoint
    if (fileSizeMB > 100) {
      console.log(`Large file detected (${fileSizeMB.toFixed(1)}MB), using streaming endpoint`);
      
      // Use streaming endpoint for large files - no blob download
      const streamUrl = this.apiService.getAuthenticatedUrl(`/audio/${audioFileId}/stream`);
      this._audioUrl.set(streamUrl);
      
      // No notification - let it work silently
      return;
    }
    
    // For smaller files, use the traditional blob method
    this.apiService.download(`/audio/${audioFileId}/download`, {
      showErrorMessage: false
    }).subscribe({
      next: (blob: Blob) => {
        // Create object URL from the blob
        const objectUrl = URL.createObjectURL(blob);
        this._audioUrl.set(objectUrl);
        
        // Clean up any previous object URL
        if (this.previousObjectUrl) {
          URL.revokeObjectURL(this.previousObjectUrl);
        }
        this.previousObjectUrl = objectUrl;
      },
      error: (error) => {
        console.error('Failed to load audio file:', error);
        
        // Fallback to streaming endpoint if blob download fails
        console.log('Falling back to streaming endpoint...');
        const streamUrl = this.apiService.getAuthenticatedUrl(`/audio/${audioFileId}/stream`);
        this._audioUrl.set(streamUrl);
      }
    });
  }

  // Keep track of object URLs for cleanup
  private previousObjectUrl: string | null = null;

  /**
   * Audio event handlers for better user feedback
   */
  onAudioLoadStart(): void {
    console.log('Audio loading started');
  }

  onAudioLoadedMetadata(): void {
    console.log('Audio metadata loaded');
    const audio = this.audioPlayerRef?.nativeElement;
    if (audio && !isNaN(audio.duration)) {
      this._actualAudioDuration.set(audio.duration);
      console.log(`Actual audio duration: ${audio.duration}s (DB duration: ${this.transcription()?.duration_seconds}s)`);
    }
  }

  onAudioError(event: Event): void {
    const audio = event.target as HTMLAudioElement;
    const error = audio.error;
    
    console.log('Audio error event:', event, 'Error code:', error?.code, 'Network state:', audio.networkState);
    this._isPlaying.set(false);
    
    // For streaming URLs, be more tolerant of network issues
    const currentUrl = this._audioUrl();
    const isStreamingUrl = currentUrl && currentUrl.includes('/stream');
    
    if (isStreamingUrl) {
      // For streaming, ignore most network errors as they're often temporary SSL issues
      if (error?.code === MediaError.MEDIA_ERR_NETWORK || 
          audio.networkState === HTMLMediaElement.NETWORK_NO_SOURCE) {
        console.log('Network error on streaming audio - ignoring (likely temporary SSL issue)');
        
        // Try to recover by reloading the audio source after a short delay
        setTimeout(() => {
          if (audio && !audio.src) {
            console.log('Attempting to recover streaming audio...');
            audio.load();
          }
        }, 1000);
        
        return; // Don't show error for streaming network issues
      }
    }
    
    // For other errors, show notification only if it's a real playback issue
    if (error?.code === MediaError.MEDIA_ERR_DECODE || 
        error?.code === MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED) {
      this.notificationService.error('Σφάλμα κατά την αναπαραγωγή του αρχείου ήχου');
    }
  }

  onAudioWaiting(event: Event): void {
    console.log('Audio waiting for data...');
    // Audio is buffering - don't show error, just wait
  }

  onAudioCanPlay(event: Event): void {
    console.log('Audio can start playing');
    // Audio has enough data to start playing
  }

  /**
   * Additional event handlers for better video file support
   */
  onTimeUpdate(event: Event): void {
    const audio = event.target as HTMLAudioElement;
    if (audio) {
      this._currentPlaybackTime.set(audio.currentTime);
    }
  }

  onPlayEvent(event: Event): void {
    console.log('Play event triggered');
    this._isPlaying.set(true);
  }

  onPauseEvent(event: Event): void {
    console.log('Pause event triggered');
    this._isPlaying.set(false);
  }

  onEndedEvent(event: Event): void {
    console.log('Audio ended');
    this._isPlaying.set(false);
    this._currentPlaybackTime.set(0);
  }

  /**
   * Enhanced audio player methods
   */
  stopAudio(): void {
    const audio = this.audioPlayerRef?.nativeElement;
    if (!audio) return;
    
    audio.pause();
    audio.currentTime = 0;
    this._currentPlaybackTime.set(0);
    this._isPlaying.set(false);
  }

  skipBackward(): void {
    const audio = this.audioPlayerRef?.nativeElement;
    if (!audio) return;
    
    const newTime = Math.max(0, audio.currentTime - 10);
    audio.currentTime = newTime;
    this._currentPlaybackTime.set(newTime);
  }

  skipForward(): void {
    const audio = this.audioPlayerRef?.nativeElement;
    if (!audio) return;
    
    const maxTime = this.effectiveAudioDuration();
    const newTime = Math.min(maxTime, audio.currentTime + 10);
    audio.currentTime = newTime;
    this._currentPlaybackTime.set(newTime);
  }

  toggleMute(): void {
    const audio = this.audioPlayerRef?.nativeElement;
    if (!audio) return;
    
    const isMuted = this.isAudioMuted();
    this._isAudioMuted.set(!isMuted);
    audio.muted = !isMuted;
  }

  changeVolume(volume: number): void {
    const audio = this.audioPlayerRef?.nativeElement;
    if (!audio) return;
    
    this._audioVolume.set(volume);
    audio.volume = volume;
    
    // Auto-unmute if volume is increased
    if (volume > 0 && this.isAudioMuted()) {
      this._isAudioMuted.set(false);
      audio.muted = false;
    }
  }

  getProgressPercentage(): number {
    const current = this.currentPlaybackTime();
    const total = this.effectiveAudioDuration();
    
    if (total === 0) return 0;
    return Math.round((current / total) * 100);
  }

  /**
   * Initialize enhanced audio player with volume controls and video support
   */
  private initializeEnhancedAudioPlayer(): void {
    if (!this.audioPlayerRef?.nativeElement) return;
    
    const audio = this.audioPlayerRef.nativeElement;
    
    // Set initial volume
    audio.volume = this.audioVolume();
    audio.muted = this.isAudioMuted();
    
    // Enhanced event listeners with improved handling for video files
    audio.addEventListener('timeupdate', () => {
      this._currentPlaybackTime.set(audio.currentTime);
    });
    
    audio.addEventListener('play', () => {
      this._isPlaying.set(true);
      console.log('Audio started playing - state updated');
    });
    
    audio.addEventListener('pause', () => {
      this._isPlaying.set(false);
      console.log('Audio paused - state updated');
    });
    
    audio.addEventListener('ended', () => {
      this._isPlaying.set(false);
      this._currentPlaybackTime.set(0);
      console.log('Audio ended - state reset');
    });
    
    audio.addEventListener('volumechange', () => {
      this._audioVolume.set(audio.volume);
      this._isAudioMuted.set(audio.muted);
    });
    
    // Better error handling for video containers
    audio.addEventListener('error', (e) => {
      console.error('Audio element error:', e);
      this._isPlaying.set(false);
      this.onAudioError(e);
    });
    
    // Handle loading events for better UX with video files
    audio.addEventListener('loadstart', () => {
      console.log('Audio loading started');
      this.onAudioLoadStart();
    });
    
    audio.addEventListener('loadedmetadata', () => {
      console.log('Audio metadata loaded - duration:', audio.duration);
      if (!isNaN(audio.duration)) {
        this._actualAudioDuration.set(audio.duration);
      }
      this.onAudioLoadedMetadata();
    });
    
    audio.addEventListener('canplay', () => {
      console.log('Audio can start playing');
    });
    
    audio.addEventListener('canplaythrough', () => {
      console.log('Audio can play through without buffering');
    });
    
    audio.addEventListener('durationchange', () => {
      console.log('Audio duration changed:', audio.duration);
      if (!isNaN(audio.duration)) {
        this._actualAudioDuration.set(audio.duration);
      }
    });
    
    // Set playback rate
    audio.playbackRate = this.selectedPlaybackSpeed();
    
    console.log('Enhanced audio player initialized with video support');
  }

  /**
   * Initialize audio player with retry mechanism for video files
   */
  private initializeEnhancedAudioPlayerWithRetry(retryCount: number = 0): void {
    const maxRetries = 3;
    const retryDelay = 200;
    
    if (!this.audioPlayerRef?.nativeElement || !this.audioUrl()) {
      if (retryCount < maxRetries) {
        console.log(`Audio player not ready, retrying... (${retryCount + 1}/${maxRetries})`);
        setTimeout(() => {
          this.initializeEnhancedAudioPlayerWithRetry(retryCount + 1);
        }, retryDelay);
      } else {
        console.warn('Failed to initialize audio player after maximum retries');
      }
      return;
    }
    
    this.initializeEnhancedAudioPlayer();
    console.log('Audio player successfully initialized');
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