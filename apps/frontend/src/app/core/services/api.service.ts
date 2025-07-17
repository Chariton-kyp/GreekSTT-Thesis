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
  showSuccessMessage?: boolean;
  showErrorMessage?: boolean;
  successMessage?: string;
  silentRequest?: boolean;
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
  private readonly defaultTimeout = 30000;

  get<T>(endpoint: string, options: ApiOptions = {}): Observable<T> {
    return this.request<T>('GET', endpoint, null, options);
  }

  post<T>(endpoint: string, data: any, options: ApiOptions = {}): Observable<T> {
    return this.request<T>('POST', endpoint, data, options);
  }

  put<T>(endpoint: string, data: any, options: ApiOptions = {}): Observable<T> {
    return this.request<T>('PUT', endpoint, data, options);
  }

  patch<T>(endpoint: string, data: any, options: ApiOptions = {}): Observable<T> {
    return this.request<T>('PATCH', endpoint, data, options);
  }

  delete<T>(endpoint: string, options: ApiOptions = {}): Observable<T> {
    return this.request<T>('DELETE', endpoint, null, options);
  }
  async execute<T>(requestFn: () => Observable<T>, options: ApiOptions = {}): Promise<T> {
    try {
      const result = await firstValueFrom(requestFn().pipe(
        tap((response) => {
          if (this.shouldShowSuccessMessage(options) && !options.silentRequest) {
            if (options.successMessage) {
              this.messageService.handleResponse({
                success: true,
                message: options.successMessage,
                message_type: 'success'
              });
            } else if (this.isUnifiedResponse(response)) {
              this.messageService.showSuccess(response);
            }
          }
        }),
        catchError((error) => {
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

  upload<T>(endpoint: string, formData: FormData, options: ApiOptions = {}): Observable<HttpEvent<T>> {
    const url = this.buildUrl(endpoint);
    
    const headers = new HttpHeaders({
      'Accept': 'application/json',
      'Accept-Language': 'el'
    });
    
    let finalHeaders = headers;
    if (options.headers) {
      if (options.headers instanceof HttpHeaders) {
        const httpHeaders = options.headers as HttpHeaders;
        httpHeaders.keys().forEach(key => {
          const values = httpHeaders.getAll(key);
          if (values && key.toLowerCase() !== 'content-type') {
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


    return this.http.post<T>(url, formData, requestOptions).pipe(
      timeout(options.timeout || 300000),
      tap((event: any) => {
        if (event.type === 4 && !options.silentRequest) {
          if (this.shouldShowSuccessMessage(options) && this.isUnifiedResponse(event.body)) {
            this.messageService.showSuccess(event.body);
          }
        }
      }),
      catchError((error) => {
        return this.handleError(error, options);
      })
    );
  }

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

  private handleError(error: any, options: ApiOptions = {}): Observable<never> {
    return throwError(() => error);
  }

  private shouldShowSuccessMessage(options: ApiOptions): boolean {
    return options.showSuccessMessage !== false;
  }

  private shouldShowErrorMessage(options: ApiOptions): boolean {
    return options.showErrorMessage !== false;
  }

  getAuthenticatedUrl(endpoint: string): string {
    const url = this.buildUrl(endpoint);
    const token = this.storage.getItem<string>('token');
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}Authorization=Bearer ${token}`;
  }

  private buildUrl(endpoint: string): string {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
    return `${this.baseUrl}/${cleanEndpoint}`;
  }

  private buildHeaders(headers?: HttpHeaders | { [header: string]: string | string[] }): HttpHeaders {
    let httpHeaders = new HttpHeaders({
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Accept-Language': 'el'
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

  private isUnifiedResponse(response: any): response is UnifiedResponse {
    return response && 
           typeof response === 'object' && 
           'message' in response && 
           'message_type' in response;
  }

  buildPaginationParams(page: number = 1, perPage: number = 10, filters?: Record<string, any>): HttpParams {
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

  getBaseUrl(): string {
    return this.baseUrl;
  }

  getAuthenticatedFileUrl(endpoint: string): string {
    return this.buildUrl(endpoint);
  }
}

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