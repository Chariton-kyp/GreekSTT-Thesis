import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ApiService } from '../../../core/services/api.service';
import { ApiPatternsService } from '../../../core/services/api-patterns.service';
import { environment } from '../../../../environments/environment';

interface ExportOptions {
  dataType: string;
  format: string;
  dateRange: Date[];
  filters: any;
  includeMetadata: boolean;
  anonymizeData: boolean;
  compressionEnabled: boolean;
}

interface ExportEstimate {
  recordCount: number;
  estimatedSize: number;
  processingTime: number;
}

export type ExportFormat = 'txt' | 'srt' | 'docx';

@Injectable({
  providedIn: 'root'
})
export class ExportService {
  private readonly http = inject(HttpClient);
  private readonly api = inject(ApiService);
  private readonly apiPatterns = inject(ApiPatternsService);
  private readonly baseUrl = `/export`;

  /**
   * Export dashboard statistics in various formats
   */
  async exportDashboardStatistics(format: ExportFormat): Promise<Blob> {
    const response = await this.http.get(
      `${environment.apiUrl}${this.baseUrl}/dashboard-stats.${format}`,
      {
        responseType: 'blob',
        headers: {
          'Accept': this.getMimeType(format)
        }
      }
    ).toPromise();
    
    return response!;
  }

  /**
   * Export transcription data
   */
  async exportTranscriptionData(params: {
    format: ExportFormat;
    dateRange?: Date[];
    models?: string[];
    includeAudio?: boolean;
  }): Promise<Blob> {
    const queryParams: any = {
      format: params.format
    };

    if (params.dateRange) {
      queryParams.start_date = params.dateRange[0].toISOString();
      queryParams.end_date = params.dateRange[1].toISOString();
    }

    if (params.models) {
      queryParams.models = params.models.join(',');
    }

    if (params.includeAudio !== undefined) {
      queryParams.include_audio = params.includeAudio;
    }

    const response = await this.http.get(
      `${environment.apiUrl}${this.baseUrl}/transcriptions`,
      {
        params: queryParams,
        responseType: 'blob'
      }
    ).toPromise();

    return response!;
  }

  /**
   * Export model comparison results
   */
  async exportModelComparison(comparisonId: string, format: ExportFormat): Promise<Blob> {
    const response = await this.http.get(
      `${environment.apiUrl}${this.baseUrl}/comparisons/${comparisonId}.${format}`,
      {
        responseType: 'blob'
      }
    ).toPromise();

    return response!;
  }



  /**
   * Export data based on options
   */
  async exportData(options: ExportOptions): Promise<Blob> {
    const payload = {
      data_type: options.dataType,
      format: options.format,
      start_date: options.dateRange[0].toISOString(),
      end_date: options.dateRange[1].toISOString(),
      filters: options.filters,
      include_metadata: options.includeMetadata,
      anonymize_data: options.anonymizeData,
      compression_enabled: options.compressionEnabled
    };

    const response = await this.http.post(
      `${environment.apiUrl}${this.baseUrl}/data`,
      payload,
      {
        responseType: 'blob'
      }
    ).toPromise();

    return response!;
  }

  /**
   * Estimate export size
   */
  async estimateExportSize(options: ExportOptions): Promise<ExportEstimate> {
    const payload = {
      data_type: options.dataType,
      format: options.format,
      start_date: options.dateRange[0].toISOString(),
      end_date: options.dateRange[1].toISOString(),
      filters: options.filters
    };

    const result = await this.apiPatterns.create<ExportEstimate>(`${this.baseUrl}/estimate`, payload).toPromise();
    if (!result) {
      throw new Error('Failed to get export estimate');
    }
    return result;
  }

  /**
   * Get recent exports
   */
  async getRecentExports(limit: number = 10): Promise<any[]> {
    const result = await this.apiPatterns.read<any[]>(`${this.baseUrl}/recent`, { params: { limit: limit.toString() } }).toPromise();
    return result || [];
  }

  /**
   * Download existing export
   */
  async downloadExistingExport(exportId: string): Promise<Blob> {
    const response = await this.http.get(
      `${environment.apiUrl}${this.baseUrl}/download/${exportId}`,
      {
        responseType: 'blob'
      }
    ).toPromise();

    return response!;
  }

  /**
   * Download existing report
   */
  async downloadExistingReport(reportId: string): Promise<Blob> {
    const response = await this.http.get(
      `${environment.apiUrl}${this.baseUrl}/reports/download/${reportId}`,
      {
        responseType: 'blob'
      }
    ).toPromise();

    return response!;
  }

  /**
   * Export academic research data (simplified for thesis)
   */
  async exportResearchData(params: {
    includeTranscriptions: boolean;
    includeComparisons: boolean;
    format: ExportFormat;
    dateRange?: Date[];
  }): Promise<Blob> {
    const payload = {
      include_transcriptions: params.includeTranscriptions,
      include_comparisons: params.includeComparisons,
      format: params.format,
      start_date: params.dateRange?.[0].toISOString(),
      end_date: params.dateRange?.[1].toISOString()
    };

    const response = await this.http.post(
      `${environment.apiUrl}${this.baseUrl}/research-data`,
      payload,
      {
        responseType: 'blob'
      }
    ).toPromise();

    return response!;
  }

  /**
   * Download blob as file
   */
  downloadBlob(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    
    // Append to body, click, and remove
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Clean up
    window.URL.revokeObjectURL(url);
  }

  /**
   * Get MIME type for format
   */
  private getMimeType(format: ExportFormat): string {
    const mimeTypes: Record<ExportFormat, string> = {
      txt: 'text/plain',
      srt: 'application/x-subrip',
      docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    };

    return mimeTypes[format] || 'application/octet-stream';
  }

  /**
   * Generate filename with timestamp
   */
  generateFilename(prefix: string, format: ExportFormat): string {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    return `${prefix}_${timestamp}.${format}`;
  }

  /**
   * Check if export format is supported for data type
   */
  isFormatSupported(dataType: string, format: ExportFormat): boolean {
    const supportedFormats: Record<string, ExportFormat[]> = {
      transcriptions: ['txt', 'srt', 'docx'],
      comparisons: ['txt', 'docx'],
      research: ['txt', 'docx']
    };

    return supportedFormats[dataType]?.includes(format) || false;
  }

  /**
   * Create export preview
   */
  async createExportPreview(options: ExportOptions): Promise<any> {
    const payload = {
      data_type: options.dataType,
      format: options.format,
      filters: options.filters,
      limit: 10 // Preview first 10 records
    };

    return this.apiPatterns.create(`${this.baseUrl}/preview`, payload);
  }
}