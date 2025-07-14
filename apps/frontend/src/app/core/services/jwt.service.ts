import { Injectable } from '@angular/core';

import { JWTClaims } from '../models/user.model';

@Injectable({
  providedIn: 'root'
})
export class JwtService {

  /**
   * Decode JWT token and extract claims
   */
  decodeToken(token: string): JWTClaims | null {
    try {
      const payload = token.split('.')[1];
      const decoded = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')));
      return decoded as JWTClaims;
    } catch (error) {
      console.warn('Failed to decode JWT token:', error);
      return null;
    }
  }

  /**
   * Check if token is expired
   */
  isTokenExpired(token: string): boolean {
    const claims = this.decodeToken(token);
    if (!claims) return true;
    
    const now = Date.now() / 1000;
    return claims.exp < now;
  }

  /**
   * Get token expiration time in milliseconds
   */
  getTokenExpiration(token: string): number | null {
    const claims = this.decodeToken(token);
    if (!claims) return null;
    
    return claims.exp * 1000;
  }

  /**
   * Get time until token refresh is needed (5 minutes before expiry)
   */
  getTimeUntilRefresh(token: string): number {
    const expiration = this.getTokenExpiration(token);
    if (!expiration) return 0;
    
    const refreshTime = expiration - (5 * 60 * 1000); // 5 minutes before expiry
    const now = Date.now();
    
    return Math.max(refreshTime - now, 0);
  }
}