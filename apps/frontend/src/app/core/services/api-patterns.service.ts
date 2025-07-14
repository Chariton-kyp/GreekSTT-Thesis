import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService, ApiOptions } from './api.service';
import { HttpParams } from '@angular/common/http';

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface DashboardStats {
  totalTranscriptions: number;
  totalDuration: number;
  averageAccuracy: number;
  modelUsage: ModelUsage[];
  recentActivity: TranscriptionActivity[];
  performanceMetrics: PerformanceMetrics;
}

export interface ModelUsage {
  model: string;
  count: number;
  percentage: number;
}

export interface TranscriptionActivity {
  id: string;
  timestamp: Date;
  model: string;
  duration: number;
  accuracy: number;
}

export interface PerformanceMetrics {
  processingSpeed: number;
  errorRate: number;
  uptime: number;
}

export interface AnalyticsData {
  dateRange: string;
  metrics: {
    [key: string]: number | string;
  };
}

@Injectable({
  providedIn: 'root'
})
export class ApiPatternsService {
  private readonly api = inject(ApiService);

  /**
   * Get dashboard statistics
   */
  getDashboardStats(): Observable<DashboardStats> {
    return this.api.get<DashboardStats>('/dashboard/stats');
  }

  /**
   * Get analytics data
   */
  getAnalytics(dateRange: string, metrics: string[]): Observable<AnalyticsData> {
    const params = new HttpParams()
      .set('date_range', dateRange)
      .set('metrics', metrics.join(','));
    
    return this.api.get<AnalyticsData>('/analytics', { params });
  }

  /**
   * Get paginated data with filters
   */
  getPaginatedData<T>(
    endpoint: string,
    page: number = 1,
    perPage: number = 10,
    filters?: Record<string, any>
  ): Observable<PaginatedResponse<T>> {
    const params = this.api.buildPaginationParams(page, perPage, filters);
    return this.api.get<PaginatedResponse<T>>(endpoint, { params });
  }

  /**
   * Execute async API call with automatic message handling
   */
  async execute<T>(
    method: 'get' | 'post' | 'put' | 'patch' | 'delete',
    endpoint: string,
    data?: any,
    options: ApiOptions = {}
  ): Promise<T> {
    const requestFn = () => {
      switch (method) {
        case 'get':
          return this.api.get<T>(endpoint, options);
        case 'post':
          return this.api.post<T>(endpoint, data, options);
        case 'put':
          return this.api.put<T>(endpoint, data, options);
        case 'patch':
          return this.api.patch<T>(endpoint, data, options);
        case 'delete':
          return this.api.delete<T>(endpoint, options);
      }
    };

    return this.api.execute(requestFn, options);
  }

  /**
   * Read data from an endpoint
   */
  read<T>(endpoint: string, options: ApiOptions = {}): Observable<T> {
    return this.api.get<T>(endpoint, options);
  }

  /**
   * Create new resource
   */
  create<T>(endpoint: string, data: any, options: ApiOptions = {}): Observable<T> {
    return this.api.post<T>(endpoint, data, options);
  }

  /**
   * Update existing resource
   */
  update<T>(endpoint: string, data: any, options: ApiOptions = {}): Observable<T> {
    return this.api.put<T>(endpoint, data, options);
  }

  /**
   * Delete resource
   */
  delete<T>(endpoint: string, options: ApiOptions = {}): Observable<T> {
    return this.api.delete<T>(endpoint, options);
  }

  /**
   * Patch resource
   */
  patch<T>(endpoint: string, data: any, options: ApiOptions = {}): Observable<T> {
    return this.api.patch<T>(endpoint, data, options);
  }

  /**
   * Upload file with progress tracking
   */
  uploadFile(endpoint: string, formData: FormData, options: ApiOptions = {}) {
    return this.api.upload(endpoint, formData, options);
  }

  /**
   * Download file
   */
  downloadFile(endpoint: string, options: ApiOptions = {}) {
    return this.api.download(endpoint, options);
  }
}