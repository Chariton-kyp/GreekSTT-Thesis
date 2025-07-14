import { Injectable, inject } from '@angular/core';

import { JwtService } from './jwt.service';
import { StorageService } from './storage.service';

@Injectable({
  providedIn: 'root'
})
export class TokenService {
  private readonly storage = inject(StorageService);
  private readonly jwtService = inject(JwtService);

  /**
   * Get access token from storage
   */
  getAccessToken(): string | null {
    return this.storage.getItem('token');
  }

  /**
   * Get refresh token from storage
   */
  getRefreshToken(): string | null {
    return this.storage.getItem('refresh_token');
  }

  /**
   * Set tokens in storage
   */
  setTokens(accessToken: string, refreshToken: string): void {
    this.storage.setItem('token', accessToken);
    this.storage.setItem('refresh_token', refreshToken);
  }

  /**
   * Clear tokens from storage
   */
  clearTokens(): void {
    this.storage.removeItem('token');
    this.storage.removeItem('refresh_token');
  }

  /**
   * Check if access token is valid
   */
  isAccessTokenValid(): boolean {
    const token = this.getAccessToken();
    return token ? !this.jwtService.isTokenExpired(token) : false;
  }

  /**
   * Check if refresh token is valid
   */
  isRefreshTokenValid(): boolean {
    const token = this.getRefreshToken();
    return token ? !this.jwtService.isTokenExpired(token) : false;
  }

  /**
   * Check if we have valid tokens
   */
  hasValidTokens(): boolean {
    return this.isAccessTokenValid() && this.isRefreshTokenValid();
  }
}