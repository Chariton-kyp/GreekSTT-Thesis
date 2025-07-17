import { HttpInterceptorFn, HttpRequest, HttpHandlerFn, HttpEventType } from '@angular/common/http';
import { inject } from '@angular/core';

import { finalize, tap } from 'rxjs/operators';

import { LoadingService } from '../services/loading.service';

export const loadingInterceptor: HttpInterceptorFn = (req: HttpRequest<unknown>, next: HttpHandlerFn) => {
  const loadingService = inject(LoadingService);
  
  if (shouldSkipLoading(req)) {
    return next(req);
  }
  
  const requestKey = generateRequestKey(req);
  
  loadingService.show(requestKey, getLoadingMessage(req));
  
  return next(req).pipe(
    tap(event => {
      if (event.type === HttpEventType.UploadProgress && event.total) {
        const progress = Math.round(100 * event.loaded / event.total);
        loadingService.updateProgress(requestKey, progress, 'Μεταφόρτωση...');
      }
      
      if (event.type === HttpEventType.DownloadProgress && event.total) {
        const progress = Math.round(100 * event.loaded / event.total);
        loadingService.updateProgress(requestKey, progress, 'Λήψη...');
      }
    }),
    finalize(() => {
      loadingService.hide(requestKey);
    })
  );
};

function shouldSkipLoading(req: HttpRequest<unknown>): boolean {
  const skipEndpoints = [
    '/auth/refresh',
    '/health',
    '/ping'
  ];
  
  return skipEndpoints.some(endpoint => req.url.includes(endpoint)) ||
         req.headers.has('Skip-Loading');
}

function generateRequestKey(req: HttpRequest<unknown>): string {
  const timestamp = Date.now();
  const url = req.url.split('?')[0];
  return `${req.method}_${url}_${timestamp}`;
}

function getLoadingMessage(req: HttpRequest<unknown>): string {
  const url = req.url;
  const method = req.method;
  
  if (url.includes('/auth/login')) {
    return 'Σύνδεση...';
  }
  if (url.includes('/auth/register')) {
    return 'Εγγραφή...';
  }
  if (url.includes('/auth/logout')) {
    return 'Αποσύνδεση...';
  }
  
  if (url.includes('/upload') || method === 'POST' && req.body instanceof FormData) {
    return 'Μεταφόρτωση αρχείου...';
  }
  if (url.includes('/download')) {
    return 'Λήψη αρχείου...';
  }
  
  if (url.includes('/transcriptions')) {
    switch (method) {
      case 'POST':
        return 'Δημιουργία μεταγραφής...';
      case 'PUT':
      case 'PATCH':
        return 'Ενημέρωση μεταγραφής...';
      case 'DELETE':
        return 'Διαγραφή μεταγραφής...';
      default:
        return 'Φόρτωση μεταγραφών...';
    }
  }
  
  if (url.includes('/users/me')) {
    switch (method) {
      case 'PUT':
      case 'PATCH':
        return 'Ενημέρωση προφίλ...';
      default:
        return 'Φόρτωση προφίλ...';
    }
  }
  
  if (url.includes('/templates')) {
    return 'Φόρτωση προτύπων...';
  }
  
  if (url.includes('/research')) {
    return 'Φόρτωση στατιστικών...';
  }
  
  switch (method) {
    case 'POST':
      return 'Δημιουργία...';
    case 'PUT':
    case 'PATCH':
      return 'Ενημέρωση...';
    case 'DELETE':
      return 'Διαγραφή...';
    default:
      return 'Φόρτωση...';
  }
}