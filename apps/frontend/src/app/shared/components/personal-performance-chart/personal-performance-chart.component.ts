import { Component, Input, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChartModule } from 'primeng/chart';
import { ThemeService } from '../../../core/services/theme.service';

interface PerformanceData {
  dates: string[];
  accuracy: number[];
  processingTime: number[];
  wordErrorRate: number[];
}

@Component({
  selector: 'app-personal-performance-chart',
  standalone: true,
  imports: [CommonModule, ChartModule],
  template: `
    <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">
          Προσωπική Επίδοση
        </h3>
        <select class="text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-700 dark:text-white px-3 py-1 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent">
          <option value="7">Τελευταίες 7 ημέρες</option>
          <option value="30">Τελευταίες 30 ημέρες</option>
          <option value="90">Τελευταίες 90 ημέρες</option>
        </select>
      </div>
      
      <div class="h-64">
        <p-chart type="line" [data]="chartData()" [options]="chartOptions()" styleClass="dashboard-chart"></p-chart>
      </div>
      
      <div class="mt-4 grid grid-cols-3 gap-4 text-center">
        <div>
          <p class="text-xs text-gray-500 dark:text-gray-400">Μέση Ακρίβεια</p>
          <p class="text-lg font-semibold text-gray-900 dark:text-white">
            {{ getAverageAccuracy() }}%
          </p>
        </div>
        <div>
          <p class="text-xs text-gray-500 dark:text-gray-400">Μέσος Χρόνος</p>
          <p class="text-lg font-semibold text-gray-900 dark:text-white">
            {{ getAverageTime() }}s
          </p>
        </div>
        <div>
          <p class="text-xs text-gray-500 dark:text-gray-400">Μέσο WER</p>
          <p class="text-lg font-semibold text-gray-900 dark:text-white">
            {{ getAverageWER() }}%
          </p>
        </div>
      </div>
    </div>
  `,
  styles: [`
    ::ng-deep .dashboard-chart {
      .p-chart {
        height: 250px;
        
        canvas {
          max-height: 250px !important;
          border: none !important;
          outline: none !important;
          box-shadow: none !important;
        }
      }
    }
  `]
})
export class PersonalPerformanceChartComponent {
  @Input() data: PerformanceData | null = null;
  private readonly themeService = inject(ThemeService);

  // Chart data with theme-aware colors - exactly like analytics dashboard
  readonly chartData = computed(() => {
    if (!this.data) {
      return {
        labels: [],
        datasets: []
      };
    }

    const isDark = this.themeService.isDarkMode();
    
    // Theme-aware colors for line chart - using analytics pattern
    const accuracyColor = isDark ? 'rgb(74, 222, 128)' : 'rgb(34, 197, 94)'; // green
    const werColor = isDark ? 'rgb(248, 113, 113)' : 'rgb(239, 68, 68)'; // red
    const timeColor = isDark ? 'rgb(96, 165, 250)' : 'rgb(59, 130, 246)'; // blue
    const pointBorderColor = isDark ? '#1f2937' : '#fff';

    return {
      labels: this.data.dates,
      datasets: [
        {
          label: 'Ακρίβεια (%)',
          data: this.data.accuracy,
          borderColor: accuracyColor,
          backgroundColor: isDark ? 'rgba(74, 222, 128, 0.1)' : 'rgba(34, 197, 94, 0.1)',
          pointBackgroundColor: accuracyColor,
          pointBorderColor: pointBorderColor,
          pointHoverBackgroundColor: pointBorderColor,
          pointHoverBorderColor: accuracyColor,
          tension: 0.4,
          yAxisID: 'y'
        },
        {
          label: 'WER (%)',
          data: this.data.wordErrorRate,
          borderColor: werColor,
          backgroundColor: isDark ? 'rgba(248, 113, 113, 0.1)' : 'rgba(239, 68, 68, 0.1)',
          pointBackgroundColor: werColor,
          pointBorderColor: pointBorderColor,
          pointHoverBackgroundColor: pointBorderColor,
          pointHoverBorderColor: werColor,
          tension: 0.4,
          yAxisID: 'y'
        },
        {
          label: 'Χρόνος (s)',
          data: this.data.processingTime,
          borderColor: timeColor,
          backgroundColor: isDark ? 'rgba(96, 165, 250, 0.1)' : 'rgba(59, 130, 246, 0.1)',
          pointBackgroundColor: timeColor,
          pointBorderColor: pointBorderColor,
          pointHoverBackgroundColor: pointBorderColor,
          pointHoverBorderColor: timeColor,
          tension: 0.4,
          yAxisID: 'y1'
        }
      ]
    };
  });

  // Chart options with theme-aware colors - exactly like analytics dashboard
  readonly chartOptions = computed(() => {
    const isDark = this.themeService.isDarkMode();
    const textColor = isDark ? '#f9fafb' : '#374151';
    const gridColor = isDark ? 'rgba(156, 163, 175, 0.5)' : 'rgba(156, 163, 175, 0.3)';

    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom' as const,
          labels: {
            usePointStyle: true,
            padding: 15,
            color: textColor,
            font: {
              size: 11
            }
          }
        },
        tooltip: {
          callbacks: {
            label: (context: any) => {
              const label = context.dataset.label || '';
              const value = context.parsed.y || 0;
              
              if (label.includes('Χρόνος')) {
                return `${label}: ${value.toFixed(2)}s`;
              }
              return `${label}: ${value.toFixed(1)}%`;
            }
          }
        }
      },
      scales: {
        x: {
          display: true,
          ticks: {
            maxRotation: 0,
            autoSkip: true,
            maxTicksLimit: 7,
            color: textColor
          },
          grid: {
            color: gridColor
          }
        },
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          beginAtZero: true,
          max: 100,
          title: {
            display: true,
            text: 'Ακρίβεια / WER (%)',
            color: textColor,
            font: {
              size: 12,
              weight: 'bold'
            }
          },
          ticks: {
            callback: (value: any) => value + '%',
            color: textColor
          },
          grid: {
            color: gridColor
          }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          beginAtZero: true,
          title: {
            display: true,
            text: 'Χρόνος (s)',
            color: textColor,
            font: {
              size: 12,
              weight: 'bold'
            }
          },
          ticks: {
            callback: (value: any) => value + 's',
            color: textColor
          },
          grid: {
            drawOnChartArea: false
          }
        }
      }
    };
  });

  getAverageAccuracy(): string {
    if (!this.data?.accuracy.length) return '0';
    const avg = this.data.accuracy.reduce((a, b) => a + b, 0) / this.data.accuracy.length;
    return avg.toFixed(1);
  }

  getAverageTime(): string {
    if (!this.data?.processingTime.length) return '0';
    const avg = this.data.processingTime.reduce((a, b) => a + b, 0) / this.data.processingTime.length;
    return avg.toFixed(2);
  }

  getAverageWER(): string {
    if (!this.data?.wordErrorRate.length) return '0';
    const avg = this.data.wordErrorRate.reduce((a, b) => a + b, 0) / this.data.wordErrorRate.length;
    return avg.toFixed(2);
  }
}