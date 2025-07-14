// API Configuration
export const API_ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    FORGOT_PASSWORD: '/auth/forgot-password',
    RESET_PASSWORD: '/auth/reset-password',
    VERIFY_EMAIL: '/auth/verify-email',
    RESEND_VERIFICATION: '/auth/resend-verification',
    RETRIEVE_TOKENS: '/auth/retrieve-tokens'
  },
  
  // Users
  USERS: {
    ME: '/users/me',
    UPDATE_PROFILE: '/users/me',
    CHANGE_PASSWORD: '/users/me/password',
    SESSIONS: '/users/me/sessions'
  },
  
  // Audio
  AUDIO: {
    UPLOAD: '/audio/upload',
    LIST: '/audio',
    GET: '/audio/:id',
    DELETE: '/audio/:id'
  },
  
  // Transcriptions
  TRANSCRIPTIONS: {
    CREATE: '/transcriptions',
    LIST: '/transcriptions',
    GET: '/transcriptions/:id',
    UPDATE: '/transcriptions/:id',
    DELETE: '/transcriptions/:id',
    DOWNLOAD: '/transcriptions/:id/download'
  },
  
  // Templates
  TEMPLATES: {
    LIST: '/templates',
    GET: '/templates/:id',
    CREATE: '/templates',
    UPDATE: '/templates/:id',
    DELETE: '/templates/:id',
    SECTORS: '/templates/sectors'
  },
  
  // Research
  RESEARCH: {
    INFO: '/research/info',
    USAGE: '/research/usage',
    PROFILE: '/research/profile'
  },
  
  // Health
  HEALTH: '/health'
} as const;

// Environment configurations
export interface Environment {
  production: boolean;
  api: {
    baseUrl: string;
    timeout: number;
  };
  features: {
    emailVerification: boolean;
    research: boolean;
    analytics: boolean;
  };
  storage: {
    tokenKey: string;
    refreshTokenKey: string;
    userKey: string;
  };
  security: {
    maxFileSize: number; // in MB
    allowedFileTypes: string[];
    sessionTimeout: number; // in minutes
  };
}

// Default environment configuration
export const DEFAULT_ENVIRONMENT: Environment = {
  production: false,
  api: {
    baseUrl: 'http://localhost:5001/api',
    timeout: 30000
  },
  features: {
    emailVerification: true,
    research: true, // Enabled for academic use
    analytics: false
  },
  storage: {
    tokenKey: 'vs_token',
    refreshTokenKey: 'vs_refresh_token',
    userKey: 'vs_user'
  },
  security: {
    maxFileSize: 500, // 500MB
    allowedFileTypes: ['wav', 'mp3', 'm4a', 'flac', 'ogg', 'wma', 'aac', 'opus', 'webm'],
    sessionTimeout: 60 // 1 hour
  }
};



// Template sectors
export const TEMPLATE_SECTORS = {
  MEDICAL: 'medical',
  LEGAL: 'legal',
  BUSINESS: 'business',
  ACADEMIC: 'academic',
  GENERAL: 'general'
} as const;

// Status constants
export const TRANSCRIPTION_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed'
} as const;

export const AUDIO_STATUS = {
  UPLOADED: 'uploaded',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed'
} as const;

// Error codes
export const ERROR_CODES = {
  // Authentication
  INVALID_CREDENTIALS: 'INVALID_CREDENTIALS',
  EMAIL_NOT_VERIFIED: 'EMAIL_NOT_VERIFIED',
  ACCOUNT_LOCKED: 'ACCOUNT_LOCKED',
  TOKEN_EXPIRED: 'TOKEN_EXPIRED',
  
  // Validation
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  DUPLICATE_EMAIL: 'DUPLICATE_EMAIL',
  DUPLICATE_USERNAME: 'DUPLICATE_USERNAME',
  
  // File upload
  FILE_TOO_LARGE: 'FILE_TOO_LARGE',
  INVALID_FILE_TYPE: 'INVALID_FILE_TYPE',
  UPLOAD_FAILED: 'UPLOAD_FAILED',
  
  
  // Server errors
  INTERNAL_ERROR: 'INTERNAL_ERROR',
  SERVICE_UNAVAILABLE: 'SERVICE_UNAVAILABLE',
  NETWORK_ERROR: 'NETWORK_ERROR'
} as const;

// Greek locale configuration
export const GREEK_LOCALE = {
  code: 'el-GR',
  name: 'Ελληνικά',
  rtl: false,
  dateFormat: 'DD/MM/YYYY',
  timeFormat: 'HH:mm',
  currency: 'EUR',
  numberFormat: {
    decimal: ',',
    thousands: '.'
  }
} as const;

// Validation rules
export const VALIDATION_RULES = {
  PASSWORD: {
    minLength: 8,
    maxLength: 128,
    requireUppercase: true,
    requireLowercase: true,
    requireNumbers: true,
    requireSpecialChars: false
  },
  USERNAME: {
    minLength: 3,
    maxLength: 30,
    allowedChars: /^[a-zA-Z0-9_-]+$/
  },
  EMAIL: {
    maxLength: 254,
    pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  },
  PHONE: {
    pattern: /^(\+30|0030)?[2-9]\d{8,9}$/
  },
  FILENAME: {
    maxLength: 255,
    disallowedChars: /[<>:"/\\|?*]/
  }
} as const;

// Cache configuration
export const CACHE_KEYS = {
  USER_PROFILE: 'user_profile',
  TRANSCRIPTIONS: 'transcriptions',
  TEMPLATES: 'templates',
  AUDIO_FILES: 'audio_files',
  RESEARCH_INFO: 'research_info'
} as const;

export const CACHE_DURATION = {
  SHORT: 5 * 60 * 1000, // 5 minutes
  MEDIUM: 15 * 60 * 1000, // 15 minutes
  LONG: 60 * 60 * 1000, // 1 hour
  VERY_LONG: 24 * 60 * 60 * 1000 // 24 hours
} as const;