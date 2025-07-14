import { Component, Input, OnChanges, SimpleChanges, ViewChild, ElementRef, OnDestroy, AfterViewInit, ChangeDetectionStrategy, signal, computed, inject, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { 
  Chart, 
  ChartConfiguration, 
  ChartData, 
  ChartType,
  registerables
} from 'chart.js';
import { WERResult, ComparisonWERResult } from '../../../core/models/wer-result.model';
import { TranscriptionResult } from '../../../core/models/transcription.model';
import { ThemeService } from '../../../core/services/theme.service';

Chart.register(...registerables);

export interface ComparisonChartData {
  whisperResult?: TranscriptionResult;
  wav2vecResult?: TranscriptionResult;
  werResult?: WERResult;
  comparisonWER?: ComparisonWERResult;
  modelUsed?: 'whisper' | 'wav2vec2'; // For single model charts
  processingTimes?: {
    whisper?: number;
    wav2vec?: number;
  };
  confidenceScores?: {
    whisper?: number;
    wav2vec?: number;
  };
}

@Component({
  selector: 'app-comparison-charts',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="comparison-charts-container">
      <!-- WER/CER Comparison Chart -->
      @if (showWERChart()) {
        <div class="chart-section mb-4">
          <h3 class="text-lg font-semibold mb-2">
            <i class="pi pi-chart-bar mr-2"></i>Σύγκριση WER/CER
          </h3>
          <div class="chart-wrapper">
            <canvas #werChart></canvas>
          </div>
        </div>
      }

      <!-- Performance Metrics Chart -->
      @if (showPerformanceChart()) {
        <div class="chart-section mb-4">
          <h3 class="text-lg font-semibold mb-2">
            <i class="pi pi-gauge mr-2"></i>Μετρικές Απόδοσης
          </h3>
          <div class="chart-wrapper">
            <canvas #performanceChart></canvas>
          </div>
        </div>
      }

      <!-- Processing Time Chart -->
      @if (showProcessingTimeChart()) {
        <div class="chart-section mb-4">
          <h3 class="text-lg font-semibold mb-2">
            <i class="pi pi-clock mr-2"></i>Χρόνος Επεξεργασίας
          </h3>
          <div class="chart-wrapper">
            <canvas #processingTimeChart></canvas>
          </div>
        </div>
      }

      <!-- Confidence Score Chart -->
      @if (showConfidenceChart()) {
        <div class="chart-section mb-4">
          <h3 class="text-lg font-semibold mb-2">
            <i class="pi pi-shield mr-2"></i>Βαθμοί Εμπιστοσύνης
          </h3>
          <div class="chart-wrapper">
            <canvas #confidenceChart></canvas>
          </div>
        </div>
      }

      <!-- Error Breakdown Chart -->
      @if (showErrorBreakdownChart()) {
        <div class="chart-section mb-4">
          <h3 class="text-lg font-semibold mb-2">
            <i class="pi pi-exclamation-triangle mr-2"></i>Ανάλυση Σφαλμάτων
          </h3>
          <div class="chart-wrapper">
            <canvas #errorBreakdownChart></canvas>
          </div>
        </div>
      }

      <!-- Greek-specific Metrics Chart -->
      @if (showGreekMetricsChart()) {
        <div class="chart-section mb-4">
          <h3 class="text-lg font-semibold mb-2">
            <i class="pi pi-language mr-2"></i>Ελληνικά Χαρακτηριστικά
          </h3>
          <div class="chart-wrapper">
            <canvas #greekMetricsChart></canvas>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .comparison-charts-container {
      background: var(--surface-card, #ffffff);
      border-radius: 8px;
      padding: 1.5rem;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
      border: 1px solid var(--surface-border, #e9ecef);
      min-height: 200px;
    }

    .chart-section {
      background: var(--surface-hover, #f8f9fa);
      border-radius: 6px;
      padding: 1rem;
      border: none; /* Remove border completely */
      margin-bottom: 1rem;
    }

    .chart-wrapper {
      position: relative;
      height: 300px;
      margin-top: 0.5rem;
      background: transparent;
    }

    .chart-wrapper canvas {
      max-height: 300px;
      width: 100% !important;
      height: 300px !important;
    }

    h3 {
      color: var(--text-primary, #495057);
      margin-bottom: 0.5rem;
      display: flex;
      align-items: center;
      font-size: 1.125rem;
      font-weight: 600;
    }

    .pi {
      color: var(--color-accent-primary, #007bff);
      margin-right: 0.5rem;
    }

    /* Dark mode styles */
    @media (prefers-color-scheme: dark) {
      .comparison-charts-container {
        background: var(--surface-card, #1f2937);
        border-color: var(--surface-border, #374151);
      }

      .chart-section {
        background: var(--surface-hover, #374151);
        border-color: var(--surface-border, #4b5563);
      }

      h3 {
        color: var(--text-primary, #f9fafb);
      }

      .pi {
        color: var(--color-accent-primary, #06b6d4);
      }
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ComparisonChartsComponent implements OnChanges, OnDestroy {
  @Input() data: ComparisonChartData | null = null;
  @Input() showWER: boolean = true;
  @Input() showPerformance: boolean = true;
  @Input() showProcessingTime: boolean = true;
  @Input() showConfidence: boolean = true;
  @Input() showErrorBreakdown: boolean = true;
  @Input() showGreekMetrics: boolean = true;

  @ViewChild('werChart', { static: false }) werChartRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('performanceChart', { static: false }) performanceChartRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('processingTimeChart', { static: false }) processingTimeChartRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('confidenceChart', { static: false }) confidenceChartRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('errorBreakdownChart', { static: false }) errorBreakdownChartRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('greekMetricsChart', { static: false }) greekMetricsChartRef!: ElementRef<HTMLCanvasElement>;

  private charts: { [key: string]: Chart } = {};
  private readonly themeService = inject(ThemeService);

  constructor() {
    // Create an effect that updates charts when theme changes
    effect(() => {
      const isDark = this.themeService.isDarkMode();
      console.log('Theme changed effect triggered - isDark:', isDark);
      
      // Only update if we have data and charts are rendered
      if (this.data) {
        setTimeout(() => {
          console.log('Updating charts due to theme change');
          this.updateCharts();
        }, 50);
      }
    });
  }

  private getThemeColors() {
    // Simple and clear theme detection
    const isDark = this.themeService.isDarkMode();
    
    const colors = {
      whisperColor: '#2563eb', // More vibrant blue
      wav2vecColor: '#059669', // More vibrant green  
      whisperColorLight: '#93c5fd', // Light blue for backgrounds
      wav2vecColorLight: '#6ee7b7', // Light green for backgrounds
      textColor: isDark ? '#ffffff' : '#000000',
      gridColor: isDark ? 'rgba(156, 163, 175, 0.6)' : 'rgba(156, 163, 175, 0.3)', // More visible grid lines
      bgColor: isDark ? '#1f2937' : '#ffffff'
    };
    
    return colors;
  }

  // Computed properties for conditional rendering
  readonly showWERChart = computed(() => 
    this.showWER && (this.data?.comparisonWER || this.data?.werResult)
  );

  readonly showPerformanceChart = computed(() => 
    this.showPerformance && (this.data?.comparisonWER || this.data?.werResult)
  );

  readonly showProcessingTimeChart = computed(() => 
    this.showProcessingTime && this.data?.processingTimes && 
    (this.data.processingTimes.whisper || this.data.processingTimes.wav2vec)
  );

  readonly showConfidenceChart = computed(() => 
    this.showConfidence && this.data?.confidenceScores && 
    (this.data.confidenceScores.whisper || this.data.confidenceScores.wav2vec)
  );

  readonly showErrorBreakdownChart = computed(() => 
    this.showErrorBreakdown && this.data?.comparisonWER
  );

  readonly showGreekMetricsChart = computed(() => 
    this.showGreekMetrics && this.data?.comparisonWER
  );

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['data'] && this.data) {
      // Give Angular time to render the DOM before creating charts
      setTimeout(() => this.updateCharts(), 100);
    }
  }

  ngAfterViewInit(): void {
    // Charts will be updated automatically when data changes 
    // and the getThemeColors() method will use the current theme from themeService
  }

  ngOnDestroy(): void {
    Object.values(this.charts).forEach(chart => chart.destroy());
  }

  private updateCharts(): void {
    if (!this.data) return;

    if (this.showWERChart()) {
      this.createWERChart();
    }
    if (this.showPerformanceChart()) {
      this.createPerformanceChart();
    }
    if (this.showProcessingTimeChart()) {
      this.createProcessingTimeChart();
    }
    if (this.showConfidenceChart()) {
      this.createConfidenceChart();
    }
    if (this.showErrorBreakdownChart()) {
      this.createErrorBreakdownChart();
    }
    if (this.showGreekMetricsChart()) {
      this.createGreekMetricsChart();
    }
  }

  private createWERChart(): void {
    if (!this.werChartRef?.nativeElement || (!this.data?.comparisonWER && !this.data?.werResult)) return;

    this.destroyChart('wer');

    const ctx = this.werChartRef.nativeElement.getContext('2d');
    if (!ctx) return;

    const colors = this.getThemeColors();
    let config: ChartConfiguration | null = null;

    if (this.data.comparisonWER) {
      // Comparison mode - both models
      const { whisperWER, wav2vecWER } = this.data.comparisonWER;
      config = {
        type: 'bar',
        data: {
          labels: ['Word Error Rate (WER)', 'Character Error Rate (CER)', 'Ακρίβεια Λέξεων', 'Ακρίβεια Χαρακτήρων'],
          datasets: [
            {
              label: 'Whisper',
              data: [
                whisperWER.werPercentage,
                whisperWER.cerPercentage,
                whisperWER.accuracy, // Backend already calculates as percentage
                whisperWER.charAccuracy // Backend already calculates as percentage
              ],
              backgroundColor: colors.whisperColor,
              borderWidth: 2,
              borderColor: colors.whisperColor,
              borderRadius: 4
            },
            {
              label: 'Wav2Vec2',
              data: [
                wav2vecWER.werPercentage,
                wav2vecWER.cerPercentage,
                wav2vecWER.accuracy, // Backend already calculates as percentage
                wav2vecWER.charAccuracy // Backend already calculates as percentage
              ],
              backgroundColor: colors.wav2vecColor,
              borderWidth: 2,
              borderColor: colors.wav2vecColor,
              borderRadius: 4
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: true,
              text: 'Σύγκριση WER/CER και Ακρίβειας',
              color: colors.textColor,
              font: {
                size: 16,
                weight: 'bold'
              }
            },
            legend: {
              display: true,
              position: 'top',
              labels: {
                color: colors.textColor,
                usePointStyle: true,
                padding: 20
              }
            }
          },
          scales: {
            x: {
              ticks: {
                color: colors.textColor
              },
              grid: {
                color: colors.gridColor,
                lineWidth: 1,
                display: true
              }
            },
            y: {
              beginAtZero: true,
              max: 100,
              ticks: {
                color: colors.textColor,
                callback: function(value) {
                  return value + '%';
                }
              },
              grid: {
                color: colors.gridColor,
                lineWidth: 1,
                display: true
              }
            }
          }
        }
      };
    } else if (this.data.werResult) {
      // Single model mode - performance charts
      const werData = this.data.werResult;
      
      // Determine model name and color from modelUsed or default to Whisper
      const modelName = this.data.modelUsed === 'wav2vec2' ? 'Wav2Vec2' : 'Whisper';
      const modelColor = this.data.modelUsed === 'wav2vec2' ? colors.wav2vecColor : colors.whisperColor;
      
      config = {
        type: 'bar',
        data: {
          labels: ['Word Error Rate (WER)', 'Character Error Rate (CER)', 'Ακρίβεια Λέξεων', 'Ακρίβεια Χαρακτήρων'],
          datasets: [
            {
              label: modelName,
              data: [
                werData.werPercentage,
                werData.cerPercentage,
                werData.accuracy,
                werData.charAccuracy
              ],
              backgroundColor: modelColor,
              borderWidth: 2,
              borderColor: modelColor,
              borderRadius: 4
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: true,
              text: `Απόδοση Μοντέλου ${modelName}`,
              color: colors.textColor,
              font: {
                size: 16,
                weight: 'bold'
              }
            },
            legend: {
              display: true,
              position: 'top',
              labels: {
                color: colors.textColor,
                usePointStyle: true,
                padding: 20
              }
            }
          },
          scales: {
            x: {
              ticks: {
                color: colors.textColor
              },
              grid: {
                color: colors.gridColor,
                lineWidth: 1,
                display: true
              }
            },
            y: {
              beginAtZero: true,
              max: 100,
              ticks: {
                color: colors.textColor,
                callback: function(value) {
                  return value + '%';
                }
              },
              grid: {
                color: colors.gridColor,
                lineWidth: 1,
                display: true
              }
            }
          }
        }
      };
    }

    if (config) {
      this.charts['wer'] = new Chart(ctx, config);
    }
  }

  private createPerformanceChart(): void {
    if (!this.performanceChartRef?.nativeElement || (!this.data?.comparisonWER && !this.data?.werResult)) return;

    this.destroyChart('performance');

    const ctx = this.performanceChartRef.nativeElement.getContext('2d');
    if (!ctx) return;

    const colors = this.getThemeColors();
    let config: ChartConfiguration | null = null;

    if (this.data.comparisonWER) {
      // Comparison mode - both models
      const { whisperWER, wav2vecWER } = this.data.comparisonWER;
      config = {
        type: 'radar',
        data: {
          labels: ['Ακρίβεια Λέξεων', 'Ακρίβεια Χαρακτήρων', 'Ελληνικά Χαρακτηριστικά', 'Ακρίβεια Τόνων'],
          datasets: [
            {
              label: 'Whisper',
              data: [
                whisperWER.accuracy, // Backend already calculates as percentage
                whisperWER.charAccuracy, // Backend already calculates as percentage
                whisperWER.greekCharacterAccuracy,
                whisperWER.diacriticAccuracy
              ],
              backgroundColor: colors.whisperColor + '40', // 25% opacity
              borderColor: colors.whisperColor,
              pointBackgroundColor: colors.whisperColor,
              pointBorderColor: colors.bgColor,
              pointHoverBackgroundColor: colors.bgColor,
              pointHoverBorderColor: colors.whisperColor,
              borderWidth: 2,
              pointBorderWidth: 2
            },
            {
              label: 'Wav2Vec2',
              data: [
                wav2vecWER.accuracy, // Backend already calculates as percentage
                wav2vecWER.charAccuracy, // Backend already calculates as percentage
                wav2vecWER.greekCharacterAccuracy,
                wav2vecWER.diacriticAccuracy
              ],
              backgroundColor: colors.wav2vecColor + '40', // 25% opacity
              borderColor: colors.wav2vecColor,
              pointBackgroundColor: colors.wav2vecColor,
              pointBorderColor: colors.bgColor,
              pointHoverBackgroundColor: colors.bgColor,
              pointHoverBorderColor: colors.wav2vecColor,
              borderWidth: 2,
              pointBorderWidth: 2
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: true,
              text: 'Συνολική Απόδοση Μοντέλων',
              color: colors.textColor,
              font: {
                size: 16,
                weight: 'bold'
              }
            },
            legend: {
              display: true,
              position: 'top',
              labels: {
                color: colors.textColor,
                usePointStyle: true,
                padding: 20
              }
            }
          },
          scales: {
            r: {
              beginAtZero: true,
              max: 100,
              ticks: {
                color: colors.textColor,
                backdropColor: 'transparent', // Remove gray background
                callback: function(value) {
                  return value + '%';
                }
              },
              grid: {
                color: colors.gridColor,
                lineWidth: 1,
                display: true
              },
              angleLines: {
                color: colors.gridColor
              },
              pointLabels: {
                color: colors.textColor
              }
            }
          }
        }
      };
    } else if (this.data.werResult) {
      // Single model mode - performance charts
      const werData = this.data.werResult;
      
      // Determine model name and color from modelUsed or default to Whisper
      const modelName = this.data.modelUsed === 'wav2vec2' ? 'Wav2Vec2' : 'Whisper';
      const modelColor = this.data.modelUsed === 'wav2vec2' ? colors.wav2vecColor : colors.whisperColor;
      
      config = {
        type: 'radar',
        data: {
          labels: ['Ακρίβεια Λέξεων', 'Ακρίβεια Χαρακτήρων', 'Ελληνικά Χαρακτηριστικά', 'Ακρίβεια Τόνων'],
          datasets: [
            {
              label: modelName,
              data: [
                werData.accuracy,
                werData.charAccuracy,
                werData.greekCharacterAccuracy,
                werData.diacriticAccuracy
              ],
              backgroundColor: modelColor + '40', // 25% opacity
              borderColor: modelColor,
              pointBackgroundColor: modelColor,
              pointBorderColor: colors.bgColor,
              pointHoverBackgroundColor: colors.bgColor,
              pointHoverBorderColor: modelColor,
              borderWidth: 2,
              pointBorderWidth: 2
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: true,
              text: `Απόδοση Μοντέλου ${modelName}`,
              color: colors.textColor,
              font: {
                size: 16,
                weight: 'bold'
              }
            },
            legend: {
              display: true,
              position: 'top',
              labels: {
                color: colors.textColor,
                usePointStyle: true,
                padding: 20
              }
            }
          },
          scales: {
            r: {
              beginAtZero: true,
              max: 100,
              ticks: {
                color: colors.textColor,
                backdropColor: 'transparent', // Remove gray background
                callback: function(value) {
                  return value + '%';
                }
              },
              grid: {
                color: colors.gridColor,
                lineWidth: 1,
                display: true
              },
              angleLines: {
                color: colors.gridColor
              },
              pointLabels: {
                color: colors.textColor
              }
            }
          }
        }
      };
    }

    if (config) {
      this.charts['performance'] = new Chart(ctx, config);
    }
  }

  private createProcessingTimeChart(): void {
    if (!this.processingTimeChartRef?.nativeElement || !this.data?.processingTimes) return;

    this.destroyChart('processingTime');

    const ctx = this.processingTimeChartRef.nativeElement.getContext('2d');
    if (!ctx) return;

    const { whisper, wav2vec } = this.data.processingTimes;
    const colors = this.getThemeColors();

    const config: ChartConfiguration = {
      type: 'doughnut',
      data: {
        labels: ['Whisper', 'wav2vec2'],
        datasets: [
          {
            data: [whisper || 0, wav2vec || 0],
            backgroundColor: [
              colors.whisperColor, // Full vibrant color
              colors.wav2vecColor  // Full vibrant color
            ],
            borderWidth: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'Χρόνος Επεξεργασίας (δευτερόλεπτα)',
            color: colors.textColor,
            font: {
              size: 16,
              weight: 'bold'
            }
          },
          legend: {
            position: 'bottom',
            labels: {
              color: colors.textColor,
              usePointStyle: true,
              padding: 20
            }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                return context.label + ': ' + context.parsed + 's';
              }
            }
          }
        }
      }
    };

    this.charts['processingTime'] = new Chart(ctx, config);
  }

  private createConfidenceChart(): void {
    if (!this.confidenceChartRef?.nativeElement || !this.data?.confidenceScores) return;

    this.destroyChart('confidence');

    const ctx = this.confidenceChartRef.nativeElement.getContext('2d');
    if (!ctx) return;

    const { whisper, wav2vec } = this.data.confidenceScores;
    const colors = this.getThemeColors();

    const config: ChartConfiguration = {
      type: 'bar',
      data: {
        labels: ['Whisper', 'wav2vec2'],
        datasets: [
          {
            label: 'Βαθμός Εμπιστοσύνης',
            data: [whisper || 0, wav2vec || 0],
            backgroundColor: [
              colors.whisperColor,
              colors.wav2vecColor
            ],
            borderWidth: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'Βαθμοί Εμπιστοσύνης Μοντέλων',
            color: colors.textColor,
            font: {
              size: 16,
              weight: 'bold'
            }
          },
          legend: {
            display: false
          }
        },
        scales: {
          x: {
            ticks: {
              color: colors.textColor
            },
            grid: {
              color: colors.gridColor,
              lineWidth: 1,
              display: true
            }
          },
          y: {
            beginAtZero: true,
            max: 1,
            ticks: {
              color: colors.textColor,
              callback: function(value) {
                return (Number(value) * 100).toFixed(0) + '%';
              }
            },
            grid: {
              color: colors.gridColor,
              lineWidth: 1,
              display: true
            }
          }
        }
      }
    };

    this.charts['confidence'] = new Chart(ctx, config);
  }

  private createErrorBreakdownChart(): void {
    if (!this.errorBreakdownChartRef?.nativeElement || !this.data?.comparisonWER) return;

    this.destroyChart('errorBreakdown');

    const ctx = this.errorBreakdownChartRef.nativeElement.getContext('2d');
    if (!ctx) return;

    const { whisperWER, wav2vecWER } = this.data.comparisonWER;
    const colors = this.getThemeColors();

    const config: ChartConfiguration = {
      type: 'bar',
      data: {
        labels: ['Αντικαταστάσεις', 'Διαγραφές', 'Εισαγωγές', 'Σφάλματα Τόνων'],
        datasets: [
          {
            label: 'Whisper',
            data: [
              whisperWER.substitutions,
              whisperWER.deletions,
              whisperWER.insertions,
              whisperWER.diacriticErrors
            ],
            backgroundColor: colors.whisperColor,
            borderWidth: 0
          },
          {
            label: 'wav2vec2',
            data: [
              wav2vecWER.substitutions,
              wav2vecWER.deletions,
              wav2vecWER.insertions,
              wav2vecWER.diacriticErrors
            ],
            backgroundColor: colors.wav2vecColor,
            borderWidth: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'Ανάλυση Τύπων Σφαλμάτων',
            color: colors.textColor,
            font: {
              size: 16,
              weight: 'bold'
            }
          },
          legend: {
            display: true,
            position: 'top',
            labels: {
              color: colors.textColor,
              usePointStyle: true,
              padding: 20
            }
          }
        },
        scales: {
          x: {
            ticks: {
              color: colors.textColor
            },
            grid: {
              color: colors.gridColor,
              lineWidth: 1,
              display: true
            }
          },
          y: {
            beginAtZero: true,
            ticks: {
              color: colors.textColor,
              stepSize: 1
            },
            grid: {
              color: colors.gridColor,
              lineWidth: 1,
              display: true
            }
          }
        }
      }
    };

    this.charts['errorBreakdown'] = new Chart(ctx, config);
  }

  private createGreekMetricsChart(): void {
    if (!this.greekMetricsChartRef?.nativeElement || !this.data?.comparisonWER) return;

    this.destroyChart('greekMetrics');

    const ctx = this.greekMetricsChartRef.nativeElement.getContext('2d');
    if (!ctx) return;

    const { whisperWER, wav2vecWER } = this.data.comparisonWER;
    const colors = this.getThemeColors();

    const config: ChartConfiguration = {
      type: 'line',
      data: {
        labels: ['Ελληνικοί Χαρακτήρες', 'Ακρίβεια Τόνων'],
        datasets: [
          {
            label: 'Whisper',
            data: [
              whisperWER.greekCharacterAccuracy,
              whisperWER.diacriticAccuracy
            ],
            backgroundColor: colors.whisperColor + '30', // 20% opacity
            borderColor: colors.whisperColor,
            borderWidth: 3,
            fill: true,
            tension: 0.4,
            pointBackgroundColor: colors.whisperColor,
            pointBorderColor: colors.bgColor,
            pointBorderWidth: 2
          },
          {
            label: 'wav2vec2',
            data: [
              wav2vecWER.greekCharacterAccuracy,
              wav2vecWER.diacriticAccuracy
            ],
            backgroundColor: colors.wav2vecColor + '30', // 20% opacity
            borderColor: colors.wav2vecColor,
            borderWidth: 3,
            fill: true,
            tension: 0.4,
            pointBackgroundColor: colors.wav2vecColor,
            pointBorderColor: colors.bgColor,
            pointBorderWidth: 2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'Ελληνικά Χαρακτηριστικά',
            color: colors.textColor,
            font: {
              size: 16,
              weight: 'bold'
            }
          },
          legend: {
            display: true,
            position: 'top',
            labels: {
              color: colors.textColor,
              usePointStyle: true,
              padding: 20
            }
          }
        },
        scales: {
          x: {
            ticks: {
              color: colors.textColor
            },
            grid: {
              color: colors.gridColor,
              lineWidth: 1,
              display: true
            }
          },
          y: {
            beginAtZero: true,
            max: 100,
            ticks: {
              color: colors.textColor,
              callback: function(value) {
                return value + '%';
              }
            },
            grid: {
              color: colors.gridColor,
              lineWidth: 1,
              display: true
            }
          }
        }
      }
    };

    this.charts['greekMetrics'] = new Chart(ctx, config);
  }

  private destroyChart(chartKey: string): void {
    if (this.charts[chartKey]) {
      this.charts[chartKey].destroy();
      delete this.charts[chartKey];
    }
  }
}