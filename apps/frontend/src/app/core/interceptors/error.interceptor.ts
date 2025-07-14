import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';

import { catchError, throwError } from 'rxjs';

import { AuthService } from '../services/auth.service';
import { NotificationService } from '../services/notification.service';
import { MessageService } from '../services/message.service';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const notificationService = inject(NotificationService);
  const messageService = inject(MessageService);
  const router = inject(Router);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      console.error('HTTP Error:', error);

      // Define endpoints that should NOT show automatic error notifications
      // These endpoints handle their own error display
      const silentEndpoints = [
        '/auth/verify-email-code',
        '/auth/verify-reset-code',
        '/auth/reset-password-with-code'
      ];
      
      const isSilentEndpoint = silentEndpoints.some(endpoint => req.url?.includes(endpoint));

      // Handle authentication errors first (401)
      if (error.status === 401) {
        handleUnauthorized(authService, router, notificationService, req.url);
      }
      // API errors are now handled by ApiService automatically
      // No longer show messages here to avoid duplicates

      return throwError(() => error);
    })
  );
};


/**
 * Handle 401 Unauthorized errors
 */
function handleUnauthorized(
  authService: AuthService, 
  router: Router, 
  notificationService: NotificationService,
  url?: string
): void {
  // Endpoints that should not trigger automatic logout on 401
  // These endpoints may return 401 for validation errors, not auth errors
  const noLogoutEndpoints = [
    '/auth/verify-email-code',
    '/auth/verify-reset-code',
    '/auth/reset-password-with-code',
    '/auth/login',
    '/auth/register',
    '/auth/logout',  // IMPORTANT: Prevent infinite loop on logout failures
    '/auth/refresh'  // IMPORTANT: Refresh failures should not trigger logout loop
  ];
  
  // Check if this 401 is from an endpoint that shouldn't trigger logout
  const shouldNotLogout = noLogoutEndpoints.some(endpoint => url?.includes(endpoint));
  
  if (shouldNotLogout) {
    // Don't logout, just let the component handle the error
    return;
  }
  
  // Clear auth state and redirect to login for genuine auth errors
  authService.logout();
  notificationService.sessionExpired();
  router.navigate(['/auth/login']);
}

