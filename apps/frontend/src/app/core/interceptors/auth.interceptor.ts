import { HttpInterceptorFn, HttpRequest, HttpHandlerFn } from '@angular/common/http';
import { inject } from '@angular/core';

import { TokenService } from '../services/token.service';

export const authInterceptor: HttpInterceptorFn = (req: HttpRequest<unknown>, next: HttpHandlerFn) => {
  const tokenService = inject(TokenService);
  
  const isPublicEndpoint = isPublicUrl(req.url);
  
  if (!isPublicEndpoint) {
    let token: string | null = null;
    
    if (req.url.includes('/auth/refresh')) {
      token = tokenService.getRefreshToken();
    } else {
      token = tokenService.getAccessToken();
    }
    
    if (token) {
      const authReq = req.clone({
        headers: req.headers.set('Authorization', `Bearer ${token}`)
      });
      
      return next(authReq);
    }
  }
  
  return next(req);
};

function isPublicUrl(url: string): boolean {
  const publicEndpoints = [
    '/auth/login',
    '/auth/register',
    '/auth/forgot-password',
    '/auth/reset-password',
    '/auth/verify-email/',
  ];
  
  return publicEndpoints.some(endpoint => url.includes(endpoint));
}