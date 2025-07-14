import { HttpInterceptorFn, HttpRequest, HttpHandlerFn, HttpEventType } from '@angular/common/http';
import { inject } from '@angular/core';

import { finalize, tap } from 'rxjs/operators';

import { LoadingService } from '../services/loading.service';

export const loadingInterceptor: HttpInterceptorFn = (req: HttpRequest<unknown>, next: HttpHandlerFn) => {
  const loadingService = inject(LoadingService);
  
  // Skip loading indicator for certain requests
  if (shouldSkipLoading(req)) {
    return next(req);
  }
  
  // Generate a unique key for this request
  const requestKey = generateRequestKey(req);
  
  // Show loading
  loadingService.show(requestKey, getLoadingMessage(req));
  
  return next(req).pipe(
    tap(event => {
      // Handle upload progress
      if (event.type === HttpEventType.UploadProgress && event.total) {
        const progress = Math.round(100 * event.loaded / event.total);
        loadingService.updateProgress(requestKey, progress, 'Μεταφόρτωση...');
      }
      
      // Handle download progress
      if (event.type === HttpEventType.DownloadProgress && event.total) {
        const progress = Math.round(100 * event.loaded / event.total);
        loadingService.updateProgress(requestKey, progress, 'Λήψη...');
      }
    }),
    finalize(() => {
      // Hide loading when request completes (success or error)
      loadingService.hide(requestKey);
    })
  );
};

/**
 * Check if loading indicator should be skipped for this request
 */
function shouldSkipLoading(req: HttpRequest<unknown>): boolean {
  // Skip loading for specific endpoints
  const skipEndpoints = [
    '/auth/refresh', // Don't show loading for token refresh
    '/health',       // Don't show loading for health checks
    '/ping'          // Don't show loading for ping requests
  ];
  
  return skipEndpoints.some(endpoint => req.url.includes(endpoint)) ||
         req.headers.has('Skip-Loading'); // Allow explicit skip via header
}

/**
 * Generate a unique key for the request
 */
function generateRequestKey(req: HttpRequest<unknown>): string {
  // Use method + URL + timestamp to create unique key
  const timestamp = Date.now();
  const url = req.url.split('?')[0]; // Remove query params for key
  return `${req.method}_${url}_${timestamp}`;
}

/**
 * Get appropriate loading message based on request
 */
function getLoadingMessage(req: HttpRequest<unknown>): string {
  const url = req.url;
  const method = req.method;
  
  // Authentication requests
  if (url.includes('/auth/login')) {
    return 'Σύνδεση...';
  }
  if (url.includes('/auth/register')) {
    return 'Εγγραφή...';
  }
  if (url.includes('/auth/logout')) {
    return 'Αποσύνδεση...';
  }
  
  // File operations
  if (url.includes('/upload') || method === 'POST' && req.body instanceof FormData) {
    return 'Μεταφόρτωση αρχείου...';
  }
  if (url.includes('/download')) {
    return 'Λήψη αρχείου...';
  }
  
  // Transcription operations
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
  
  // User profile operations
  if (url.includes('/users/me')) {
    switch (method) {
      case 'PUT':
      case 'PATCH':
        return 'Ενημέρωση προφίλ...';
      default:
        return 'Φόρτωση προφίλ...';
    }
  }
  
  // Template operations
  if (url.includes('/templates')) {
    return 'Φόρτωση προτύπων...';
  }
  
  // Research operations
  if (url.includes('/research')) {
    return 'Φόρτωση στατιστικών...';
  }
  
  // Generic messages based on HTTP method
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