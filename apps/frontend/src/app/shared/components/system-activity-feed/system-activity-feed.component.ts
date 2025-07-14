import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { GreekDatePipe } from '../../pipes/greek-date.pipe';

interface SystemActivity {
  id: string;
  type: 'transcription' | 'user' | 'system' | 'error';
  action: string;
  user?: string;
  details: string;
  timestamp: string;
  severity?: 'info' | 'warning' | 'error' | 'success';
}

@Component({
  selector: 'app-system-activity-feed',
  standalone: true,
  imports: [CommonModule, GreekDatePipe],
  template: `
    <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">
          Πρόσφατη Δραστηριότητα Συστήματος
        </h3>
        <span class="text-sm text-gray-500 dark:text-gray-400">
          Τελευταίες 24 ώρες
        </span>
      </div>
      
      @if (activities && activities.length > 0) {
        <div class="flow-root">
          <ul role="list" class="-mb-8">
            @for (activity of activities; track activity.id; let isLast = $last) {
              <li>
                <div class="relative pb-8">
                  @if (!isLast) {
                    <span class="absolute left-4 top-4 -ml-px h-full w-0.5 bg-gray-200 dark:bg-gray-700" aria-hidden="true"></span>
                  }
                  
                  <div class="relative flex space-x-3">
                    <div>
                      <span class="h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white dark:ring-gray-800"
                            [ngClass]="getActivityIconClass(activity)">
                        <span class="text-white text-xs">{{ getActivityIcon(activity) }}</span>
                      </span>
                    </div>
                    
                    <div class="flex min-w-0 flex-1 justify-between space-x-4 pt-1.5">
                      <div>
                        <p class="text-sm text-gray-900 dark:text-gray-100">
                          {{ activity.action }}
                          @if (activity.user) {
                            <span class="font-medium">{{ activity.user }}</span>
                          }
                        </p>
                        <p class="mt-0.5 text-sm text-gray-500 dark:text-gray-400">
                          {{ activity.details }}
                        </p>
                      </div>
                      <div class="whitespace-nowrap text-right text-sm text-gray-500 dark:text-gray-400">
                        <time [dateTime]="activity.timestamp">
                          {{ activity.timestamp | greekDate:'relative' }}
                        </time>
                      </div>
                    </div>
                  </div>
                </div>
              </li>
            }
          </ul>
        </div>
      } @else {
        <div class="text-center py-6 text-gray-500 dark:text-gray-400">
          <p>Δεν υπάρχει πρόσφατη δραστηριότητα</p>
        </div>
      }
    </div>
  `
})
export class SystemActivityFeedComponent {
  @Input() activities: SystemActivity[] = [];

  getActivityIcon(activity: SystemActivity): string {
    switch (activity.type) {
      case 'transcription':
        return '🎙️';
      case 'user':
        return '👤';
      case 'system':
        return '⚙️';
      case 'error':
        return '⚠️';
      default:
        return '📌';
    }
  }

  getActivityIconClass(activity: SystemActivity): string {
    const baseClasses = 'h-8 w-8 rounded-full flex items-center justify-center';
    
    switch (activity.severity || activity.type) {
      case 'success':
      case 'transcription':
        return `${baseClasses} bg-green-500`;
      case 'warning':
        return `${baseClasses} bg-yellow-500`;
      case 'error':
        return `${baseClasses} bg-red-500`;
      case 'user':
        return `${baseClasses} bg-blue-500`;
      case 'system':
        return `${baseClasses} bg-purple-500`;
      default:
        return `${baseClasses} bg-gray-500`;
    }
  }
}