import { Injectable, signal, computed } from '@angular/core';
import { BehaviorSubject, Observable, interval, takeWhile, map } from 'rxjs';

export interface RecordingState {
  isRecording: boolean;
  isPaused: boolean;
  duration: number;
  visualizerData: number[];
  error: string | null;
}

export interface AudioRecordingResult {
  blob: Blob;
  url: string;
  duration: number;
  filename: string;
}

@Injectable({
  providedIn: 'root'
})
export class AudioRecordingService {
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];
  private stream: MediaStream | null = null;
  private startTime: number = 0;
  private pausedTime: number = 0;

  // Recording state signals
  private _isRecording = signal(false);
  private _isPaused = signal(false);
  private _duration = signal(0);
  private _visualizerData = signal<number[]>(Array(20).fill(20));
  private _error = signal<string | null>(null);
  private _isPermissionGranted = signal<boolean | null>(null);

  // Public readonly signals
  readonly isRecording = this._isRecording.asReadonly();
  readonly isPaused = this._isPaused.asReadonly();
  readonly duration = this._duration.asReadonly();
  readonly visualizerData = this._visualizerData.asReadonly();
  readonly error = this._error.asReadonly();
  readonly isPermissionGranted = this._isPermissionGranted.asReadonly();

  // Computed signals
  readonly formattedDuration = computed(() => this.formatDuration(this._duration()));
  readonly canRecord = computed(() => this._isPermissionGranted() === true && !this._isRecording());
  readonly canPause = computed(() => this._isRecording() && !this._isPaused());
  readonly canResume = computed(() => this._isRecording() && this._isPaused());
  readonly canStop = computed(() => this._isRecording());

  private recordingInterval: any;
  private analyser: AnalyserNode | null = null;
  private audioContext: AudioContext | null = null;

  constructor() {}

  async requestPermission(): Promise<boolean> {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
      this._isPermissionGranted.set(true);
      this._error.set(null);
      return true;
    } catch (error) {
      console.error('Microphone permission denied:', error);
      this._isPermissionGranted.set(false);
      this._error.set('Δεν παρασχέθηκε άδεια για πρόσβαση στο μικρόφωνο');
      return false;
    }
  }

  async startRecording(): Promise<boolean> {
    if (this._isRecording()) {
      console.warn('Recording already in progress');
      return false;
    }

    try {
      // Request permission first
      const hasPermission = await this.requestPermission();
      if (!hasPermission) {
        return false;
      }

      // Get audio stream
      this.stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      // Setup audio context for visualization
      this.setupAudioVisualization();

      // Setup MediaRecorder
      this.mediaRecorder = new MediaRecorder(this.stream, {
        mimeType: this.getSupportedMimeType()
      });

      this.audioChunks = [];
      this.startTime = Date.now();
      this.pausedTime = 0;

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      this.mediaRecorder.onstop = () => {
        this.stopVisualization();
        this.cleanupStream();
      };

      this.mediaRecorder.start();
      this._isRecording.set(true);
      this._isPaused.set(false);
      this._error.set(null);
      this._duration.set(0);

      // Start duration timer and visualization
      this.startTimer();

      return true;
    } catch (error) {
      console.error('Failed to start recording:', error);
      this._error.set('Αποτυχία έναρξης ηχογράφησης');
      this.cleanup();
      return false;
    }
  }

  pauseRecording(): boolean {
    if (!this._isRecording() || this._isPaused()) {
      return false;
    }

    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      this.mediaRecorder.pause();
      this._isPaused.set(true);
      this.pausedTime += Date.now() - this.startTime;
      this.stopTimer();
      return true;
    }
    return false;
  }

  resumeRecording(): boolean {
    if (!this._isRecording() || !this._isPaused()) {
      return false;
    }

    if (this.mediaRecorder && this.mediaRecorder.state === 'paused') {
      this.mediaRecorder.resume();
      this._isPaused.set(false);
      this.startTime = Date.now();
      this.startTimer();
      return true;
    }
    return false;
  }

  async stopRecording(): Promise<AudioRecordingResult | null> {
    if (!this._isRecording()) {
      return null;
    }

    return new Promise((resolve) => {
      if (!this.mediaRecorder) {
        resolve(null);
        return;
      }

      this.mediaRecorder.onstop = () => {
        const finalDuration = this.pausedTime + (Date.now() - this.startTime);
        const audioBlob = new Blob(this.audioChunks, { 
          type: this.getSupportedMimeType() 
        });
        const audioUrl = URL.createObjectURL(audioBlob);
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `recording-${timestamp}.webm`;

        const result: AudioRecordingResult = {
          blob: audioBlob,
          url: audioUrl,
          duration: Math.floor(finalDuration / 1000),
          filename
        };

        this.cleanup();
        resolve(result);
      };

      this.mediaRecorder.stop();
      this._isRecording.set(false);
      this._isPaused.set(false);
      this.stopTimer();
    });
  }

  cancelRecording(): void {
    if (this._isRecording() && this.mediaRecorder) {
      this.mediaRecorder.stop();
    }
    this.cleanup();
  }

  private setupAudioVisualization(): void {
    if (!this.stream) return;

    try {
      this.audioContext = new AudioContext();
      const source = this.audioContext.createMediaStreamSource(this.stream);
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 64;
      source.connect(this.analyser);

      this.updateVisualization();
    } catch (error) {
      console.warn('Audio visualization setup failed:', error);
    }
  }

  private updateVisualization(): void {
    if (!this.analyser || !this._isRecording() || this._isPaused()) {
      return;
    }

    const bufferLength = this.analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    this.analyser.getByteFrequencyData(dataArray);

    // Convert to visualization data (20 bars)
    const barCount = 20;
    const visualData: number[] = [];
    const step = Math.floor(bufferLength / barCount);

    for (let i = 0; i < barCount; i++) {
      let sum = 0;
      for (let j = 0; j < step; j++) {
        sum += dataArray[i * step + j];
      }
      const average = sum / step;
      const normalized = Math.max(20, (average / 255) * 100);
      visualData.push(normalized);
    }

    this._visualizerData.set(visualData);

    if (this._isRecording() && !this._isPaused()) {
      requestAnimationFrame(() => this.updateVisualization());
    }
  }

  private stopVisualization(): void {
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }
    this.analyser = null;
    this._visualizerData.set(Array(20).fill(20));
  }

  private startTimer(): void {
    this.recordingInterval = setInterval(() => {
      if (this._isRecording() && !this._isPaused()) {
        const currentTime = this.pausedTime + (Date.now() - this.startTime);
        this._duration.set(Math.floor(currentTime / 1000));
      }
    }, 100);
  }

  private stopTimer(): void {
    if (this.recordingInterval) {
      clearInterval(this.recordingInterval);
      this.recordingInterval = null;
    }
  }

  private cleanupStream(): void {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
  }

  private cleanup(): void {
    this._isRecording.set(false);
    this._isPaused.set(false);
    this._duration.set(0);
    this._error.set(null);
    
    this.stopTimer();
    this.stopVisualization();
    this.cleanupStream();
    
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.startTime = 0;
    this.pausedTime = 0;
  }

  private getSupportedMimeType(): string {
    const types = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/mp4',
      'audio/mp3'
    ];

    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        return type;
      }
    }
    return 'audio/webm';
  }

  private formatDuration(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  // Utility method to create File from AudioRecordingResult
  createFileFromRecording(recording: AudioRecordingResult): File {
    return new File([recording.blob], recording.filename, {
      type: recording.blob.type
    });
  }

  // Cleanup method for URLs
  revokeRecordingUrl(url: string): void {
    URL.revokeObjectURL(url);
  }
}