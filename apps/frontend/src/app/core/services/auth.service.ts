import { Injectable, signal, computed, effect, inject } from '@angular/core';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';

import { firstValueFrom } from 'rxjs';

import { ApiService } from './api.service';
import { JwtService } from './jwt.service';
import { MessageService } from './message.service';
import { StorageService } from './storage.service';
import { environment } from '../../../environments/environment';
import { 
  User, 
  LoginCredentials, 
  RegisterData, 
  AuthResponse, 
  PasswordResetRequest, 
  PasswordReset,
  JWTClaims
} from '../models/user.model';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly api = inject(ApiService);
  private readonly storage = inject(StorageService);
  private readonly router = inject(Router);
  private readonly jwtService = inject(JwtService);
  private readonly messageService = inject(MessageService);

  private _currentUser = signal<User | null>(null);
  private _currentClaims = signal<JWTClaims | null>(null);
  private _isLoading = signal<boolean>(false);
  private _error = signal<string | null>(null);
  private _isInitialized = signal<boolean>(false);

  readonly currentUser = this._currentUser.asReadonly();
  readonly currentClaims = this._currentClaims.asReadonly();
  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();
  readonly isInitialized = this._isInitialized.asReadonly();

  readonly isAuthenticated = computed(() => {
    return !!this.currentClaims() || !!this.currentUser();
  });
  readonly isEmailVerified = computed(() => {
    const claims = this.currentClaims();
    if (claims) {
      return claims.email_verified || false;
    }
    return this.currentUser()?.email_verified || false;
  });
  readonly fullName = computed(() => {
    const claims = this.currentClaims();
    if (claims?.full_name) return claims.full_name;
    
    const user = this.currentUser();
    return user ? `${user.first_name} ${user.last_name}`.trim() : '';
  });
  readonly initials = computed(() => {
    const fullName = this.fullName();
    if (!fullName) return '';
    
    const parts = fullName.split(' ');
    return `${parts[0]?.[0] || ''}${parts[parts.length - 1]?.[0] || ''}`.toUpperCase();
  });

  private tokenRefreshTimer?: any;
  
  private _emailVerificationUpdated = new Subject<boolean>();
  readonly emailVerificationUpdated$ = this._emailVerificationUpdated.asObservable();

  constructor() {
    this.initializeAuth();

    effect(() => {
      if (this.isAuthenticated()) {
        this.scheduleTokenRefresh();
      } else {
        this.clearTokenRefreshTimer();
      }
    });
  }

  private async initializeAuth(): Promise<void> {
    if (!environment.production) {
    }
    
    const token = this.storage.getItem<string>('token');
    const refreshToken = this.storage.getItem<string>('refresh_token');

    if (!environment.production) {
    }

    if (token) {
      try {
        const claims = this.jwtService.decodeToken(token);
        if (claims && !this.jwtService.isTokenExpired(token)) {
          this._currentClaims.set(claims);
          
          if (!environment.production) {
          }
          try {
            await this.getCurrentUser();
          } catch (error) {
            if (!environment.production) {
            }
            // Keep JWT claims even if getCurrentUser fails - allows unverified users to stay authenticated
          }
        } else if (refreshToken) {
          if (!environment.production) {
          }
          
          await this.refreshToken();
        } else {
          if (!environment.production) {
          }
          
          this.clearAuthStorage();
        }
      } catch (error) {
        if (!environment.production) {
        }
        
        // Token is invalid, clear storage
        this.clearAuthStorage();
      }
    } else {
      if (!environment.production) {
      }
    }

    this._isInitialized.set(true);
    
    if (!environment.production) {
    }
  }

  async login(credentials: LoginCredentials): Promise<void> {
    this._isLoading.set(true);
    this._error.set(null);

    if (!environment.production) {
    }

    try {
      const response = await this.api.execute(
        () => this.api.post<AuthResponse>('/auth/login', credentials)
      );

      if (!environment.production) {
      }

      this.handleAuthResponse(response);
      
      if (!environment.production) {
      }
    } catch (error: any) {
      if (!environment.production) {
      }
      
      this._error.set(this.getErrorMessage(error));
      throw error;
    } finally {
      this._isLoading.set(false);
    }
  }

  async register(userData: RegisterData): Promise<{ requiresVerification: boolean; user?: any }> {
    this._isLoading.set(true);
    this._error.set(null);

    try {
      const response = await this.api.execute(
        () => this.api.post<any>('/auth/register', userData)
      );

      if (response.requires_verification) {
        this.handleAuthResponse(response);
        return { requiresVerification: true, user: response.user };
      } else {
        this.handleAuthResponse(response);
        return { requiresVerification: false, user: response.user };
      }
    } catch (error: any) {
      this._error.set(this.getErrorMessage(error));
      throw error;
    } finally {
      this._isLoading.set(false);
    }
  }

  async logout(): Promise<void> {
    if (this._isLoading()) {
      return;
    }

    this._isLoading.set(true);

    if (!environment.production) {
    }

    try {
      const token = this.storage.getItem<string>('token');
      if (token && !this.jwtService.isTokenExpired(token)) {
        await this.api.execute(
          () => this.api.post('/auth/logout', {})
        );
        
        if (!environment.production) {
        }
      } else {
        if (!environment.production) {
        }
      }
    } catch (error) {
      if (!environment.production) {
      }
    }

    this.clearAuthStorage();
    this._currentUser.set(null);
    this._isLoading.set(false);
    
    if (!environment.production) {
    }
    
    await this.router.navigate(['/']);
  }

  /**
   * Refresh access token
   */
  async refreshToken(): Promise<void> {
    const refreshToken = this.storage.getItem<string>('refresh_token');
    
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      // The refresh endpoint expects the refresh token in Authorization header
      // The auth interceptor will handle this automatically for /auth/refresh
      const response = await this.api.execute(
        () => this.api.post<AuthResponse>('/auth/refresh', {}),
        { silentRequest: true }
      );

      this.handleAuthResponse(response);
    } catch (error) {
      // Refresh failed, logout user
      await this.logout();
      throw error;
    }
  }

  /**
   * Request password reset
   */
  async forgotPassword(email: string): Promise<void> {
    this._isLoading.set(true);
    this._error.set(null);

    try {
      await this.api.execute(
        () => this.api.post('/auth/forgot-password', { email })
      );
    } catch (error: any) {
      this._error.set(this.getErrorMessage(error));
      throw error;
    } finally {
      this._isLoading.set(false);
    }
  }

  /**
   * Reset password with token
   */
  async resetPassword(token: string, password: string): Promise<void> {
    this._isLoading.set(true);
    this._error.set(null);

    try {
      await this.api.execute(
        () => this.api.post('/auth/reset-password', { token, password })
      );
    } catch (error: any) {
      this._error.set(this.getErrorMessage(error));
      throw error;
    } finally {
      this._isLoading.set(false);
    }
  }

  /**
   * Verify password reset code
   */
  async verifyPasswordResetCode(email: string, code: string): Promise<void> {
    this._isLoading.set(true);
    this._error.set(null);

    try {
      await this.api.execute(
        () => this.api.post('/auth/verify-reset-code', { email, code })
      );
    } catch (error: any) {
      this._error.set(this.getErrorMessage(error));
      throw error;
    } finally {
      this._isLoading.set(false);
    }
  }

  /**
   * Reset password with 6-digit code
   */
  async resetPasswordWithCode(email: string, code: string, password: string): Promise<{ autoLogin: boolean, redirectTo?: string }> {
    this._isLoading.set(true);
    this._error.set(null);

    try {
      const response = await this.api.execute(
        () => this.api.post<any>('/auth/reset-password-with-code', { email, code, password })
      );

      // Check if backend provided tokens for auto-login
      if (response.access_token && response.user) {
        // Auto-login: handle auth response to store tokens and set user
        this.handleAuthResponse(response);
        
        if (!environment.production) {
        }
        
        return { 
          autoLogin: true, 
          redirectTo: response.redirect_to || '/app/dashboard' 
        };
      } else {
        // Fallback: no auto-login, redirect to login
        return { 
          autoLogin: false, 
          redirectTo: '/auth/login' 
        };
      }
    } catch (error: any) {
      this._error.set(this.getErrorMessage(error));
      throw error;
    } finally {
      this._isLoading.set(false);
    }
  }

  /**
   * Verify email with token
   */
  async verifyEmail(token: string): Promise<void> {
    this._isLoading.set(true);
    this._error.set(null);

    try {
      await this.api.execute(
        () => this.api.get(`/auth/verify-email/${token}`)
      );
      
      // Refresh user data to update verification status
      await this.getCurrentUser();
    } catch (error: any) {
      this._error.set(this.getErrorMessage(error));
      throw error;
    } finally {
      this._isLoading.set(false);
    }
  }

  /**
   * Verify email with 6-digit code
   */
  async verifyEmailWithCode(code: string): Promise<void> {
    this._isLoading.set(true);
    this._error.set(null);

    try {
      // Backend uses JWT token to identify user, only code is needed
      const response = await this.api.execute(
        () => this.api.post('/auth/verify-email-code', { code })
      );
      
      // Handle new tokens if provided (for updated email_verified status)
      const responseData = response as any;
      if (responseData.access_token && responseData.refresh_token) {
        if (!environment.production) {
        }
        
        this.storage.setItem('token', responseData.access_token);
        this.storage.setItem('refresh_token', responseData.refresh_token);
        
        // Decode new JWT claims with updated email_verified status
        const claims = this.jwtService.decodeToken(responseData.access_token);
        if (claims) {
          this._currentClaims.set(claims);
          if (!environment.production) {
          }
        }
      }
      
      // Refresh user data to update verification status in UI
      await this.getCurrentUser();
      
      if (!environment.production) {
      }
      
      // Emit event for components that need to react to email verification changes
      this._emailVerificationUpdated.next(true);
    } catch (error: any) {
      this._error.set(this.getErrorMessage(error));
      throw error;
    } finally {
      this._isLoading.set(false);
    }
  }

  /**
   * Resend email verification code
   */
  async resendVerificationCode(): Promise<void> {
    this._isLoading.set(true);
    this._error.set(null);

    try {
      const response = await this.api.execute(
        () => this.api.post<{cooldown_remaining?: number}>('/auth/resend-verification', {})
      );
      
      // Handle server-side cooldown if returned
      if (response.cooldown_remaining && response.cooldown_remaining > 0) {
        throw {
          error: {
            message: `Παρακαλώ περιμένετε ${Math.ceil(response.cooldown_remaining / 60)} λεπτά πριν ζητήσετε νέο κωδικό`,
            error_code: 'RESEND_COOLDOWN_ACTIVE',
            cooldown_remaining: response.cooldown_remaining
          }
        };
      }
    } catch (error: any) {
      this._error.set(this.getErrorMessage(error));
      throw error;
    } finally {
      this._isLoading.set(false);
    }
  }

  /**
   * Get current user data (internal - silent)
   */
  async getCurrentUser(): Promise<void> {
    try {
      const response = await this.api.execute(
        () => this.api.get<any>('/users/me'),
        { silentRequest: true }
      );
      
      // Handle both old and new response formats
      const userData = response.user || response;
      this._currentUser.set(userData);
    } catch (error) {
      // Only clear user if we don't have valid JWT claims
      // This prevents clearing auth state when /users/me fails but token is valid
      if (!this.currentClaims()) {
        this._currentUser.set(null);
      }
      throw error;
    }
  }

  /**
   * Refresh user data (public - with loading state for UI)
   */
  async refreshUserData(): Promise<void> {
    if (!environment.production) {
    }
    
    try {
      const response = await this.api.execute(
        () => this.api.get<any>('/users/me'),
        { showSuccessMessage: false }
      );
      
      // Handle both old and new response formats
      const userData = response.user || response;
      this._currentUser.set(userData);
      
      if (!environment.production) {
      }
    } catch (error) {
      if (!environment.production) {
      }
      // Only clear user if we don't have valid JWT claims
      if (!this.currentClaims()) {
        this._currentUser.set(null);
      }
      throw error;
    }
  }

  /**
   * Update user profile
   */
  async updateProfile(userData: Partial<User>): Promise<void> {
    this._isLoading.set(true);
    this._error.set(null);

    try {
      const response = await this.api.execute(
        () => this.api.put<any>('/users/profile', userData)
      );
      
      // Handle response format from backend
      const updatedUser = response.user || response;
      this._currentUser.set(updatedUser);
    } catch (error: any) {
      this._error.set(this.getErrorMessage(error));
      throw error;
    } finally {
      this._isLoading.set(false);
    }
  }

  /**
   * Change user password
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    this._isLoading.set(true);
    this._error.set(null);

    try {
      await this.api.execute(
        () => this.api.post('/users/change-password', {
          current_password: currentPassword,
          new_password: newPassword
        })
      );
    } catch (error: any) {
      this._error.set(this.getErrorMessage(error));
      throw error;
    } finally {
      this._isLoading.set(false);
    }
  }

  /**
   * Clear authentication error
   */
  clearError(): void {
    this._error.set(null);
  }

  /**
   * Get current access token
   */
  getAccessToken(): string | null {
    return this.storage.getItem<string>('token');
  }

  /**
   * Get the stored refresh token
   */
  getRefreshToken(): string | null {
    return this.storage.getItem<string>('refresh_token');
  }

  /**
   * Handle successful authentication response
   */
  private handleAuthResponse(response: AuthResponse): void {
    this._currentUser.set(response.user);
    this.storage.setItem('token', response.access_token);
    
    // Debug logging for refresh token
    if (!environment.production) {
    }
    
    // Check if refresh_token exists in response
    if (!response.refresh_token) {
    }
    
    this.storage.setItem('refresh_token', response.refresh_token);
    
    // Decode and store JWT claims for fast access
    const claims = this.jwtService.decodeToken(response.access_token);
    if (claims) {
      this._currentClaims.set(claims);
    }
    
    // Store token expiration time (prefer JWT exp claim if available)
    const expiresAt = claims?.exp 
      ? new Date(claims.exp * 1000)
      : new Date(Date.now() + ((response.expires_in || 3600) * 1000));
    
    if (!environment.production) {
    }
    
    this.storage.setItem('token_expires_at', expiresAt.toISOString());
  }

  /**
   * Clear authentication storage
   */
  private clearAuthStorage(): void {
    this.storage.removeItem('token');
    this.storage.removeItem('refresh_token');
    this.storage.removeItem('token_expires_at');
    this._currentClaims.set(null);
    this.clearTokenRefreshTimer();
  }

  /**
   * Schedule token refresh before expiration
   */
  private scheduleTokenRefresh(): void {
    this.clearTokenRefreshTimer();

    const expiresAt = this.storage.getItem<string>('token_expires_at');
    if (!expiresAt) return;

    const expirationTime = new Date(expiresAt).getTime();
    const now = Date.now();
    const timeUntilExpiry = expirationTime - now;
    
    // Refresh 5 minutes before expiration
    const refreshTime = Math.max(timeUntilExpiry - (5 * 60 * 1000), 0);

    if (!environment.production) {
    }

    if (refreshTime > 0) {
      this.tokenRefreshTimer = setTimeout(async () => {
        try {
          await this.refreshToken();
        } catch (error) {
        }
      }, refreshTime);
    }
  }

  /**
   * Clear token refresh timer
   */
  private clearTokenRefreshTimer(): void {
    if (this.tokenRefreshTimer) {
      clearTimeout(this.tokenRefreshTimer);
      this.tokenRefreshTimer = undefined;
    }
  }

  /**
   * Update current user data
   */
  updateCurrentUser(user: User): void {
    this._currentUser.set(user);
  }

  /**
   * Check if user can access features (simplified for thesis - only email verification matters)
   */
  canAccessFeatures(): boolean {
    return this.isAuthenticated() && this.isEmailVerified();
  }

  /**
   * Extract error message from error object
   */
  private getErrorMessage(error: any): string {
    return this.messageService.extractMessage(error).message;
  }
}