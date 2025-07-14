// Enhanced comparison result with model-specific analysis
export interface EnhancedComparisonResult {
  whisperResult?: {
    text: string;
    processing_time: number;
    word_error_rate?: number;
    confidence_score?: number;
  };
  wav2vecResult?: {
    text: string;
    processing_time: number;
    word_error_rate?: number;
    confidence_score?: number;
  };
  comparisonMetrics?: {
    overall_accuracy: number;
    whisper_accuracy: number;
    wav2vec_accuracy: number;
    preferred_model: 'whisper' | 'wav2vec2';
    processing_time_comparison: number;
  };
  metadata?: {
    audio_duration: number;
    file_size: number;
    language: string;
    timestamp: string;
  };
}

// Model performance for analytics
export interface ModelPerformance {
  modelName: string;
  totalTranscriptions: number;
  avgAccuracy: number;
  avgWER: number;
  avgProcessingTime: number;
  usagePercentage: number;
}

// Analytics data structure
export interface AnalyticsData {
  performanceData: ModelPerformance[];
  dateRange: [string, string];
  totalTranscriptions: number;
  avgOverallAccuracy: number;
  mostUsedModel: string;
}