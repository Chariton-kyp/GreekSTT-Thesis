import { Component, Input, Output, EventEmitter, ViewChild, ElementRef, OnInit, OnDestroy, ChangeDetectionStrategy, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TranscriptionSegment } from '../../../core/models/transcription.model';

@Component({
  selector: 'app-audio-waveform',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="waveform-container" #waveformContainer>
      <canvas #waveformCanvas 
              [width]="canvasWidth()" 
              [height]="canvasHeight()"
              (click)="onCanvasClick($event)"
              (mousemove)="onCanvasMouseMove($event)"
              (mouseleave)="onCanvasMouseLeave()"
              class="waveform-canvas">
      </canvas>
      
      <!-- Segment overlays -->
      @for (segment of segments; track segment; let i = $index) {
        <div class="segment-overlay" 
             [style.left.%]="getSegmentPosition(segment).start"
             [style.width.%]="getSegmentPosition(segment).width"
             [class.active]="isSegmentActive(segment)"
             [attr.data-segment-index]="i"
             (click)="onSegmentOverlayClick(segment, $event)"
             [title]="getSegmentTooltip(segment)">
        </div>
      }
      
      <!-- Playhead -->
      <div class="playhead" 
           [style.left.%]="playheadPosition()">
        <div class="playhead-line"></div>
        <div class="playhead-time">{{ formatTime(currentTime) }}</div>
      </div>
      
      <!-- Hover indicator -->
      @if (isHovering()) {
        <div class="hover-indicator" 
             [style.left.px]="hoverX()">
          <div class="hover-line"></div>
          <div class="hover-time">{{ formatTime(hoverTime()) }}</div>
        </div>
      }
      
      <!-- Loading overlay -->
      @if (isLoading()) {
        <div class="loading-overlay">
          <div class="spinner"></div>
          <span>Φόρτωση κυματογράμματος...</span>
        </div>
      }
      
      <!-- Error overlay -->
      @if (hasError()) {
        <div class="error-overlay">
          <i class="pi pi-exclamation-triangle"></i>
          <span>Σφάλμα φόρτωσης κυματογράμματος</span>
        </div>
      }
    </div>
  `,
  styleUrls: ['./audio-waveform.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class AudioWaveformComponent implements OnInit, OnDestroy {
  @Input() audioUrl: string = '';
  @Input() segments: TranscriptionSegment[] = [];
  @Input() currentTime: number = 0;
  @Input() duration: number = 0;
  @Output() timeUpdate = new EventEmitter<number>();
  @Output() segmentClick = new EventEmitter<TranscriptionSegment>();

  @ViewChild('waveformCanvas', { static: true }) canvasRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('waveformContainer', { static: true }) containerRef!: ElementRef<HTMLDivElement>;

  // Canvas dimensions
  readonly canvasWidth = signal(800);
  readonly canvasHeight = signal(120);
  
  // Waveform data
  readonly waveformData = signal<Float32Array | null>(null);
  readonly audioDuration = signal(0);
  
  // UI state
  readonly isLoading = signal(false);
  readonly hasError = signal(false);
  readonly isHovering = signal(false);
  readonly hoverX = signal(0);
  readonly hoverTime = signal(0);
  readonly activeSegment = signal<TranscriptionSegment | null>(null);
  
  // Computed values
  readonly playheadPosition = computed(() => {
    const duration = this.audioDuration() || this.duration;
    return duration > 0 ? (this.currentTime / duration) * 100 : 0;
  });

  private audioContext?: AudioContext;
  private audioBuffer?: AudioBuffer;
  private resizeObserver?: ResizeObserver;
  private animationFrameId?: number;
  private readonly targetSamples = 1000; // Default sample count for waveform

  ngOnInit() {
    this.setupResizeObserver();
    this.initializeAudio();
  }

  ngOnDestroy() {
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
    if (this.audioContext) {
      this.audioContext.close();
    }
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }
  }

  private async initializeAudio(): Promise<void> {
    if (!this.audioUrl) return;

    this.isLoading.set(true);
    this.hasError.set(false);

    try {
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      
      // Check if this is a streaming URL (contains /stream)
      const isStreamingUrl = this.audioUrl.includes('/stream');
      const isLargeFile = isStreamingUrl || this.audioUrl.includes('X-Compressed-Stream');
      
      if (isLargeFile) {
        console.log('Large file detected - skipping waveform generation for performance');
        // For large files, create a simple placeholder waveform
        this.generatePlaceholderWaveform();
        this.isLoading.set(false);
        return;
      }
      
      // Check file size before downloading (if possible)
      const response = await fetch(this.audioUrl, { method: 'HEAD' });
      const contentLength = response.headers.get('content-length');
      const fileSizeMB = contentLength ? parseInt(contentLength) / (1024 * 1024) : 0;
      
      if (fileSizeMB > 50) {
        console.log(`Large file detected (${fileSizeMB.toFixed(1)}MB) - using placeholder waveform`);
        this.generatePlaceholderWaveform();
        this.isLoading.set(false);
        return;
      }
      
      // For smaller files, generate full waveform
      const fullResponse = await fetch(this.audioUrl);
      if (!fullResponse.ok) throw new Error('Failed to fetch audio');
      
      const arrayBuffer = await fullResponse.arrayBuffer();
      this.audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
      
      this.audioDuration.set(this.audioBuffer.duration);
      this.generateWaveformData();
      
      this.isLoading.set(false);
    } catch (error) {
      console.error('Failed to load audio for waveform:', error);
      this.hasError.set(true);
      this.isLoading.set(false);
    }
  }

  private generateWaveformData(): void {
    if (!this.audioBuffer) return;

    const channelData = this.audioBuffer.getChannelData(0);
    const samples = this.canvasWidth();
    const blockSize = Math.floor(channelData.length / samples);
    const waveformData = new Float32Array(samples * 2); // Store both positive and negative peaks

    for (let i = 0; i < samples; i++) {
      const start = i * blockSize;
      const end = Math.min(start + blockSize, channelData.length);
      let max = 0;
      let min = 0;

      for (let j = start; j < end; j++) {
        const value = channelData[j];
        if (value > max) max = value;
        if (value < min) min = value;
      }

      waveformData[i * 2] = max;
      waveformData[i * 2 + 1] = min;
    }

    this.waveformData.set(waveformData);
    this.drawWaveform();
  }

  private generatePlaceholderWaveform(): void {
    // Create a simple placeholder waveform for large files
    const sampleCount = Math.min(this.targetSamples, 500); // Reduced for performance
    const placeholderData = new Float32Array(sampleCount);
    
    // Generate a simple sine wave pattern with some randomness
    for (let i = 0; i < sampleCount; i++) {
      const x = (i / sampleCount) * Math.PI * 4; // 4 cycles across the waveform
      const baseWave = Math.sin(x) * 0.5;
      const randomVariation = (Math.random() - 0.5) * 0.3;
      const amplitude = Math.abs(baseWave + randomVariation);
      placeholderData[i] = amplitude;
    }
    
    this.waveformData.set(placeholderData);
    
    // Set a default duration (this will be updated by the audio element if available)
    if (this.audioDuration() === 0) {
      this.audioDuration.set(300); // 5 minutes default for large files
    }
  }

  private drawWaveform(): void {
    const canvas = this.canvasRef.nativeElement;
    const ctx = canvas.getContext('2d');
    if (!ctx || !this.waveformData()) return;

    const width = canvas.width;
    const height = canvas.height;
    const data = this.waveformData()!;
    const halfHeight = height / 2;

    // Clear canvas
    ctx.fillStyle = '#f8f9fa';
    ctx.fillRect(0, 0, width, height);

    // Draw center line
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, halfHeight);
    ctx.lineTo(width, halfHeight);
    ctx.stroke();

    // Draw waveform
    const barWidth = width / (data.length / 2);
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, '#3b82f6');
    gradient.addColorStop(0.5, '#60a5fa');
    gradient.addColorStop(1, '#3b82f6');
    
    ctx.fillStyle = gradient;

    for (let i = 0; i < data.length / 2; i++) {
      const max = data[i * 2];
      const min = data[i * 2 + 1];
      
      const x = i * barWidth;
      const topHeight = max * halfHeight * 0.9;
      const bottomHeight = -min * halfHeight * 0.9;
      
      // Draw top part
      ctx.fillRect(x, halfHeight - topHeight, barWidth - 1, topHeight);
      
      // Draw bottom part
      ctx.fillRect(x, halfHeight, barWidth - 1, bottomHeight);
    }

    // Draw segment markers
    this.drawSegmentMarkers(ctx);
  }

  private drawSegmentMarkers(ctx: CanvasRenderingContext2D): void {
    if (!this.segments || this.segments.length === 0) return;

    const width = this.canvasWidth();
    const height = this.canvasHeight();
    const duration = this.audioDuration() || this.duration;

    ctx.save();
    ctx.strokeStyle = '#6366f1';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 3]);

    this.segments.forEach(segment => {
      const x = (segment.start_time / duration) * width;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    });

    ctx.restore();
  }

  private setupResizeObserver(): void {
    this.resizeObserver = new ResizeObserver(entries => {
      for (const entry of entries) {
        const { width } = entry.contentRect;
        if (width > 0) {
          this.canvasWidth.set(Math.floor(width));
          this.generateWaveformData();
        }
      }
    });

    this.resizeObserver.observe(this.containerRef.nativeElement);
  }

  onCanvasClick(event: MouseEvent): void {
    const canvas = this.canvasRef.nativeElement;
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const percentage = x / canvas.width;
    const duration = this.audioDuration() || this.duration;
    const time = percentage * duration;
    
    this.timeUpdate.emit(time);
  }

  onCanvasMouseMove(event: MouseEvent): void {
    const canvas = this.canvasRef.nativeElement;
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const percentage = x / canvas.width;
    const duration = this.audioDuration() || this.duration;
    const time = percentage * duration;
    
    this.isHovering.set(true);
    this.hoverX.set(x);
    this.hoverTime.set(time);
  }

  onCanvasMouseLeave(): void {
    this.isHovering.set(false);
  }

  onSegmentOverlayClick(segment: TranscriptionSegment, event: MouseEvent): void {
    event.stopPropagation();
    this.activeSegment.set(segment);
    this.segmentClick.emit(segment);
    this.timeUpdate.emit(segment.start_time);
  }

  getSegmentPosition(segment: TranscriptionSegment): { start: number; width: number } {
    const duration = this.audioDuration() || this.duration;
    if (duration === 0) return { start: 0, width: 0 };
    
    const start = (segment.start_time / duration) * 100;
    const width = ((segment.end_time - segment.start_time) / duration) * 100;
    return { start, width };
  }

  isSegmentActive(segment: TranscriptionSegment): boolean {
    return this.currentTime >= segment.start_time && this.currentTime <= segment.end_time;
  }

  getSegmentTooltip(segment: TranscriptionSegment): string {
    const start = this.formatTime(segment.start_time);
    const end = this.formatTime(segment.end_time);
    return `${start} - ${end}`;
  }

  formatTime(seconds: number): string {
    if (!seconds || seconds < 0) return '0:00';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
      return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
  }

  // Public method to redraw waveform (can be called from parent)
  redraw(): void {
    this.drawWaveform();
  }

  // Public method to update duration (if not loading from audio)
  updateDuration(duration: number): void {
    this.audioDuration.set(duration);
    this.drawWaveform();
  }
}