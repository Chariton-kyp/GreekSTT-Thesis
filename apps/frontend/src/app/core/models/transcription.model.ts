export interface Transcription {
  id: string;
  audioFileId: string;
  userId: string;
  title: string;
  description?: string;
  text: string;
  language: string;
  academicNotes?: string;
  ai_model?: string;
  file_name?: string;
  file_size?: number;
  file_size_formatted?: string;
  duration?: number;
  duration_seconds: number;
  word_count: number;
  character_count?: number; // Backend calculated character count
  confidence_score: number;
  model_used: string;
  // structuredData removed for academic version
  status: TranscriptionStatus;
  startedAt?: Date | string;
  completedAt?: Date | string;
  errorMessage?: string;
  durationSeconds: number;
  wordCount: number;
  confidenceScore: number;
  modelUsed: string;
  processingMetadata?: Record<string, any>;
  metadata?: Record<string, any>;
  processing_time?: number;
  transcription_text?: string;
  creditsUsed: number;
  segments?: TranscriptionSegment[];
  
  // Dual Model Support Properties
  whisper_text?: string;
  wav2vec_text?: string;
  whisper_confidence?: number;
  wav2vec_confidence?: number;
  whisper_processing_time?: number;
  wav2vec_processing_time?: number;
  faster_model?: string; // 'whisper' or 'wav2vec2' based on processing time
  
  // WER/CER Evaluation Properties
  ground_truth_text?: string;
  ground_truth_word_count?: number; // Backend calculated ground truth word count
  whisper_wer?: number;
  whisper_cer?: number;
  wav2vec_wer?: number;
  wav2vec_cer?: number;
  evaluation_completed?: boolean;
  evaluation_date?: Date | string;
  evaluation_notes?: string;
  academic_accuracy_score?: number;
  best_performing_model?: string;
  has_evaluation?: boolean;
  whisper_accuracy?: number;
  wav2vec_accuracy?: number;
  
  audio_file?: {
    id: string;
    file_path: string;
    filename: string;
    file_size: number;
    file_size_formatted: string;
    mime_type: string;
    duration: number;
  };
  createdAt: Date | string;
  updatedAt: Date | string;
  created_at: Date | string;
  updated_at: Date | string;
}

export enum TranscriptionStatus {
  PENDING = 'pending',
  PROCESSING = 'processing', 
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export interface TranscriptionSegment {
  text: string;
  start: number;
  end: number;
  start_time: number;
  end_time: number;
  confidence?: number;
  speaker?: string;
}

export interface CreateTranscriptionRequest {
  audioFileId: string;
  language?: string;
  academicNotes?: string;
  options?: {
    includeTimestamps?: boolean;
    speakerDiarization?: boolean;
    customVocabulary?: string[];
  };
}

// TranscriptionTemplate interface removed - academic version has no templates

export interface ExportOptions {
  format: 'txt' | 'srt' | 'docx' | 'pdf';
  includeTimestamps?: boolean;
  includeConfidenceScores?: boolean;
  includeAcademicNotes?: boolean;
}

export interface TranscriptionRequest {
  title: string;
  description?: string;
  language: string;
  academicNotes?: string;
  ai_model: string;
  template_id?: number; // Optional for backward compatibility
}

export interface TranscriptionListResponse {
  data: {
    transcriptions: Transcription[];
    pagination: {
      total: number;
      page: number;
      per_page: number;
      pages: number;
      has_next: boolean;
      has_prev: boolean;
      current_page: number;
    };
    academic_mode: boolean;
  };
  message?: string;
  success?: boolean;
}

export interface CreateTranscriptionResponse {
  message: string;
  audio_file: any;
  transcription: Transcription;
  development_mode?: boolean;
}

export interface TranscriptionAPIResponse {
  success: boolean;
  message: string;
  data?: {
    text: string;
    processing_time: number;
    confidence_score: number;
    whisper?: any;
    wav2vec2?: any;
    comparison?: any;
  };
  error_code?: string;
}

export interface FileUploadResponse {
  message: string;
  audio_file: any;
}

export interface Usage {
  totalTranscriptions: number;
  monthlyUsage: number; // in seconds
  availableCredits: number;
  freeMinutesUsed: number;
  freeMinutesTotal: number;
  successRate: number;
}

export interface TranscriptionResult {
  id: string;
  text: string;
  status: TranscriptionStatus;
  confidence_score?: number;
  processing_time?: number;
  created_at: Date | string;
  updated_at: Date | string;
}