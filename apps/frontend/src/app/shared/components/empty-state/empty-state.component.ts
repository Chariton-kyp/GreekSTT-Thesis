import { CommonModule } from '@angular/common';
import { Component, Input, ChangeDetectionStrategy } from '@angular/core';

import { ButtonModule } from 'primeng/button';

@Component({
  selector: 'app-empty-state',
  standalone: true,
  imports: [CommonModule, ButtonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './empty-state.component.html',
  styles: [`
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 3rem 1.5rem;
      min-height: 300px;
    }

    .empty-icon {
      margin-bottom: 1.5rem;
    }

    .empty-icon i {
      font-size: 4rem;
      color: var(--text-tertiary);
      opacity: 0.6;
    }

    .empty-content {
      margin-bottom: 2rem;
      max-width: 400px;
    }

    .empty-title {
      font-size: 1.25rem;
      font-weight: 600;
      color: var(--text-primary);
      margin: 0 0 0.5rem 0;
    }

    .empty-subtitle {
      font-size: 0.9rem;
      color: var(--text-secondary);
      margin: 0;
      line-height: 1.5;
    }

    .empty-action {
      margin-bottom: 1rem;
    }

    .empty-secondary-action {
      margin-bottom: 0;
    }

    /* Size variants */
    .empty-state.small {
      padding: 2rem 1rem;
      min-height: 200px;
    }

    .empty-state.small .empty-icon i {
      font-size: 3rem;
    }

    .empty-state.small .empty-title {
      font-size: 1.1rem;
    }

    .empty-state.small .empty-subtitle {
      font-size: 0.85rem;
    }

    .empty-state.large {
      padding: 4rem 2rem;
      min-height: 400px;
    }

    .empty-state.large .empty-icon i {
      font-size: 5rem;
    }

    .empty-state.large .empty-title {
      font-size: 1.5rem;
    }

    .empty-state.large .empty-subtitle {
      font-size: 1rem;
    }

    /* Dark mode adjustments */
    :host-context(.dark) .empty-icon i {
      color: var(--dark-text-tertiary);
    }

    :host-context(.dark) .empty-title {
      color: var(--dark-text-primary);
    }

    :host-context(.dark) .empty-subtitle {
      color: var(--dark-text-secondary);
    }

    /* Light mode adjustments */
    :host-context(.light) .empty-icon i {
      color: var(--light-text-tertiary);
    }

    :host-context(.light) .empty-title {
      color: var(--light-text-primary);
    }

    :host-context(.light) .empty-subtitle {
      color: var(--light-text-secondary);
    }
  `],
  host: {
    '[class.small]': 'size === "small"',
    '[class.large]': 'size === "large"'
  }
})
export class EmptyStateComponent {
  @Input() title: string = 'Δεν υπάρχουν δεδομένα';
  @Input() subtitle?: string;
  @Input() iconClass: string = 'pi pi-inbox';
  @Input() size: 'small' | 'medium' | 'large' = 'medium';
  @Input() showAction: boolean = true;
  
  // Primary action
  @Input() actionLabel?: string;
  @Input() actionIcon?: string;
  @Input() actionHandler?: () => void;
  
  // Secondary action
  @Input() secondaryActionLabel?: string;
  @Input() secondaryActionIcon?: string;
  @Input() secondaryActionHandler?: () => void;
}

// Common empty state configurations
export const EMPTY_STATE_CONFIGS = {
  NO_TRANSCRIPTIONS: {
    title: 'Δεν έχετε μεταγραφές',
    subtitle: 'Ξεκινήστε ανεβάζοντας ένα αρχείο ήχου ή βίντεο για μεταγραφή',
    iconClass: 'pi pi-microphone',
    actionLabel: 'Μεταφόρτωση αρχείου',
    actionIcon: 'pi pi-upload'
  },
  NO_FILES: {
    title: 'Δεν έχετε αρχεία',
    subtitle: 'Μεταφορτώστε αρχεία ήχου ή βίντεο για να ξεκινήσετε',
    iconClass: 'pi pi-folder-open',
    actionLabel: 'Μεταφόρτωση',
    actionIcon: 'pi pi-plus'
  },
  NO_TEMPLATES: {
    title: 'Δεν βρέθηκαν πρότυπα',
    subtitle: 'Δημιουργήστε ένα προσαρμοσμένο πρότυπο ή επιλέξτε από τα διαθέσιμα',
    iconClass: 'pi pi-file-o',
    actionLabel: 'Δημιουργία προτύπου',
    actionIcon: 'pi pi-plus'
  },
  SEARCH_NO_RESULTS: {
    title: 'Δεν βρέθηκαν αποτελέσματα',
    subtitle: 'Δοκιμάστε να αλλάξετε τα κριτήρια αναζήτησης',
    iconClass: 'pi pi-search',
    actionLabel: 'Καθαρισμός φίλτρων',
    actionIcon: 'pi pi-times'
  },
  NETWORK_ERROR: {
    title: 'Σφάλμα σύνδεσης',
    subtitle: 'Παρουσιάστηκε πρόβλημα με τη σύνδεση στο διαδίκτυο',
    iconClass: 'pi pi-wifi',
    actionLabel: 'Επανάληψη',
    actionIcon: 'pi pi-refresh'
  },
  LOADING_ERROR: {
    title: 'Σφάλμα φόρτωσης',
    subtitle: 'Δεν ήταν δυνατή η φόρτωση των δεδομένων',
    iconClass: 'pi pi-exclamation-triangle',
    actionLabel: 'Επανάληψη',
    actionIcon: 'pi pi-refresh'
  }
};