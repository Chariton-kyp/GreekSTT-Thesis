import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { Router, RouterModule } from '@angular/router';

// PrimeNG

import { Transcription } from '../../core/models/transcription.model';
import { BaseComponent } from '../../shared/components/base/base.component';
import { ApiPatternsService } from '../../core/services/api-patterns.service';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService } from '../../core/services/notification.service';
import { 
  LoadingSpinnerComponent, 
  PersonalPerformanceChartComponent,
  WeeklyActivityChartComponent,
  EnhancedRecentTranscriptionsComponent
} from '../../shared';

interface DashboardStats {
  totalTranscriptions: number;
  totalMinutesTranscribed: number;
  totalFilesUploaded: number;
  averageAccuracy: number;
  monthlyUsage: {
    minutesUsed: number;
    minutesLimit: number;
    filesUploaded: number;
    filesLimit: number;
  };
  recentActivity: {
    completedToday: number;
    processingCount: number;
    failedCount: number;
  };
}

interface UserDashboardStats {
  // Personal Statistics
  userTranscriptions: number;
  userWhisperUsage: number;
  userWav2vecUsage: number;
  userComparisonAnalyses: number;
  
  // Personal Performance
  userAvgAccuracy: number;
  userAvgProcessingTime: number;
  personalBestAccuracy: number;
  
  // Recent Activity
  recentTranscriptions: Transcription[];
  weeklyActivity: { date: string; count: number }[];
  
  // Personal Insights
  preferredModel: 'whisper' | 'wav2vec2' | 'comparison' | 'Whisper-Large-3' | 'wav2vec2-Greek' | 'Σύγκριση Μοντέλων' | string;
  mostUsedAudioFormat: string;
  averageFileSize: number;
  
  // Academic Progress
  researchProgress: {
    samplesAnalyzed: number;
    modelsCompared: number;
    insightsGenerated: number;
  };
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule, 
    RouterModule, 
    LoadingSpinnerComponent,
    PersonalPerformanceChartComponent,
    WeeklyActivityChartComponent,
    EnhancedRecentTranscriptionsComponent
  ],
  templateUrl: './dashboard.component.html'
})
export class DashboardComponent extends BaseComponent implements OnInit {
  private readonly authService = inject(AuthService);
  protected override readonly apiPatterns = inject(ApiPatternsService);
  protected override readonly notificationService = inject(NotificationService);
  protected override readonly router = inject(Router);

  constructor() {
    super();
  }

  // Private signals
  private _stats = signal<DashboardStats | null>(null);
  private _userStats = signal<UserDashboardStats | null>(null);
  private _recentTranscriptions = signal<Transcription[]>([]);
  private _isLoading = signal(true);
  private _error = signal<string | null>(null);

  // Public readonly signals
  readonly stats = this._stats.asReadonly();
  readonly userStats = this._userStats.asReadonly();
  readonly recentTranscriptions = this._recentTranscriptions.asReadonly();
  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();

  // Computed signals from AuthService
  readonly currentUser = this.authService.currentUser;
  readonly fullName = this.authService.fullName;
  readonly isEmailVerified = this.authService.isEmailVerified;

  // Computed dashboard signals
  readonly usagePercentage = computed(() => {
    // Academic version - no usage limits
    return 0;
  });

  readonly filesUsagePercentage = computed(() => {
    // Academic version - no file limits
    return 0;
  });

  readonly hasRecentActivity = computed(() => {
    return this.recentTranscriptions().length > 0;
  });

  async ngOnInit() {
    await this.loadDashboardData();
    
    // Listen for email verification updates to refresh user data
    this.subscribe(
      this.authService.emailVerificationUpdated$,
      () => {
        // Email verification status changed - refresh user data only (not full dashboard)
        this.authService.refreshUserData().catch(() => {
          console.warn('Failed to refresh user data after email verification');
        });
      }
    );
  }

  async loadDashboardData(): Promise<void> {
    this._isLoading.set(true);
    this._error.set(null);

    try {
      // Load user data
      console.log('[Dashboard] Starting data load with user refresh...');
      
      await this.authService.refreshUserData().catch((error) => {
        // Continue if user data refresh fails
        console.warn('Failed to refresh user data on dashboard load:', error);
      });

      // Load user dashboard data
      await this.loadUserDashboard();

      // Load recent transcriptions for all users
      const transcriptionsResponse = await this.apiPatterns.read<{transcriptions: Transcription[]}>('/transcriptions', { 
        params: { page: '1', per_page: '5', sort: 'created_at', order: 'desc' } 
      }).toPromise().then(response => response?.transcriptions || []).catch((error) => {
        // Show empty state if API fails
        console.warn('Transcriptions API failed, showing empty state:', error);
        return [];
      });

      this._recentTranscriptions.set(transcriptionsResponse);
    } catch (error) {
      console.error('Dashboard data loading failed:', error);
      this._error.set('Αποτυχία φόρτωσης δεδομένων dashboard');
    } finally {
      this._isLoading.set(false);
    }
  }

  async loadUserDashboard(): Promise<void> {
    try {
      const [userStatsResponse, basicStatsResponse] = await Promise.all([
        this.apiPatterns.read<{stats: UserDashboardStats}>('/analytics/users/me/dashboard-stats').toPromise()
          .then(response => response?.stats)
          .catch(() => null),
        this.apiPatterns.read<{stats: DashboardStats}>('/users/me/dashboard-stats').toPromise()
          .then(response => response?.stats || null)
          .catch(() => this.getFallbackStats())
      ]);

      if (userStatsResponse) {
        this._userStats.set(userStatsResponse);
      }
      this._stats.set(basicStatsResponse);
    } catch (error) {
      console.warn('User dashboard stats API failed:', error);
      this._stats.set(this.getFallbackStats());
    }
  }

  private getFallbackStats(): DashboardStats {
    // Minimal fallback for new users when API fails
    return {
      totalTranscriptions: 0,
      totalMinutesTranscribed: 0,
      totalFilesUploaded: 0,
      averageAccuracy: 0,
      monthlyUsage: {
        minutesUsed: 0,
        minutesLimit: -1, // -1 indicates unlimited for academic use
        filesUploaded: 0,
        filesLimit: -1 // -1 indicates unlimited for academic use
      },
      recentActivity: {
        completedToday: 0,
        processingCount: 0,
        failedCount: 0
      }
    };
  }

  trackByTranscriptionId(index: number, transcription: Transcription): string {
    return transcription.id;
  }

  async refreshData(): Promise<void> {
    await this.loadDashboardData();
  }

  getUsageColor(percentage: number): string {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 75) return 'bg-yellow-500';
    return 'bg-cyan-500';
  }

  getRemainingMinutes(): number {
    // Academic version - unlimited usage (represented as -1)
    return -1;
  }

  getRemainingDays(): number {
    const now = new Date();
    const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1);
    return Math.ceil((nextMonth.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  }

  navigateToTranscription(transcriptionId: string): void {
    this.router.navigate(['/app/transcriptions', transcriptionId]);
  }

  /**
   * Get personal performance data for the chart with real user transcription metrics
   */
  getPersonalPerformanceData() {
    const stats = this.userStats();
    const recentTranscriptions = this.recentTranscriptions();
    
    if (!stats || !stats.weeklyActivity) {
      return {
        dates: [],
        accuracy: [],
        processingTime: [],
        wordErrorRate: []
      };
    }

    const dates = stats.weeklyActivity.map(w => w.date);
    
    // Create performance data based on actual transcription data
    // Group recent transcriptions by date to get real daily metrics
    const transcriptionsByDate = new Map<string, any[]>();
    recentTranscriptions.forEach(t => {
      if (t.completedAt) {
        const date = new Date(t.completedAt).toISOString().split('T')[0];
        if (!transcriptionsByDate.has(date)) {
          transcriptionsByDate.set(date, []);
        }
        transcriptionsByDate.get(date)!.push(t);
      }
    });

    const accuracy: number[] = [];
    const processingTime: number[] = [];
    const wordErrorRate: number[] = [];

    dates.forEach(date => {
      const dayTranscriptions = transcriptionsByDate.get(date) || [];
      
      if (dayTranscriptions.length > 0) {
        // Calculate daily averages from real transcriptions
        const dailyAccuracies = dayTranscriptions
          .filter(t => t.academic_accuracy_score != null)
          .map(t => t.academic_accuracy_score);
        
        const dailyProcessingTimes = dayTranscriptions
          .filter(t => t.processing_time != null)
          .map(t => t.processing_time);
        
        const avgAccuracy = dailyAccuracies.length > 0 
          ? dailyAccuracies.reduce((a, b) => a + b, 0) / dailyAccuracies.length 
          : stats.userAvgAccuracy || 0;
          
        const avgProcessingTime = dailyProcessingTimes.length > 0 
          ? dailyProcessingTimes.reduce((a, b) => a + b, 0) / dailyProcessingTimes.length 
          : stats.userAvgProcessingTime || 0;

        accuracy.push(Math.round(avgAccuracy * 10) / 10);
        processingTime.push(Math.round(avgProcessingTime * 100) / 100);
        wordErrorRate.push(Math.round((100 - avgAccuracy) * 10) / 10);
      } else {
        // Use average values for days with no transcriptions
        const avgAccuracy = stats.userAvgAccuracy || 0;
        const avgProcessingTime = stats.userAvgProcessingTime || 0;
        
        accuracy.push(avgAccuracy);
        processingTime.push(avgProcessingTime);
        // For users with no data, show 0 WER instead of 100
        wordErrorRate.push(avgAccuracy > 0 ? (100 - avgAccuracy) : 0);
      }
    });
    
    return {
      dates: dates,
      accuracy: accuracy,
      processingTime: processingTime,
      wordErrorRate: wordErrorRate
    };
  }
}