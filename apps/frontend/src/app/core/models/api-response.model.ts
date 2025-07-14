export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  errors?: Record<string, string[]>;
  meta?: {
    page?: number;
    per_page?: number;
    total?: number;
    total_pages?: number;
  };
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ErrorResponse {
  error: string;
  message: string;
  statusCode: number;
  timestamp: string;
  path: string;
  details?: Record<string, any>;
}

export interface UploadResponse {
  success: boolean;
  message: string;
  message_type: string;
  file?: UploadedFile;
  audio_file?: UploadedFile;
  data?: {
    audio_file?: UploadedFile;
    file?: UploadedFile;
  };
}

export interface UploadedFile {
  id: string;
  originalFilename: string;
  storedFilename: string;
  filePath: string;
  fileSize: number;
  fileHash: string;
  mimeType: string;
  durationSeconds?: number;
  sampleRate?: number;
  channels?: number;
  bitrate?: number;
  status: 'uploaded' | 'processing' | 'completed' | 'failed';
  createdAt: Date;
}