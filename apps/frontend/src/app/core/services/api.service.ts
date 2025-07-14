import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpEvent, HttpParams, HttpHeaders } from '@angular/common/http';

import { Observable, throwError, firstValueFrom } from 'rxjs';
import { catchError, timeout, tap } from 'rxjs/operators';

import { environment } from '../../../environments/environment';
import { MessageService, MessageType } from './message.service';
import { StorageService } from './storage.service';

export interface ApiOptions {
  headers?: HttpHeaders | { [header: string]: string | string[] };
  params?: HttpParams | { [param: string]: string | number | boolean | ReadonlyArray<string | number | boolean> };
  timeout?: number;
  withCredentials?: boolean;
  showSuccessMessage?: boolean;  // Default: true
  showErrorMessage?: boolean;    // Default: true
  successMessage?: string;       // Custom success message
  silentRequest?: boolean;       // No messages at all (overrides all)
  responseType?: 'arraybuffer' | 'blob' | 'json' | 'text';
}

export interface UnifiedResponse<T = any> {
  success: boolean;
  message: string;
  message_type: MessageType;
  data?: T;
  error_code?: string;
  [key: string]: any;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly messageService = inject(MessageService);
  private readonly storage = inject(StorageService);
  
  private readonly baseUrl = environment.apiUrl;
  private readonly defaultTimeout = 30000; // 30 seconds

  /**
   * GET request with automatic message handling
   */
  get<T>(endpoint: string, options: ApiOptions = {}): Observable<T> {
    return this.request<T>('GET', endpoint, null, options);
  }

  /**
   * POST request with automatic message handling
   */
  post<T>(endpoint: string, data: any, options: ApiOptions = {}): Observable<T> {
    return this.request<T>('POST', endpoint, data, options);
  }

  /**
   * PUT request with automatic message handling
   */
  put<T>(endpoint: string, data: any, options: ApiOptions = {}): Observable<T> {
    return this.request<T>('PUT', endpoint, data, options);
  }

  /**
   * PATCH request with automatic message handling
   */
  patch<T>(endpoint: string, data: any, options: ApiOptions = {}): Observable<T> {
    return this.request<T>('PATCH', endpoint, data, options);
  }

  /**
   * DELETE request with automatic message handling
   */
  delete<T>(endpoint: string, options: ApiOptions = {}): Observable<T> {
    return this.request<T>('DELETE', endpoint, null, options);
  }

  /**
   * Async/await wrapper for any request with automatic message handling
   */
  async execute<T>(requestFn: () => Observable<T>, options: ApiOptions = {}): Promise<T> {
    try {
      const result = await firstValueFrom(requestFn().pipe(
        tap((response) => {
          // Auto-show success message if enabled (default: true)
          if (this.shouldShowSuccessMessage(options) && !options.silentRequest) {
            if (options.successMessage) {
              this.messageService.handleResponse({
                success: true,
                message: options.successMessage,
                message_type: 'success'
              });
            } else if (this.isUnifiedResponse(response)) {
              console.log('🎉 SUCCESS RESPONSE:', response); // Debug log
              this.messageService.showSuccess(response);
            }
          }
        }),
        catchError((error) => {
          // Auto-show error message (default: true)
          if (this.shouldShowErrorMessage(options) && !options.silentRequest) {
            this.messageService.showError(error);
          }
          throw error;
        })
      ));
      
      return result as T;
    } catch (error) {
      throw error;
    }
  }

  /**
   * File upload with progress tracking and automatic message handling
   */
  upload<T>(endpoint: string, formData: FormData, options: ApiOptions = {}): Observable<HttpEvent<T>> {
    const url = this.buildUrl(endpoint);
    
    // Build headers without Content-Type to let browser set it for FormData
    const headers = new HttpHeaders({
      'Accept': 'application/json',
      'Accept-Language': 'el'
    });
    
    // Add custom headers from options if provided
    let finalHeaders = headers;
    if (options.headers) {
      if (options.headers instanceof HttpHeaders) {
        const httpHeaders = options.headers as HttpHeaders;
        httpHeaders.keys().forEach(key => {
          const values = httpHeaders.getAll(key);
          if (values && key.toLowerCase() !== 'content-type') { // Don't override Content-Type for FormData
            finalHeaders = finalHeaders.set(key, values);
          }
        });
      } else {
        const headerObj = options.headers as { [header: string]: string | string[] };
        Object.keys(headerObj).forEach(key => {
          const value = headerObj[key];
          if (value !== null && value !== undefined && key.toLowerCase() !== 'content-type') {
            finalHeaders = finalHeaders.set(key, value as string | string[]);
          }
        });
      }
    }
    
    const requestOptions = {
      headers: finalHeaders,
      withCredentials: options.withCredentials || false,
      reportProgress: true,
      observe: 'events' as const
    };

    console.log('API Service: Making upload request to:', url);
    console.log('API Service: Request options:', requestOptions);
    console.log('API Service: FormData entries count:', Array.from(formData.entries()).length);

    return this.http.post<T>(url, formData, requestOptions).pipe(
      timeout(options.timeout || 300000), // 5 minutes for uploads
      tap((event: any) => {
        console.log('API Service: HTTP event received:', event.type, event);
        // Handle upload completion messages
        if (event.type === 4 && !options.silentRequest) { // HttpEventType.Response
          if (this.shouldShowSuccessMessage(options) && this.isUnifiedResponse(event.body)) {
            this.messageService.showSuccess(event.body);
          }
        }
      }),
      catchError((error) => {
        console.error('API Service: Upload error caught:', error);
        console.error('API Service: Error status:', error.status);
        console.error('API Service: Error name:', error.name);
        console.error('API Service: Error message:', error.message);
        return this.handleError(error, options);
      })
    );
  }

  /**
   * File download with automatic message handling
   */
  download(endpoint: string, options: ApiOptions = {}): Observable<Blob> {
    const url = this.buildUrl(endpoint);
    const requestOptions = {
      ...options,
      responseType: 'blob' as const
    };

    return this.http.get(url, requestOptions).pipe(
      timeout(options.timeout || this.defaultTimeout),
      catchError((error) => this.handleError(error, options))
    );
  }

  /**
   * Generic request method with automatic message handling
   */
  private request<T>(
    method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE',
    endpoint: string,
    data: any = null,
    options: ApiOptions = {}
  ): Observable<T> {
    const url = this.buildUrl(endpoint);
    const requestOptions: any = {
      headers: this.buildHeaders(options.headers),
      params: options.params,
      withCredentials: options.withCredentials || false
    };

    // Add responseType if specified
    if (options.responseType) {
      requestOptions.responseType = options.responseType;
    }

    let request$: Observable<T>;

    switch (method) {
      case 'GET':
        request$ = this.http.get(url, requestOptions) as Observable<T>;
        break;
      case 'POST':
        request$ = this.http.post(url, data, requestOptions) as Observable<T>;
        break;
      case 'PUT':
        request$ = this.http.put(url, data, requestOptions) as Observable<T>;
        break;
      case 'PATCH':
        request$ = this.http.patch(url, data, requestOptions) as Observable<T>;
        break;
      case 'DELETE':
        request$ = this.http.delete(url, requestOptions) as Observable<T>;
        break;
    }

    return request$.pipe(
      timeout(options.timeout || this.defaultTimeout),
      catchError((error) => this.handleError(error, options))
    );
  }

  /**
   * Handle HTTP errors - no automatic message handling here
   * Messages are handled by execute() method only
   */
  private handleError(error: any, options: ApiOptions = {}): Observable<never> {
    // No automatic message handling here to avoid duplicates
    // All message handling is done in execute() method
    return throwError(() => error);
  }

  /**
   * Determine if success message should be shown (default: true)
   */
  private shouldShowSuccessMessage(options: ApiOptions): boolean {
    return options.showSuccessMessage !== false;
  }

  /**
   * Determine if error message should be shown (default: true)
   */
  private shouldShowErrorMessage(options: ApiOptions): boolean {
    return options.showErrorMessage !== false;
  }

  /**
   * Get authenticated URL for direct use (for streaming, etc.)
   */
  getAuthenticatedUrl(endpoint: string): string {
    const url = this.buildUrl(endpoint);
    const token = this.storage.getItem<string>('token');
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}Authorization=Bearer ${token}`;
  }

  /**
   * Build full URL from endpoint
   */
  private buildUrl(endpoint: string): string {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
    return `${this.baseUrl}/${cleanEndpoint}`;
  }

  /**
   * Build HTTP headers
   */
  private buildHeaders(headers?: HttpHeaders | { [header: string]: string | string[] }): HttpHeaders {
    let httpHeaders = new HttpHeaders({
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Accept-Language': 'el'  // Force Greek language
    });

    if (headers) {
      if (headers instanceof HttpHeaders) {
        headers.keys().forEach(key => {
          const values = headers.getAll(key);
          if (values) {
            httpHeaders = httpHeaders.set(key, values);
          }
        });
      } else {
        Object.keys(headers).forEach(key => {
          const value = headers[key];
          if (value !== null && value !== undefined) {
            httpHeaders = httpHeaders.set(key, value as string | string[]);
          }
        });
      }
    }

    return httpHeaders;
  }

  /**
   * Check if response follows unified format
   */
  private isUnifiedResponse(response: any): response is UnifiedResponse {
    return response && 
           typeof response === 'object' && 
           'message' in response && 
           'message_type' in response;
  }

  /**
   * Build query parameters for pagination
   */
  buildPaginationParams(page: number = 1, perPage: number = 10, filters?: Record<string, any>): HttpParams {
    // Ensure valid page and perPage values
    const validPage = isNaN(page) || page < 1 ? 1 : page;
    const validPerPage = isNaN(perPage) || perPage < 1 ? 10 : perPage;
    
    let params = new HttpParams()
      .set('page', validPage.toString())
      .set('per_page', validPerPage.toString());

    if (filters) {
      Object.keys(filters).forEach(key => {
        const value = filters[key];
        if (value !== null && value !== undefined && value !== '') {
          params = params.set(key, value.toString());
        }
      });
    }

    return params;
  }

  /**
   * Check if endpoint requires authentication
   */
  isProtectedEndpoint(endpoint: string): boolean {
    const publicEndpoints = [
      '/auth/login',
      '/auth/register',
      '/auth/forgot-password',
      '/auth/reset-password',
      '/auth/verify-email',
    ];

    return !publicEndpoints.some(publicEndpoint => 
      endpoint.includes(publicEndpoint)
    );
  }

  /**
   * Get base URL for building full URLs
   */
  getBaseUrl(): string {
    return this.baseUrl;
  }

  /**
   * Get authenticated file URL with proper base URL
   */
  getAuthenticatedFileUrl(endpoint: string): string {
    return this.buildUrl(endpoint);
  }
}

/**
 * Utility function for one-liner API calls with automatic message handling
 */
export function apiCall<T>(
  apiService: ApiService,
  method: 'get' | 'post' | 'put' | 'patch' | 'delete',
  endpoint: string,
  data?: any,
  options: ApiOptions = {}
): Promise<T> {
  const requestFn = () => {
    switch (method) {
      case 'get':
        return apiService.get<T>(endpoint, options);
      case 'post':
        return apiService.post<T>(endpoint, data, options);
      case 'put':
        return apiService.put<T>(endpoint, data, options);
      case 'patch':
        return apiService.patch<T>(endpoint, data, options);
      case 'delete':
        return apiService.delete<T>(endpoint, options);
      default:
        throw new Error(`Unknown method: ${method}`);
    }
  };

  return apiService.execute(requestFn, options);
}