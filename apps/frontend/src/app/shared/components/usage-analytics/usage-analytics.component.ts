import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChartModule } from 'primeng/chart';

interface UsageAnalyticsData {
  peakHours: { hour: number; count: number }[];
  popularFormats: { format: string; count: number; percentage: number }[];
  errorRates: {
    whisper: number;
    wav2vec2: number;
    comparison: number;
  };
  avgProcessingTime: {
    whisper: number;
    wav2vec2: number;
  };
  werCerMetrics?: {
    whisperWER: number;
    wav2vec2WER: number;
    whisperCER: number;
    wav2vec2CER: number;
    transcriptionsWithGroundTruth: number;
  };
}

@Component({
  selector: 'app-usage-analytics',
  standalone: true,
  imports: [CommonModule, ChartModule],
  template: `
    <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
      <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">
        Αναλυτικά Χρήσης
      </h3>
      
      @if (data) {
        <!-- Peak Usage Hours -->
        <div class="mb-6">
          <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Ώρες Αιχμής
          </h4>
          <div class="space-y-2">
            @for (hour of getTopPeakHours(); track hour.hour) {
              <div class="flex items-center">
                <span class="text-xs text-gray-600 dark:text-gray-400 w-16">
                  {{ formatHour(hour.hour) }}
                </span>
                <div class="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2 mr-2">
                  <div 
                    class="bg-cyan-500 h-2 rounded-full"
                    [style.width.%]="(hour.count / getMaxCount()) * 100"
                  ></div>
                </div>
                <span class="text-xs text-gray-600 dark:text-gray-400 w-8 text-right">
                  {{ hour.count }}
                </span>
              </div>
            }
          </div>
        </div>

        <!-- Popular Audio Formats -->
        <div class="mb-6">
          <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Δημοφιλείς Μορφές Αρχείων
          </h4>
          <div class="space-y-2">
            @for (format of data.popularFormats; track format.format) {
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-400">
                  {{ format.format.toUpperCase() }}
                </span>
                <span class="text-sm font-medium text-gray-900 dark:text-white">
                  {{ format.percentage }}%
                </span>
              </div>
            }
          </div>
        </div>

        <!-- Error Rates -->
        <div class="mb-6">
          <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Ποσοστά Σφαλμάτων
          </h4>
          <p class="text-xs text-gray-500 dark:text-gray-400 mb-3">
            (Μεταγραφές που δεν ολοκληρώθηκαν λόγω τεχνικού σφάλματος)
          </p>
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600 dark:text-gray-400">Whisper</span>
              <span class="text-sm font-medium" [class]="getErrorClass(data.errorRates.whisper)">
                {{ data.errorRates.whisper }}%
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600 dark:text-gray-400">wav2vec2</span>
              <span class="text-sm font-medium" [class]="getErrorClass(data.errorRates.wav2vec2)">
                {{ data.errorRates.wav2vec2 }}%
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600 dark:text-gray-400">Σύγκριση</span>
              <span class="text-sm font-medium" [class]="getErrorClass(data.errorRates.comparison)">
                {{ data.errorRates.comparison }}%
              </span>
            </div>
          </div>
        </div>

        <!-- WER/CER Accuracy Metrics (only if ground truth data exists) -->
        @if (data.werCerMetrics && data.werCerMetrics.transcriptionsWithGroundTruth > 0) {
          <div class="mb-6">
            <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Μετρικές Ακρίβειας (WER/CER)
            </h4>
            <p class="text-xs text-gray-500 dark:text-gray-400 mb-3">
              (Βάσει {{ data.werCerMetrics.transcriptionsWithGroundTruth }} μεταγραφών με ακριβή κείμενο)
            </p>
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-400">Whisper WER</span>
                <span class="text-sm font-medium text-gray-900 dark:text-white">
                  {{ data.werCerMetrics.whisperWER.toFixed(1) }}%
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-400">wav2vec2 WER</span>
                <span class="text-sm font-medium text-gray-900 dark:text-white">
                  {{ data.werCerMetrics.wav2vec2WER.toFixed(1) }}%
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-400">Whisper CER</span>
                <span class="text-sm font-medium text-gray-900 dark:text-white">
                  {{ data.werCerMetrics.whisperCER.toFixed(1) }}%
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-400">wav2vec2 CER</span>
                <span class="text-sm font-medium text-gray-900 dark:text-white">
                  {{ data.werCerMetrics.wav2vec2CER.toFixed(1) }}%
                </span>
              </div>
            </div>
          </div>
        }

        <!-- Average Processing Time -->
        <div>
          <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Μέσος Χρόνος Επεξεργασίας
          </h4>
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600 dark:text-gray-400">Whisper</span>
              <span class="text-sm font-medium text-gray-900 dark:text-white">
                {{ data.avgProcessingTime.whisper.toFixed(2) }}s
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600 dark:text-gray-400">wav2vec2</span>
              <span class="text-sm font-medium text-gray-900 dark:text-white">
                {{ data.avgProcessingTime.wav2vec2.toFixed(2) }}s
              </span>
            </div>
          </div>
        </div>
      }
    </div>
  `
})
export class UsageAnalyticsComponent {
  @Input() data: UsageAnalyticsData | null = null;

  getTopPeakHours(): { hour: number; count: number }[] {
    if (!this.data?.peakHours) return [];
    return this.data.peakHours
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);
  }

  getMaxCount(): number {
    if (!this.data?.peakHours) return 1;
    return Math.max(...this.data.peakHours.map(h => h.count)) || 1;
  }

  formatHour(hour: number): string {
    const period = hour >= 12 ? 'μμ' : 'πμ';
    const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
    return `${displayHour}:00 ${period}`;
  }

  getErrorClass(errorRate: number): string {
    if (errorRate >= 10) return 'text-red-600 dark:text-red-400';
    if (errorRate >= 5) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-green-600 dark:text-green-400';
  }
}