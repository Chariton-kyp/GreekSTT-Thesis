export interface User {
  id?: number; // Optional since backend may not send it for security
  email: string;
  email_display?: string; // Masked email for display
  username?: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone?: string;
  phone_display?: string; // Masked phone for display
  organization?: string;
  user_type: 'researcher' | 'student';
  research_limits: any;
  email_verified: boolean;
  is_active: boolean;
  is_deleted?: boolean;
  last_login?: string;
  created_at: string;
  updated_at: string;
}

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
}

export interface AuthResponse {
  user: User;
  access_token: string;
  refresh_token: string;
  token_type?: 'Bearer';
  expires_in?: number;
  message?: string;
}

export interface JWTClaims {
  sub: string; // User ID
  email: string;
  username: string;
  full_name: string;
  user_type: string;
  research_limits: {
    max_file_size: number;
    max_files_per_upload: number;
    monthly_minutes: number;
  };
  email_verified: boolean;
  login_method: string;
  login_time: string;
  iat: number;
  exp: number;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordReset {
  token: string;
  password: string;
  confirmPassword: string;
}

export interface UserSettingsData {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  organization: string;
  username: string;
  email_verified: boolean;
}
