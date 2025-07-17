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

      const silentEndpoints = [
        '/auth/verify-email-code',
        '/auth/verify-reset-code',
        '/auth/reset-password-with-code'
      ];
      
      const isSilentEndpoint = silentEndpoints.some(endpoint => req.url?.includes(endpoint));

      if (error.status === 401) {
        handleUnauthorized(authService, router, notificationService, req.url);
      }

      return throwError(() => error);
    })
  );
};


function handleUnauthorized(
  authService: AuthService, 
  router: Router, 
  notificationService: NotificationService,
  url?: string
): void {
  const noLogoutEndpoints = [
    '/auth/verify-email-code',
    '/auth/verify-reset-code',
    '/auth/reset-password-with-code',
    '/auth/login',
    '/auth/register',
    '/auth/logout',
    '/auth/refresh'
  ];
  
  const shouldNotLogout = noLogoutEndpoints.some(endpoint => url?.includes(endpoint));
  
  if (shouldNotLogout) {
    return;
  }
  
  authService.logout();
  notificationService.sessionExpired();
  router.navigate(['/auth/login']);
}

