import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ApiService } from './api.service';

interface EnhancedComparisonResult {
  whisperResult?: {
    text: string;
    processing_time: number;
    word_error_rate?: number;
    confidence_score?: number;
  };
  wav2vecResult?: {
    text: string;
    processing_time: number;
    word_error_rate?: number;
    confidence_score?: number;
  };
  comparisonMetrics?: {
    accuracyDifference: number;
    speedRatio: number;
    preferredModel: string;
    academicInsights: string[];
  };
  metadata: {
    fileName: string;
    fileSize: number;
    duration: number;
    timestamp: string;
  };
}

@Injectable({
  providedIn: 'root'
})
export class ComparisonService {
  private readonly http = inject(HttpClient);
  private readonly apiService = inject(ApiService);
  private readonly apiUrl = `${environment.apiUrl}/api`;


  /**
   * Export comparison results as JSON
   */
  async exportAsJSON(results: EnhancedComparisonResult): Promise<Blob> {
    const exportData = {
      metadata: {
        ...results.metadata,
        exportFormat: 'json',
        exportTimestamp: new Date().toISOString(),
        platformVersion: '1.0.0',
        academicPurpose: 'GreekSTT Research Platform - Master\'s Thesis'
      },
      comparisonResults: {
        whisper: results.whisperResult,
        wav2vec2: results.wav2vecResult,
        metrics: results.comparisonMetrics,
      },
      academicNotes: {
        methodology: 'Side-by-side comparison of ASR models for Greek language',
        disclaimer: 'Results for academic research purposes only',
        citation: 'GreekSTT Research Platform (2024). Master\'s Thesis, University of Athens'
      }
    };

    const jsonString = JSON.stringify(exportData, null, 2);
    return new Blob([jsonString], { type: 'application/json' });
  }

  /**
   * Export comparison results as PDF
   */
  async exportAsPDF(results: EnhancedComparisonResult): Promise<Blob> {
    // In a real implementation, this would generate a proper PDF
    // For now, we'll create a comprehensive HTML report that can be printed to PDF
    const html = this.generatePDFHTML(results);
    
    // Convert HTML to PDF using backend service
    const response = await firstValueFrom(
      this.http.post(
        `${this.apiUrl}/export/comparison-pdf`,
        { html, results },
        { responseType: 'blob' }
      )
    );

    return response;
  }

  /**
   * Export comparison results as CSV
   */
  async exportAsCSV(results: EnhancedComparisonResult): Promise<Blob> {
    const csvRows: string[] = [];
    
    // Headers
    csvRows.push('Metric,Whisper,wav2vec2,Difference,Notes');
    
    // Processing Time
    csvRows.push(`Processing Time (s),${results.whisperResult?.processing_time || 'N/A'},${results.wav2vecResult?.processing_time || 'N/A'},${this.calculateTimeDifference(results)},Time in seconds`);
    
    // Word Error Rate
    csvRows.push(`Word Error Rate (%),${this.formatWER(results.whisperResult?.word_error_rate)},${this.formatWER(results.wav2vecResult?.word_error_rate)},${this.calculateWERDifference(results)},Lower is better`);
    
    // Confidence Score
    csvRows.push(`Confidence Score,${this.formatConfidence(results.whisperResult?.confidence_score)},${this.formatConfidence(results.wav2vecResult?.confidence_score)},${this.calculateConfidenceDifference(results)},Higher is better`);
    
    // Model Preference
    csvRows.push(`Preferred Model,${results.comparisonMetrics?.preferredModel === 'Whisper' ? 'YES' : 'NO'},${results.comparisonMetrics?.preferredModel === 'wav2vec2' ? 'YES' : 'NO'},-,Based on overall performance`);
    
    // Add metadata
    csvRows.push('');
    csvRows.push('File Information');
    csvRows.push(`File Name,${results.metadata.fileName}`);
    csvRows.push(`File Size,${this.formatFileSize(results.metadata.fileSize)}`);
    csvRows.push(`Analysis Date,${new Date(results.metadata.timestamp).toLocaleString('el-GR')}`);
    

    const csvContent = csvRows.join('\n');
    return new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
  }

  /**
   * Helper method to generate PDF HTML
   */
  private generatePDFHTML(results: EnhancedComparisonResult): string {
    return `
<!DOCTYPE html>
<html lang="el">
<head>
    <meta charset="UTF-8">
    <title>Αναφορά Σύγκρισης Μοντέλων ASR - GreekSTT Research Platform</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1, h2, h3 {
            color: #1a5490;
        }
        .header {
            text-align: center;
            border-bottom: 3px solid #1a5490;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .section {
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-top: 20px;
        }
        .metric-box {
            background: white;
            padding: 15px;
            border-radius: 5px;
            border: 1px solid #dee2e6;
        }
        .metric-label {
            font-weight: bold;
            color: #6c757d;
            font-size: 0.9em;
        }
        .metric-value {
            font-size: 1.5em;
            color: #1a5490;
            margin-top: 5px;
        }
        .comparison-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        .comparison-table th,
        .comparison-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        .comparison-table th {
            background: #1a5490;
            color: white;
        }
        .comparison-table tr:nth-child(even) {
            background: #f8f9fa;
        }
        .insight-box {
            background: #e3f2fd;
            border-left: 4px solid #1976d2;
            padding: 15px;
            margin: 10px 0;
        }
        .recommendation-box {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 10px 0;
        }
        .greek-note {
            background: #f3e5f5;
            border-left: 4px solid #7b1fa2;
            padding: 15px;
            margin: 10px 0;
        }
        .footer {
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
            color: #6c757d;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Αναφορά Σύγκρισης Μοντέλων ASR</h1>
        <p>GreekSTT Research Platform - Ακαδημαϊκή Έρευνα</p>
        <p>Ημερομηνία: ${new Date().toLocaleDateString('el-GR', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        })}</p>
    </div>

    <div class="section">
        <h2>Πληροφορίες Αρχείου</h2>
        <div class="metric-grid">
            <div class="metric-box">
                <div class="metric-label">Όνομα Αρχείου</div>
                <div class="metric-value">${results.metadata.fileName}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Μέγεθος</div>
                <div class="metric-value">${this.formatFileSize(results.metadata.fileSize)}</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Αποτελέσματα Σύγκρισης</h2>
        <table class="comparison-table">
            <thead>
                <tr>
                    <th>Μετρική</th>
                    <th>Whisper</th>
                    <th>wav2vec2</th>
                    <th>Διαφορά</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Χρόνος Επεξεργασίας</td>
                    <td>${results.whisperResult?.processing_time || 'N/A'}s</td>
                    <td>${results.wav2vecResult?.processing_time || 'N/A'}s</td>
                    <td>${this.calculateTimeDifference(results)}</td>
                </tr>
                <tr>
                    <td>Word Error Rate (WER)</td>
                    <td>${this.formatWER(results.whisperResult?.word_error_rate)}</td>
                    <td>${this.formatWER(results.wav2vecResult?.word_error_rate)}</td>
                    <td>${this.calculateWERDifference(results)}</td>
                </tr>
                <tr>
                    <td>Βαθμός Εμπιστοσύνης</td>
                    <td>${this.formatConfidence(results.whisperResult?.confidence_score)}</td>
                    <td>${this.formatConfidence(results.wav2vecResult?.confidence_score)}</td>
                    <td>${this.calculateConfidenceDifference(results)}</td>
                </tr>
            </tbody>
        </table>
        
        <div style="margin-top: 20px;">
            <strong>Προτεινόμενο Μοντέλο:</strong> 
            <span style="color: #28a745; font-size: 1.2em;">
                ${results.comparisonMetrics?.preferredModel || 'N/A'}
            </span>
        </div>
    </div>


    <div class="section">
        <h2>Ακαδημαϊκές Παρατηρήσεις</h2>
        ${results.comparisonMetrics?.academicInsights.map(insight => `
            <p>✓ ${insight}</p>
        `).join('') || '<p>Δεν υπάρχουν διαθέσιμες παρατηρήσεις</p>'}
    </div>

    <div class="footer">
        <p>GreekSTT Research Platform - Πλατφόρμα Ακαδημαϊκής Έρευνας</p>
        <p>Διπλωματική Εργασία - Πανεπιστήμιο Αθηνών 2024</p>
        <p style="font-style: italic;">
            Τα αποτελέσματα προορίζονται αποκλειστικά για ακαδημαϊκούς και ερευνητικούς σκοπούς
        </p>
    </div>
</body>
</html>
    `;
  }

  /**
   * Helper methods for formatting
   */
  private formatWER(wer?: number): string {
    if (wer === undefined || wer === null) return 'N/A';
    return `${(wer * 100).toFixed(1)}%`;
  }

  private formatConfidence(confidence?: number): string {
    if (confidence === undefined || confidence === null) return 'N/A';
    return `${(confidence * 100).toFixed(1)}%`;
  }

  private formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  private calculateTimeDifference(results: EnhancedComparisonResult): string {
    const whisperTime = results.whisperResult?.processing_time || 0;
    const wav2vecTime = results.wav2vecResult?.processing_time || 0;
    const diff = Math.abs(whisperTime - wav2vecTime);
    const percentage = wav2vecTime > 0 ? ((diff / wav2vecTime) * 100).toFixed(1) : '0';
    return whisperTime < wav2vecTime 
      ? `Whisper ${percentage}% ταχύτερο` 
      : `wav2vec2 ${percentage}% ταχύτερο`;
  }

  private calculateWERDifference(results: EnhancedComparisonResult): string {
    const whisperWER = results.whisperResult?.word_error_rate || 0;
    const wav2vecWER = results.wav2vecResult?.word_error_rate || 0;
    const diff = Math.abs(whisperWER - wav2vecWER) * 100;
    return whisperWER < wav2vecWER 
      ? `Whisper ${diff.toFixed(1)}% καλύτερο` 
      : `wav2vec2 ${diff.toFixed(1)}% καλύτερο`;
  }

  private calculateConfidenceDifference(results: EnhancedComparisonResult): string {
    const whisperConf = results.whisperResult?.confidence_score || 0;
    const wav2vecConf = results.wav2vecResult?.confidence_score || 0;
    const diff = Math.abs(whisperConf - wav2vecConf) * 100;
    return whisperConf > wav2vecConf 
      ? `Whisper ${diff.toFixed(1)}% υψηλότερο` 
      : `wav2vec2 ${diff.toFixed(1)}% υψηλότερο`;
  }

  /**
   * Get performance metrics for academic research
   */
  async getPerformanceMetrics(params?: {
    startDate?: Date;
    endDate?: Date;
    model?: string;
    language?: string;
  }): Promise<any> {
    const queryParams: Record<string, string> = {};
    if (params?.startDate) {
      queryParams['start_date'] = params.startDate.toISOString();
    }
    if (params?.endDate) {
      queryParams['end_date'] = params.endDate.toISOString();
    }
    if (params?.model) {
      queryParams['model'] = params.model;
    }
    if (params?.language) {
      queryParams['language'] = params.language;
    }

    const response = await firstValueFrom(
      this.http.get(`${this.apiUrl}/comparison/metrics`, { params: queryParams })
    );
    return response;
  }

  /**
   * Get detailed comparison analytics
   */
  async getDetailedAnalytics(comparisonId?: string): Promise<any> {
    const endpoint = comparisonId 
      ? `${this.apiUrl}/comparison/${comparisonId}/detailed`
      : `${this.apiUrl}/comparison/detailed`;
    
    const response = await firstValueFrom(
      this.http.get(endpoint)
    );
    return response;
  }

  /**
   * Get model agreement analysis
   */
  async getModelAgreementAnalysis(params?: {
    threshold?: number;
    startDate?: Date;
    endDate?: Date;
  }): Promise<any> {
    const queryParams: Record<string, string> = {};
    if (params?.threshold !== undefined) {
      queryParams['threshold'] = params.threshold.toString();
    }
    if (params?.startDate) {
      queryParams['start_date'] = params.startDate.toISOString();
    }
    if (params?.endDate) {
      queryParams['end_date'] = params.endDate.toISOString();
    }

    const response = await firstValueFrom(
      this.http.get(`${this.apiUrl}/comparison/agreement-analysis`, { params: queryParams })
    );
    return response;
  }

  /**
   * Get comparison insights for academic research
   */
  async getComparisonInsights(comparisonId?: string): Promise<any> {
    const endpoint = comparisonId 
      ? `${this.apiUrl}/analytics/comparisons/${comparisonId}/insights`
      : `${this.apiUrl}/analytics/comparisons/insights`;
    
    const response = await firstValueFrom(
      this.http.get(endpoint)
    );
    return response;
  }

  /**
   * Export comparison data in various formats
   */
  async exportComparisonData(comparisonId: string, format: 'json' | 'csv' | 'pdf' = 'json'): Promise<Blob> {
    const response = await firstValueFrom(
      this.http.get(`${this.apiUrl}/export/comparisons/${comparisonId}.${format}`, { responseType: 'blob' })
    );
    return response;
  }

  /**
   * Generate academic comparison report
   */
  async generateAcademicReport(comparisonData: any): Promise<Blob> {
    const response = await firstValueFrom(
      this.http.post(`${this.apiUrl}/export/academic-comparison-report`, comparisonData, { responseType: 'blob' })
    );
    return response;
  }
}