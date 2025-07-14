import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChartModule } from 'primeng/chart';
import { CardModule } from 'primeng/card';
import { CalendarModule } from 'primeng/calendar';
import { DropdownModule } from 'primeng/dropdown';
import { ButtonModule } from 'primeng/button';
import { TableModule } from 'primeng/table';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { TooltipModule } from 'primeng/tooltip';

import { AnalyticsService, SystemAnalytics } from '../services/analytics.service';
import { NotificationService } from '../../../core/services/notification.service';
import { AuthService } from '../../../core/services/auth.service';
import { ThemeService } from '../../../core/services/theme.service';
import { BaseComponent } from '../../../shared/components/base/base.component';

interface ModelPerformanceData {
  modelName: string;
  totalTranscriptions: number;
  avgAccuracy: number; // Backend calculated
  avgProcessingTime: number;
  avgWER: number;
  successRate: number; // Backend calculated
  avgSpeedScore: number; // Backend calculated speed score
  avgAccuracyFromWER: number; // Backend calculated (100 - WER)
  usageScore: number; // Backend calculated usage score
}

interface TimeSeriesData {
  date: string;
  whisperCount: number;
  wav2vecCount: number;
  comparisonCount: number;
}


@Component({
  selector: 'app-analytics-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ChartModule,
    CardModule,
    CalendarModule,
    DropdownModule,
    ButtonModule,
    TableModule,
    ProgressSpinnerModule,
    TooltipModule
  ],
  templateUrl: './analytics-dashboard.component.html',
  styleUrls: ['./analytics-dashboard.component.scss']
})
export class AnalyticsDashboardComponent extends BaseComponent implements OnInit {
  private readonly analyticsService = inject(AnalyticsService);
  protected override readonly notificationService = inject(NotificationService);
  private readonly authService = inject(AuthService);
  private readonly themeService = inject(ThemeService);

  // State
  readonly isLoading = signal(true);
  readonly analyticsData = signal<SystemAnalytics | null>(null);
  readonly userAnalytics = signal<any>(null);
  readonly performanceData = signal<ModelPerformanceData[]>([]);
  readonly timeSeriesData = signal<TimeSeriesData[]>([]);

  // Date range
  dateRange: Date[] = [
    new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // Last 30 days
    new Date()
  ];

  // Computed values - backend returns user-specific data based on JWT
  readonly averageAccuracy = computed(() => {
    return this.analyticsData()?.averageAccuracy || 0;
  });

  readonly averageWER = computed(() => {
    return this.analyticsData()?.averageWER || 0;
  });

  readonly averageProcessingTime = computed(() => {
    return this.analyticsData()?.averageProcessingTime || 0;
  });

  readonly realtimeFactor = computed(() => {
    return this.analyticsData()?.realtimeFactor || 0;
  });

  readonly comparisonPercentage = computed(() => {
    return this.analyticsData()?.comparisonPercentage || 0;
  });

  readonly totalTranscriptions = computed(() => {
    return this.analyticsData()?.totalTranscriptions || 0;
  });

  readonly totalComparisons = computed(() => {
    return this.analyticsData()?.totalComparisons || 0;
  });

  // Count of transcriptions with actual accuracy evaluations
  readonly evaluatedTranscriptionsCount = computed(() => {
    return this.analyticsData()?.evaluatedTranscriptionsCount || 0;
  });

  // Chart data with theme-aware colors - ALL DATA COMES FROM BACKEND
  readonly modelComparisonChartData = computed(() => {
    const data = this.performanceData();
    const whisper = data.find(m => m.modelName === 'Whisper') || {} as ModelPerformanceData;
    const wav2vec = data.find(m => m.modelName === 'wav2vec2') || {} as ModelPerformanceData;
    const isDark = this.themeService.isDarkMode();

    // Theme-aware colors
    const whisperColor = isDark ? 'rgb(96, 165, 250)' : 'rgb(59, 130, 246)'; // lighter blue for dark mode
    const wav2vecColor = isDark ? 'rgb(74, 222, 128)' : 'rgb(34, 197, 94)'; // lighter green for dark mode
    const pointBorderColor = isDark ? '#1f2937' : '#fff'; // dark gray for dark mode, white for light mode

    return {
      labels: ['Ακρίβεια', 'Ταχύτητα', 'WER (αντίστροφο)', 'Επιτυχία', 'Χρήση'],
      datasets: [
        {
          label: 'Whisper',
          backgroundColor: isDark ? 'rgba(96, 165, 250, 0.2)' : 'rgba(59, 130, 246, 0.2)',
          borderColor: whisperColor,
          pointBackgroundColor: whisperColor,
          pointBorderColor: pointBorderColor,
          pointHoverBackgroundColor: pointBorderColor,
          pointHoverBorderColor: whisperColor,
          data: [
            whisper.avgAccuracy || 0, // Backend calculated
            whisper.avgSpeedScore || 0, // Backend calculated speed score
            whisper.avgAccuracyFromWER || 0, // Backend calculated (100 - WER)
            whisper.successRate || 0, // Backend calculated
            whisper.usageScore || 0 // Backend calculated usage score
          ]
        },
        {
          label: 'wav2vec2',
          backgroundColor: isDark ? 'rgba(74, 222, 128, 0.2)' : 'rgba(34, 197, 94, 0.2)',
          borderColor: wav2vecColor,
          pointBackgroundColor: wav2vecColor,
          pointBorderColor: pointBorderColor,
          pointHoverBackgroundColor: pointBorderColor,
          pointHoverBorderColor: wav2vecColor,
          data: [
            wav2vec.avgAccuracy || 0, // Backend calculated
            wav2vec.avgSpeedScore || 0, // Backend calculated speed score
            wav2vec.avgAccuracyFromWER || 0, // Backend calculated (100 - WER)
            wav2vec.successRate || 0, // Backend calculated
            wav2vec.usageScore || 0 // Backend calculated usage score
          ]
        }
      ]
    };
  });

  readonly usageTimelineChartData = computed(() => {
    const data = this.timeSeriesData();
    const isDark = this.themeService.isDarkMode();
    
    // Theme-aware colors for line chart
    const whisperColor = isDark ? 'rgb(96, 165, 250)' : 'rgb(59, 130, 246)'; // lighter blue for dark mode
    const wav2vecColor = isDark ? 'rgb(74, 222, 128)' : 'rgb(34, 197, 94)'; // lighter green for dark mode
    const comparisonColor = isDark ? 'rgb(196, 181, 253)' : 'rgb(168, 85, 247)'; // lighter purple for dark mode
    
    return {
      labels: data.map(d => this.formatDate(d.date)),
      datasets: [
        {
          label: 'Whisper',
          data: data.map(d => d.whisperCount),
          borderColor: whisperColor,
          backgroundColor: isDark ? 'rgba(96, 165, 250, 0.1)' : 'rgba(59, 130, 246, 0.1)',
          tension: 0.4
        },
        {
          label: 'wav2vec2',
          data: data.map(d => d.wav2vecCount),
          borderColor: wav2vecColor,
          backgroundColor: isDark ? 'rgba(74, 222, 128, 0.1)' : 'rgba(34, 197, 94, 0.1)',
          tension: 0.4
        },
        {
          label: 'Συγκρίσεις',
          data: data.map(d => d.comparisonCount),
          borderColor: comparisonColor,
          backgroundColor: isDark ? 'rgba(196, 181, 253, 0.1)' : 'rgba(168, 85, 247, 0.1)',
          tension: 0.4
        }
      ]
    };
  });

  readonly performanceTableData = computed(() => {
    return this.performanceData();
  });

  // Chart options with theme-aware colors
  readonly chartOptions = computed(() => {
    const isDark = this.themeService.isDarkMode();
    const textColor = isDark ? '#f9fafb' : '#374151';
    const gridColor = isDark ? 'rgba(156, 163, 175, 0.5)' : 'rgba(156, 163, 175, 0.3)';

    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top' as const,
          labels: {
            color: textColor,
            font: {
              size: 12
            }
          }
        }
      },
      scales: {
        r: {
          beginAtZero: true,
          max: 100,
          ticks: {
            color: textColor,
            backdropColor: 'transparent'
          },
          grid: {
            color: gridColor,
            circular: true
          },
          angleLines: {
            color: gridColor
          },
          pointLabels: {
            color: textColor,
            font: {
              size: 11
            }
          }
        }
      }
    };
  });

  readonly timelineChartOptions = computed(() => {
    const isDark = this.themeService.isDarkMode();
    const textColor = isDark ? '#f9fafb' : '#374151';
    const gridColor = isDark ? 'rgba(156, 163, 175, 0.5)' : 'rgba(156, 163, 175, 0.3)';

    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top' as const,
          labels: {
            color: textColor,
            font: {
              size: 12
            }
          }
        }
      },
      scales: {
        x: {
          display: true,
          title: {
            display: true,
            text: 'Ημερομηνία',
            color: textColor,
            font: {
              size: 12,
              weight: 'bold'
            }
          },
          ticks: {
            color: textColor
          },
          grid: {
            color: gridColor
          }
        },
        y: {
          display: true,
          title: {
            display: true,
            text: 'Αριθμός Μεταγραφών',
            color: textColor,
            font: {
              size: 12,
              weight: 'bold'
            }
          },
          ticks: {
            color: textColor
          },
          grid: {
            color: gridColor
          }
        }
      }
    };
  });

  async ngOnInit() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    await this.loadAnalytics();
  }

  async loadAnalytics() {
    try {
      this.isLoading.set(true);
      
      const userAnalytics = await this.analyticsService.getUserAnalytics();
      this.userAnalytics.set(userAnalytics);

      const systemAnalytics = await this.analyticsService.getSystemAnalytics({
        startDate: this.dateRange[0],
        endDate: this.dateRange[1]
      });
      
      this.analyticsData.set(systemAnalytics);
      
      const analytics = this.analyticsData();
      
      if (analytics) {
        this.performanceData.set([
          {
            modelName: 'Whisper',
            totalTranscriptions: analytics.whisperTranscriptions || 0,
            avgAccuracy: analytics.whisperAccuracy || 0,
            avgProcessingTime: analytics.whisperProcessingTime || 0,
            avgWER: analytics.whisperWER || 0,
            successRate: analytics.whisperSuccessRate || 0,
            avgSpeedScore: analytics.whisperSpeedScore || 0,
            avgAccuracyFromWER: analytics.whisperAccuracyFromWER || 0,
            usageScore: analytics.whisperUsageScore || 0
          },
          {
            modelName: 'wav2vec2',
            totalTranscriptions: analytics.wav2vecTranscriptions || 0,
            avgAccuracy: analytics.wav2vecAccuracy || 0,
            avgProcessingTime: analytics.wav2vecProcessingTime || 0,
            avgWER: analytics.wav2vecWER || 0,
            successRate: analytics.wav2vecSuccessRate || 0,
            avgSpeedScore: analytics.wav2vecSpeedScore || 0,
            avgAccuracyFromWER: analytics.wav2vecAccuracyFromWER || 0,
            usageScore: analytics.wav2vecUsageScore || 0
          }
        ]);
        this.timeSeriesData.set(analytics.timeSeriesData || []);
      }

    } catch (error) {
      console.error('Failed to load analytics:', error);
      this.notificationService.showError('Αποτυχία φόρτωσης στατιστικών στοιχείων');
    } finally {
      this.isLoading.set(false);
    }
  }

  async onDateRangeChange() {
    if (this.dateRange && this.dateRange.length === 2) {
      await this.loadAnalytics();
    }
  }

  calculateGrowth(metric: string): number {
    return this.analyticsData()?.growthMetrics?.[metric] || 0;
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('el-GR', { 
      day: 'numeric', 
      month: 'short' 
    });
  }
}