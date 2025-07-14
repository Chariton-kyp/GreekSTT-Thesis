import { Component, Input, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChartModule } from 'primeng/chart';
import { ThemeService } from '../../../core/services/theme.service';

@Component({
  selector: 'app-weekly-activity-chart',
  standalone: true,
  imports: [CommonModule, ChartModule],
  template: `
    <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
      <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">
        Εβδομαδιαία Δραστηριότητα
      </h3>
      
      <div class="h-64">
        <p-chart type="bar" [data]="chartData()" [options]="chartOptions()" styleClass="dashboard-chart"></p-chart>
      </div>
      
      <div class="mt-4 flex items-center justify-between text-sm">
        <div>
          <span class="text-gray-500 dark:text-gray-400">Σύνολο:</span>
          <span class="ml-2 font-medium text-gray-900 dark:text-white">
            {{ getTotalActivity() }} μεταγραφές
          </span>
        </div>
        <div>
          <span class="text-gray-500 dark:text-gray-400">Μ.Ο. ημέρας:</span>
          <span class="ml-2 font-medium text-gray-900 dark:text-white">
            {{ getAverageDaily() }}
          </span>
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
export class WeeklyActivityChartComponent {
  @Input() data: { date: string; count: number }[] = [];
  private readonly themeService = inject(ThemeService);

  // Chart data with theme-aware colors - exactly like analytics dashboard
  readonly chartData = computed(() => {
    if (!this.data || this.data.length === 0) {
      return {
        labels: [],
        datasets: []
      };
    }

    const isDark = this.themeService.isDarkMode();
    
    // Theme-aware colors for bar chart - using analytics pattern
    const barColor = isDark ? 'rgb(96, 165, 250)' : 'rgb(59, 130, 246)'; // blue theme

    // Get day names in Greek
    const dayNames = this.data.map(item => {
      const date = new Date(item.date);
      return this.getGreekDayName(date);
    });

    return {
      labels: dayNames,
      datasets: [{
        label: 'Μεταγραφές',
        data: this.data.map(item => item.count),
        backgroundColor: isDark ? 'rgba(96, 165, 250, 0.8)' : 'rgba(59, 130, 246, 0.8)',
        borderColor: barColor,
        borderWidth: 1,
        borderRadius: 4,
        hoverBackgroundColor: isDark ? 'rgba(96, 165, 250, 0.9)' : 'rgba(59, 130, 246, 0.9)',
        hoverBorderColor: barColor,
        hoverBorderWidth: 2
      }]
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
          display: false
        },
        tooltip: {
          callbacks: {
            title: (context: any) => {
              const index = context[0].dataIndex;
              const date = new Date(this.data[index].date);
              return this.formatGreekDate(date);
            },
            label: (context: any) => {
              return `Μεταγραφές: ${context.parsed.y}`;
            }
          }
        }
      },
      scales: {
        x: {
          display: true,
          ticks: {
            color: textColor
          },
          grid: {
            color: gridColor
          }
        },
        y: {
          display: true,
          beginAtZero: true,
          ticks: {
            stepSize: 1,
            color: textColor
          },
          grid: {
            color: gridColor
          }
        }
      }
    };
  });

  getTotalActivity(): number {
    return this.data.reduce((sum, item) => sum + item.count, 0);
  }

  getAverageDaily(): string {
    if (this.data.length === 0) return '0';
    const avg = this.getTotalActivity() / this.data.length;
    return avg.toFixed(1);
  }

  private getGreekDayName(date: Date): string {
    const days = ['Κυρ', 'Δευ', 'Τρί', 'Τετ', 'Πέμ', 'Παρ', 'Σάβ'];
    return days[date.getDay()];
  }

  private formatGreekDate(date: Date): string {
    const months = [
      'Ιανουαρίου', 'Φεβρουαρίου', 'Μαρτίου', 'Απριλίου', 
      'Μαΐου', 'Ιουνίου', 'Ιουλίου', 'Αυγούστου', 
      'Σεπτεμβρίου', 'Οκτωβρίου', 'Νοεμβρίου', 'Δεκεμβρίου'
    ];
    
    return `${date.getDate()} ${months[date.getMonth()]}`;
  }
}