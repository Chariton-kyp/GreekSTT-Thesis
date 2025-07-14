import { Component, Input, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChartModule } from 'primeng/chart';
import { ThemeService } from '../../../core/services/theme.service';

interface ModelPerformanceData {
  whisper: {
    accuracy: number;
    wer: number;
    processingTime: number;
    usage: number;
  };
  wav2vec2: {
    accuracy: number;
    wer: number;
    processingTime: number;
    usage: number;
  };
}

@Component({
  selector: 'app-model-performance-chart',
  standalone: true,
  imports: [CommonModule, ChartModule],
  template: `
    <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
      <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">
        Σύγκριση Επίδοσης Μοντέλων
      </h3>
      <div class="h-64">
        <p-chart type="bar" [data]="chartData()" [options]="chartOptions()"></p-chart>
      </div>
      <div class="mt-4 grid grid-cols-2 gap-4 text-sm">
        <div class="flex items-center">
          <div class="w-4 h-4 bg-blue-500 rounded mr-2"></div>
          <span class="text-gray-600 dark:text-gray-400">Whisper</span>
        </div>
        <div class="flex items-center">
          <div class="w-4 h-4 bg-green-500 rounded mr-2"></div>
          <span class="text-gray-600 dark:text-gray-400">wav2vec2</span>
        </div>
      </div>
    </div>
  `
})
export class ModelPerformanceChartComponent {
  @Input() data: ModelPerformanceData | null = null;
  private readonly themeService = inject(ThemeService);
  
  readonly chartData = computed(() => {
    if (!this.data) {
      return {
        labels: ['Ακρίβεια (%)', 'WER (%)', 'Χρόνος (s)', 'Χρήση (%)'],
        datasets: []
      };
    }

    return {
      labels: ['Ακρίβεια (%)', 'WER (%)', 'Χρόνος (s)', 'Χρήση (%)'],
      datasets: [
        {
          label: 'Whisper',
          backgroundColor: 'rgba(59, 130, 246, 0.8)',
          borderColor: 'rgb(59, 130, 246)',
          borderWidth: 1,
          hoverBackgroundColor: 'rgba(59, 130, 246, 0.9)',
          hoverBorderColor: 'rgb(59, 130, 246)',
          hoverBorderWidth: 2,
          data: [
            this.data.whisper.accuracy,
            this.data.whisper.wer,
            this.data.whisper.processingTime,
            this.data.whisper.usage
          ]
        },
        {
          label: 'wav2vec2',
          backgroundColor: 'rgba(34, 197, 94, 0.8)',
          borderColor: 'rgb(34, 197, 94)',
          borderWidth: 1,
          hoverBackgroundColor: 'rgba(34, 197, 94, 0.9)',
          hoverBorderColor: 'rgb(34, 197, 94)',
          hoverBorderWidth: 2,
          data: [
            this.data.wav2vec2.accuracy,
            this.data.wav2vec2.wer,
            this.data.wav2vec2.processingTime,
            this.data.wav2vec2.usage
          ]
        }
      ]
    };
  });
  
  readonly chartOptions = computed(() => {
    const isDark = this.themeService.isDarkMode();
    const textColor = isDark ? '#f9fafb' : '#374151';
    const gridColor = isDark ? 'rgba(156, 163, 175, 0.5)' : 'rgba(156, 163, 175, 0.3)';

    return {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'nearest',
        intersect: false
      },
      hover: {
        mode: 'nearest',
        intersect: false,
        animationDuration: 200
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: (context: any) => {
              const label = context.dataset.label || '';
              const value = context.parsed.y || 0;
              const dataIndex = context.dataIndex;
              
              // Format based on data type
              if (dataIndex === 0 || dataIndex === 3) {
                return `${label}: ${value.toFixed(1)}%`;
              } else if (dataIndex === 1) {
                return `${label}: ${value.toFixed(2)}%`;
              } else {
                return `${label}: ${value.toFixed(2)}s`;
              }
            }
          }
        }
      },
      scales: {
        x: {
          grid: {
            display: false
          },
          ticks: {
            color: textColor
          }
        },
        y: {
          beginAtZero: true,
          grid: {
            color: gridColor
          },
          ticks: {
            color: textColor
          }
        }
      }
    };
  });
}