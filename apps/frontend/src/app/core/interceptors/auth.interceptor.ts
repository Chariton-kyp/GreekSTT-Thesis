import { HttpInterceptorFn, HttpRequest, HttpHandlerFn } from '@angular/common/http';
import { inject } from '@angular/core';

import { TokenService } from '../services/token.service';

export const authInterceptor: HttpInterceptorFn = (req: HttpRequest<unknown>, next: HttpHandlerFn) => {
  const tokenService = inject(TokenService);
  
  // Don't add token to public endpoints
  const isPublicEndpoint = isPublicUrl(req.url);
  
  if (!isPublicEndpoint) {
    let token: string | null = null;
    
    // Use refresh token for refresh endpoint, access token for everything else
    if (req.url.includes('/auth/refresh')) {
      token = tokenService.getRefreshToken();
    } else {
      token = tokenService.getAccessToken();
    }
    
    if (token) {
      // Clone the request and add the authorization header
      const authReq = req.clone({
        headers: req.headers.set('Authorization', `Bearer ${token}`)
      });
      
      return next(authReq);
    }
  }
  
  return next(req);
};

/**
 * Check if the URL is a public endpoint that doesn't require authentication
 */
function isPublicUrl(url: string): boolean {
  const publicEndpoints = [
    '/auth/login',
    '/auth/register',
    '/auth/forgot-password',
    '/auth/reset-password',
    '/auth/verify-email/', // Only legacy token-based verification (with /{token})
    // Note: /auth/refresh is NOT public - it needs the refresh token in Authorization header
    // Note: /auth/verify-email-code is NOT public - it needs session authentication
    // Note: /auth/resend-verification is NOT public - it needs session authentication
  ];
  
  return publicEndpoints.some(endpoint => url.includes(endpoint));
}