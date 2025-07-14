// User Models
export interface User {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone?: string;
  organization?: string;
  user_type: string;
  email_verified: boolean;
  primary_email_verified: boolean;
  role?: string;
  last_login?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

// Authentication Models
export interface LoginCredentials {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
  organization?: string;
  terms_accepted: boolean;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user: User;
  message?: string;
  requires_verification?: boolean;
  sessions_terminated?: number;
}

export interface JWTClaims {
  sub: string; // user_id
  email: string;
  username: string;
  full_name: string;
  user_type: string;
  email_verified: boolean;
  exp: number;
  iat: number;
  jti: string;
}

// Audio Models
export interface AudioFile {
  id: number;
  original_filename: string;
  stored_filename: string;
  file_size: number;
  file_size_formatted: string;
  mime_type: string;
  duration_seconds?: number;
  duration_formatted?: string;
  sample_rate?: number;
  channels?: number;
  bitrate?: number;
  status: string;
  user_id: number;
  transcriptions_count: number;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

// Transcription Models
export interface Transcription {
  id: number;
  audio_file_id: number;
  user_id: number;
  text: string;
  language: string;
  template_id?: number;
  template_name?: string;
  structured_data?: any;
  status: string;
  started_at?: string;
  completed_at?: string;
  processing_time?: number;
  error_message?: string;
  duration_seconds?: number;
  duration_formatted?: string;
  word_count?: number;
  confidence_score?: number;
  model_used?: string;
  credits_used: number;
  audio_file?: {
    id: number;
    filename: string;
    duration?: number;
  };
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface TranscriptionSegment {
  id: number;
  start_time: number;
  end_time: number;
  text: string;
  confidence?: number;
  speaker?: string;
}

// Template Models
export interface Template {
  id: number;
  name: string;
  description?: string;
  sector: string;
  structure: any;
  example_output?: any;
  is_public: boolean;
  is_premium: boolean;
  usage_count: number;
  created_by_user_id?: number;
  creator_name?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

// API Response Models
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  errors?: Record<string, string[]>;
  timestamp?: string;
}

export interface PaginatedResponse<T = any> {
  data: T[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

// Error Models
export interface ApiError {
  message: string;
  error_code?: string;
  field?: string;
  details?: any;
}

// Session Models
export interface UserSession {
  id: string;
  user_id: number;
  device_info: {
    browser?: string;
    os?: string;
    device_type?: string;
    ip_address?: string;
    user_agent?: string;
  };
  created_at: string;
  last_activity: string;
  expires_at: string;
  is_current: boolean;
  trusted_device: boolean;
}