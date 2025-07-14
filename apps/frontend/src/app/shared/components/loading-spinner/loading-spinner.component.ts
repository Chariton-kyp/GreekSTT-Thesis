import { CommonModule } from '@angular/common';
import { Component, Input, inject, ChangeDetectionStrategy } from '@angular/core';

import { ProgressSpinnerModule } from 'primeng/progressspinner';

import { LoadingService } from '../../../core/services/loading.service';

@Component({
  selector: 'app-loading-spinner',
  standalone: true,
  imports: [CommonModule, ProgressSpinnerModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './loading-spinner.component.html',
  styles: [`
    .loading-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 9999;
    }

    .loading-overlay.global {
      background: var(--bg-primary);
    }

    .loading-content {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1rem;
      padding: 2rem;
      background: var(--bg-secondary);
      border-radius: 8px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
      min-width: 200px;
    }

    .loading-message {
      margin: 0;
      color: var(--text-primary);
      font-size: 0.9rem;
      text-align: center;
    }

    .loading-progress {
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .progress-bar {
      width: 100%;
      height: 6px;
      background: var(--border-color);
      border-radius: 3px;
      overflow: hidden;
    }

    .progress-fill {
      height: 100%;
      background: var(--accent-primary);
      transition: width 0.3s ease;
    }

    .progress-text {
      font-size: 0.8rem;
      color: var(--text-secondary);
      text-align: center;
    }

    /* Dark mode styles */
    :host-context(.dark) .loading-overlay {
      background: rgba(15, 23, 42, 0.8);
    }

    :host-context(.dark) .loading-content {
      background: var(--dark-bg-secondary);
    }

    /* Light mode styles */
    :host-context(.light) .loading-overlay {
      background: rgba(255, 255, 255, 0.8);
    }

    :host-context(.light) .loading-content {
      background: var(--light-bg-primary);
      border: 1px solid var(--light-border);
    }
  `]
})
export class LoadingSpinnerComponent {
  @Input() isGlobal: boolean = false;
  @Input() size: string = '50px';
  @Input() showProgress: boolean = true;

  private readonly loadingService = inject(LoadingService);

  // Computed properties for reactive display
  isVisible = this.loadingService.isGlobalLoading;
  message = this.loadingService.loadingMessage;
  progress = this.loadingService.loadingProgress;
}