import { Component, Input, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { Transcription } from '../../../core/models/transcription.model';
import { StatusBadgeComponent } from '../status-badge/status-badge.component';
import { DurationPipe } from '../../pipes/duration.pipe';
import { FileSizePipe } from '../../pipes/file-size.pipe';
import { GreekDatePipe } from '../../pipes/greek-date.pipe';

@Component({
  selector: 'app-enhanced-recent-transcriptions',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    StatusBadgeComponent,
    DurationPipe,
    FileSizePipe,
    GreekDatePipe
  ],
  template: `
    <div class="bg-white dark:bg-gray-800 shadow rounded-lg">
      <div class="px-4 py-5 sm:px-6 border-b border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg leading-6 font-medium text-gray-900 dark:text-white">
              Πρόσφατες Μεταγραφές
            </h3>
            <p class="mt-1 max-w-2xl text-sm text-gray-500 dark:text-gray-400">
              Οι τελευταίες μεταγραφές σας με γρήγορες ενέργειες
            </p>
          </div>
          <div class="flex items-center space-x-3">
            <a
              routerLink="/app/transcriptions"
              class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-cyan-600 hover:bg-cyan-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-cyan-500 transition-colors duration-200"
            >
              <svg class="-ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
              Νέα Μεταγραφή
            </a>
            <a 
              routerLink="/app/transcriptions"
              class="text-sm font-medium text-cyan-600 dark:text-cyan-400 hover:text-cyan-500 dark:hover:text-cyan-300"
            >
              Προβολή όλων →
            </a>
          </div>
        </div>
      </div>

      @if (transcriptions && transcriptions.length > 0) {
        <div class="divide-y divide-gray-200 dark:divide-gray-700">
          @for (transcription of transcriptions; track transcription.id) {
            <div class="p-4 sm:px-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors duration-150">
              <div class="flex items-center justify-between">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center">
                    <app-status-badge [status]="transcription.status"></app-status-badge>
                    <h4 class="ml-3 text-sm font-medium text-gray-900 dark:text-white truncate">
                      {{ transcription.title }}
                    </h4>
                  </div>
                  
                  <div class="mt-2 flex items-center text-sm text-gray-500 dark:text-gray-400">
                    <span class="flex items-center">
                      <svg class="mr-1.5 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      {{ transcription.duration_seconds | duration }}
                    </span>
                    
                    <span class="mx-2">•</span>
                    
                    <span class="flex items-center">
                      <svg class="mr-1.5 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      {{ transcription.audio_file?.file_size | fileSize }}
                    </span>
                    
                    <span class="mx-2">•</span>
                    
                    <span>{{ transcription.created_at | greekDate:'short' }}</span>
                    
                    @if (transcription.model_used) {
                      <span class="mx-2">•</span>
                      <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
                        {{ getModelDisplayName(transcription.model_used) }}
                      </span>
                    }

                    @if (transcription.has_evaluation || transcription.evaluation_completed) {
                      <span class="mx-2">•</span>
                      <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300" 
                            title="Έχει αξιολογηθεί με ground truth">
                        <svg class="mr-1 h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                        </svg>
                        Αξιολογημένο
                      </span>
                    }
                  </div>

                  @if (transcription.transcription_text) {
                    <p class="mt-2 text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                      {{ transcription.transcription_text }}
                    </p>
                  }
                </div>

                <div class="ml-4 flex items-center space-x-2">
                  <button
                    type="button"
                    (click)="viewTranscription(transcription.id)"
                    class="p-2 text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
                    title="Προβολή"
                  >
                    <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          }
        </div>
      } @else {
        <div class="p-6 text-center">
          <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
          </svg>
          <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">
            Δεν υπάρχουν μεταγραφές
          </h3>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Ξεκινήστε δημιουργώντας την πρώτη σας μεταγραφή.
          </p>
          <div class="mt-6">
            <a
              routerLink="/app/transcriptions"
              class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-cyan-600 hover:bg-cyan-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-cyan-500"
            >
              <svg class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
              Νέα Μεταγραφή
            </a>
          </div>
        </div>
      }
    </div>
  `
})
export class EnhancedRecentTranscriptionsComponent {
  @Input() transcriptions: Transcription[] = [];
  
  private readonly router = inject(Router);

  viewTranscription(id: string): void {
    this.router.navigate(['/app/transcriptions', id]);
  }

  compareTranscription(id: string): void {
    this.router.navigate(['/app/transcriptions/compare'], {
      queryParams: { transcriptionId: id }
    });
  }

  downloadTranscription(id: string): void {
    // Download functionality not implemented in academic version
    console.log('Download transcription:', id);
  }

  getModelDisplayName(modelUsed: string | undefined): string {
    if (!modelUsed) return 'Άγνωστο';
    
    switch (modelUsed) {
      case 'whisper':
      case 'faster-whisper':
        return 'Whisper-Large-3';
      case 'wav2vec2':
        return 'wav2vec2-Greek';
      case 'both':
        return 'Σύγκριση Μοντέλων';
      default:
        return modelUsed;
    }
  }
}