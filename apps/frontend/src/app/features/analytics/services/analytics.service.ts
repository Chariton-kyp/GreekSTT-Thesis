import { Injectable, inject } from '@angular/core';
import { ApiPatternsService } from '../../../core/services/api-patterns.service';

export interface SystemAnalytics {
  totalTranscriptions: number;
  whisperTranscriptions: number;
  wav2vecTranscriptions: number;
  totalComparisons: number;
  evaluatedTranscriptionsCount: number;
  
  // Basic accuracy and performance metrics
  whisperAccuracy: number;
  wav2vecAccuracy: number;
  whisperWER: number;
  wav2vecWER: number;
  whisperProcessingTime: number;
  wav2vecProcessingTime: number;
  whisperSuccessRate: number;
  wav2vecSuccessRate: number;
  
  // Calculated fields for charts (all backend calculated)
  whisperSpeedScore: number;        // Backend calculated speed score
  wav2vecSpeedScore: number;        // Backend calculated speed score
  whisperAccuracyFromWER: number;   // Backend calculated (100 - WER)
  wav2vecAccuracyFromWER: number;   // Backend calculated (100 - WER)
  whisperUsageScore: number;        // Backend calculated usage score
  wav2vecUsageScore: number;        // Backend calculated usage score
  
  // System-wide computed metrics (all backend calculated)
  averageAccuracy: number;          // Backend calculated average
  averageWER: number;               // Backend calculated average
  averageProcessingTime: number;    // Backend calculated average
  realtimeFactor: number;           // Backend calculated realtime factor
  comparisonPercentage: number;     // Backend calculated comparison percentage
  
  // Growth metrics (backend calculated)
  growthMetrics?: {                 // Backend calculated growth stats
    [metric: string]: number;
  };
  
  // Time series data
  timeSeriesData: TimeSeriesData[];
  
  // System health
  systemHealth?: {
    aiServiceStatus: boolean;
    databaseStatus: boolean;
    storageUsage: number;
  };
}

interface TimeSeriesData {
  date: string;
  whisperCount: number;
  wav2vecCount: number;
  comparisonCount: number;
}


interface UserAnalytics {
  userTranscriptions: number;
  userWhisperUsage: number;
  userWav2vecUsage: number;
  userComparisonAnalyses: number;
  userAvgAccuracy: number;
  userAvgProcessingTime: number;
  personalBestAccuracy: number;
  recentTranscriptions: any[];
  weeklyActivity: { date: string; count: number }[];
  preferredModel: 'whisper' | 'wav2vec2' | 'comparison';
  mostUsedAudioFormat: string;
  averageFileSize: number;
  researchProgress: {
    samplesAnalyzed: number;
    modelsCompared: number;
    insightsGenerated: number;
  };
}

interface ModelPerformanceAnalytics {
  whisper: {
    totalTranscriptions: number;
    avgAccuracy: number;
    avgWER: number;
    avgProcessingTime: number;
    successRate: number;
    errorPatterns: ErrorPattern[];
  };
  wav2vec2: {
    totalTranscriptions: number;
    avgAccuracy: number;
    avgWER: number;
    avgProcessingTime: number;
    successRate: number;
    errorPatterns: ErrorPattern[];
  };
  comparison: {
    totalComparisons: number;
    modelAgreementRate: number;
    avgAccuracyDifference: number;
    bestPerformingScenarios: string[];
  };
}

interface ErrorPattern {
  type: string;
  frequency: number;
  examples: string[];
}

interface ReportParams {
  reportType: string;
  dateRange: Date[];
  format: string;
  selectedSections: string[];
  includeCharts: boolean;
  includeRawData: boolean;
  language: string;
}

interface ComprehensiveReport {
  id: string;
  reportType: string;
  generatedAt: Date;
  dateRange: { start: Date; end: Date };
  sections: ReportSection[];
  metadata: ReportMetadata;
}

interface ReportSection {
  id: string;
  title: string;
  content: any;
  charts?: ChartData[];
  tables?: TableData[];
}

interface ReportMetadata {
  totalPages: number;
  dataPoints: number;
  generationTime: number;
  language: string;
}

interface ChartData {
  type: string;
  data: any;
  options: any;
}

interface TableData {
  headers: string[];
  rows: any[][];
}

@Injectable({
  providedIn: 'root'
})
export class AnalyticsService {
  private readonly apiPatterns = inject(ApiPatternsService);
  private readonly baseUrl = '/analytics';

  /**
   * Get system-wide analytics data
   */
  async getSystemAnalytics(params?: { startDate?: Date; endDate?: Date }): Promise<SystemAnalytics> {
    const queryParams: Record<string, string> = {};
    if (params?.startDate) {
      queryParams['start_date'] = params.startDate.toISOString();
    }
    if (params?.endDate) {
      queryParams['end_date'] = params.endDate.toISOString();
    }

    const result = await this.apiPatterns.read<SystemAnalytics>(`${this.baseUrl}/system`, { params: queryParams }).toPromise();
    if (!result) {
      throw new Error('Failed to load system analytics');
    }
    return result;
  }

  /**
   * Get user-specific analytics
   */
  async getUserAnalytics(userId?: string): Promise<UserAnalytics> {
    const endpoint = userId ? `${this.baseUrl}/users/${userId}` : `${this.baseUrl}/users/me`;
    const result = await this.apiPatterns.read<UserAnalytics>(endpoint).toPromise();
    if (!result) {
      throw new Error('Failed to load user analytics');
    }
    return result;
  }

  /**
   * Get model performance analytics
   */
  async getModelPerformanceAnalytics(params?: {
    startDate?: Date;
    endDate?: Date;
    groupBy?: 'day' | 'week' | 'month';
  }): Promise<ModelPerformanceAnalytics> {
    const queryParams: Record<string, string> = {};
    if (params?.startDate) {
      queryParams['start_date'] = params.startDate.toISOString();
    }
    if (params?.endDate) {
      queryParams['end_date'] = params.endDate.toISOString();
    }
    if (params?.groupBy) {
      queryParams['group_by'] = params.groupBy;
    }

    const result = await this.apiPatterns.read<ModelPerformanceAnalytics>(
      `${this.baseUrl}/models/performance`,
      { params: queryParams }
    ).toPromise();
    if (!result) {
      throw new Error('Failed to load model performance analytics');
    }
    return result;
  }

  /**
   * Generate a comprehensive report
   */
  async generateComprehensiveReport(params: ReportParams): Promise<ComprehensiveReport> {
    const payload = {
      report_type: params.reportType,
      start_date: params.dateRange[0].toISOString(),
      end_date: params.dateRange[1].toISOString(),
      format: params.format,
      selected_sections: params.selectedSections,
      include_charts: params.includeCharts,
      include_raw_data: params.includeRawData,
      language: params.language
    };

    const result = await this.apiPatterns.create<ComprehensiveReport>(
      `${this.baseUrl}/reports/generate`,
      payload
    ).toPromise();
    if (!result) {
      throw new Error('Failed to generate comprehensive report');
    }
    return result;
  }

  /**
   * Preview a comprehensive report
   */
  async previewComprehensiveReport(params: {
    report_type: string;
    start_date?: string;
    end_date?: string;
    selected_sections: string[];
    language: string;
  }): Promise<any> {
    const result = await this.apiPatterns.create<any>(
      `${this.baseUrl}/reports/preview`,
      params
    ).toPromise();
    if (!result) {
      throw new Error('Failed to preview comprehensive report');
    }
    return result;
  }

  /**
   * Get recent reports
   */
  async getRecentReports(limit: number = 10): Promise<any[]> {
    const result = await this.apiPatterns.read<any[]>(`${this.baseUrl}/reports/recent`, { params: { limit: limit.toString() } }).toPromise();
    return result || [];
  }


  /**
   * Get error analysis
   */
  async getErrorAnalysis(params?: {
    model?: string;
    startDate?: Date;
    endDate?: Date;
  }): Promise<ErrorPattern[]> {
    const queryParams: Record<string, string> = {};
    if (params?.model) {
      queryParams['model'] = params.model;
    }
    if (params?.startDate) {
      queryParams['start_date'] = params.startDate.toISOString();
    }
    if (params?.endDate) {
      queryParams['end_date'] = params.endDate.toISOString();
    }

    const result = await this.apiPatterns.read<ErrorPattern[]>(`${this.baseUrl}/error-analysis`, { params: queryParams }).toPromise();
    return result || [];
  }

  /**
   * Get comparison insights
   */
  async getComparisonInsights(comparisonId?: string): Promise<any> {
    const endpoint = comparisonId 
      ? `${this.baseUrl}/comparisons/${comparisonId}/insights`
      : `${this.baseUrl}/comparisons/insights`;
    
    const result = await this.apiPatterns.read<any>(endpoint).toPromise();
    return result || null;
  }

  /**
   * Get research progress metrics
   */
  async getResearchProgress(userId?: string): Promise<any> {
    const endpoint = userId 
      ? `${this.baseUrl}/research/progress/${userId}`
      : `${this.baseUrl}/research/progress/me`;
    
    const result = await this.apiPatterns.read<any>(endpoint).toPromise();
    return result || null;
  }

  /**
   * Get peak usage hours
   */
  async getPeakUsageHours(params?: {
    startDate?: Date;
    endDate?: Date;
    timezone?: string;
  }): Promise<{ hour: number; count: number }[]> {
    const queryParams: Record<string, string> = {};
    if (params?.startDate) {
      queryParams['start_date'] = params.startDate.toISOString();
    }
    if (params?.endDate) {
      queryParams['end_date'] = params.endDate.toISOString();
    }
    if (params?.timezone) {
      queryParams['timezone'] = params.timezone;
    } else {
      queryParams['timezone'] = 'Europe/Athens';
    }

    const result = await this.apiPatterns.read<{ hour: number; count: number }[]>(
      `${this.baseUrl}/usage/peak-hours`,
      { params: queryParams }
    ).toPromise();
    return result || [];
  }

  /**
   * Get audio format statistics
   */
  async getAudioFormatStats(): Promise<{ format: string; count: number; percentage: number }[]> {
    const result = await this.apiPatterns.read<{ format: string; count: number; percentage: number }[]>(
      `${this.baseUrl}/audio/format-stats`
    ).toPromise();
    return result || [];
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

    const result = await this.apiPatterns.read<any>(`${this.baseUrl}/models/agreement-analysis`, { params: queryParams }).toPromise();
    return result || null;
  }

  /**
   * Get academic insights
   */
  async getAcademicInsights(params?: {
    focus?: 'accuracy' | 'performance' | 'comparison' | 'errors';
    language?: string;
  }): Promise<any> {
    const queryParams: Record<string, string> = {};
    if (params?.focus) {
      queryParams['focus'] = params.focus;
    }
    if (params?.language) {
      queryParams['language'] = params.language;
    } else {
      queryParams['language'] = 'el';
    }

    const result = await this.apiPatterns.read<any>(`${this.baseUrl}/academic-insights`, { params: queryParams }).toPromise();
    return result || null;
  }

  /**
   * Get comprehensive insights (from insights blueprint)
   */
  async getComprehensiveInsights(): Promise<any> {
    const result = await this.apiPatterns.read<any>(`${this.baseUrl}/insights/comprehensive`).toPromise();
    return result || null;
  }

  /**
   * Get thesis guidance insights
   */
  async getThesisGuidance(): Promise<any> {
    const result = await this.apiPatterns.read<any>(`${this.baseUrl}/insights/thesis-guidance`).toPromise();
    return result || null;
  }

  /**
   * Get model comparison insights from insights blueprint
   */
  async getModelComparisonInsights(): Promise<any> {
    const result = await this.apiPatterns.read<any>(`${this.baseUrl}/insights/model-comparison`).toPromise();
    return result || null;
  }

  /**
   * Get research recommendations
   */
  async getResearchRecommendations(): Promise<any> {
    const result = await this.apiPatterns.read<any>(`${this.baseUrl}/insights/research-recommendations`).toPromise();
    return result || null;
  }

  /**
   * Get personalized insights
   */
  async getPersonalizedInsights(): Promise<any> {
    const result = await this.apiPatterns.read<any>(`${this.baseUrl}/insights/personalized`).toPromise();
    return result || null;
  }

  /**
   * Get comparative study insights
   */
  async getComparativeStudyInsights(): Promise<any> {
    const result = await this.apiPatterns.read<any>(`${this.baseUrl}/insights/comparative-study`).toPromise();
    return result || null;
  }

  /**
   * Get methodology assessment
   */
  async getMethodologyAssessment(): Promise<any> {
    const result = await this.apiPatterns.read<any>(`${this.baseUrl}/insights/methodology-assessment`).toPromise();
    return result || null;
  }

  /**
   * Get publication readiness insights
   */
  async getPublicationReadiness(): Promise<any> {
    const result = await this.apiPatterns.read<any>(`${this.baseUrl}/insights/publication-readiness`).toPromise();
    return result || null;
  }

  /**
   * Get Greek linguistics insights
   */
  async getGreekLinguisticsInsights(): Promise<any> {
    const result = await this.apiPatterns.read<any>(`${this.baseUrl}/insights/greek-linguistics`).toPromise();
    return result || null;
  }

  /**
   * Get optimization suggestions
   */
  async getOptimizationSuggestions(): Promise<any> {
    const result = await this.apiPatterns.read<any>(`${this.baseUrl}/insights/optimization-suggestions`).toPromise();
    return result || null;
  }

  /**
   * Get error trends analysis
   */
  async getErrorTrends(params?: {
    startDate?: Date;
    endDate?: Date;
    model?: string;
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

    const result = await this.apiPatterns.read<any>(`${this.baseUrl}/errors/trends`, { params: queryParams }).toPromise();
    return result || null;
  }

  /**
   * Get error patterns analysis
   */
  async getErrorPatterns(params?: {
    startDate?: Date;
    endDate?: Date;
    model?: string;
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

    const result = await this.apiPatterns.read<any>(`${this.baseUrl}/errors/patterns`, { params: queryParams }).toPromise();
    return result || null;
  }

  /**
   * Get research insights
   */
  async getResearchInsights(): Promise<any> {
    const result = await this.apiPatterns.read<any>(`${this.baseUrl}/research/insights`).toPromise();
    return result || null;
  }

  /**
   * Get progress milestones
   */
  async getProgressMilestones(): Promise<any> {
    const result = await this.apiPatterns.read<any>(`${this.baseUrl}/progress/milestones`).toPromise();
    return result || [];
  }

  /**
   * Create progress milestone
   */
  async createProgressMilestone(milestone: any): Promise<any> {
    const result = await this.apiPatterns.create<any>(`${this.baseUrl}/progress/milestones`, milestone).toPromise();
    return result;
  }

  /**
   * Update progress milestone
   */
  async updateProgressMilestone(milestoneId: number, updates: any): Promise<any> {
    const result = await this.apiPatterns.update<any>(`${this.baseUrl}/progress/milestones/${milestoneId}`, updates).toPromise();
    return result;
  }

  /**
   * Get detailed comparison analytics
   */
  async getDetailedComparisonAnalytics(): Promise<any> {
    const result = await this.apiPatterns.read<any>(`${this.baseUrl}/comparison/detailed`).toPromise();
    return result || null;
  }

  /**
   * Get performance benchmarks
   */
  async getPerformanceBenchmarks(): Promise<any> {
    const result = await this.apiPatterns.read<any>(`${this.baseUrl}/performance/benchmarks`).toPromise();
    return result || null;
  }
}