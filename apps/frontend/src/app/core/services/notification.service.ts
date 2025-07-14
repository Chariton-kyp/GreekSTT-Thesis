import { Injectable, inject } from '@angular/core';

import { MessageService } from 'primeng/api';

export interface NotificationOptions {
  life?: number; // Duration in ms
  sticky?: boolean;
  closable?: boolean;
  key?: string;
}

@Injectable({
  providedIn: 'root',
})
export class NotificationService {
  private readonly messageService = inject(MessageService);

  constructor() {}

  /**
   * Show success notification
   */
  success(message: string, detail?: string, options: NotificationOptions = {}): void {
    this.messageService.add({
      severity: 'success',
      summary: message,
      detail: detail,
      life: options.life || 5000,
      sticky: options.sticky || false,
      closable: options.closable !== false,
      key: options.key
    });
  }

  /**
   * Show error notification
   */
  error(message: string, detail?: string, options: NotificationOptions = {}): void {
    this.messageService.add({
      severity: 'error',
      summary: message,
      detail: detail,
      life: options.life || 8000,
      sticky: options.sticky || false,
      closable: options.closable !== false,
      key: options.key
    });
  }

  /**
   * Show warning notification
   */
  warning(message: string, detail?: string, options: NotificationOptions = {}): void {
    this.messageService.add({
      severity: 'warn',
      summary: message,
      detail: detail,
      life: options.life || 6000,
      sticky: options.sticky || false,
      closable: options.closable !== false,
      key: options.key
    });
  }

  /**
   * Show info notification
   */
  info(message: string, detail?: string, options: NotificationOptions = {}): void {
    this.messageService.add({
      severity: 'info',
      summary: message,
      detail: detail,
      life: options.life || 5000,
      sticky: options.sticky || false,
      closable: options.closable !== false,
      key: options.key
    });
  }

  /**
   * Show custom notification
   */
  custom(
    severity: 'success' | 'info' | 'warn' | 'error',
    message: string,
    detail?: string,
    options: NotificationOptions = {}
  ): void {
    this.messageService.add({
      severity: severity,
      summary: message,
      detail: detail,
      life: options.life || 5000,
      sticky: options.sticky || false,
      closable: options.closable !== false,
      key: options.key
    });
  }

  /**
   * Clear all notifications
   */
  clear(key?: string): void {
    this.messageService.clear(key);
  }

  /**
   * Show authentication success message
   */
  authSuccess(action: 'login' | 'register' | 'logout'): void {
    const messages = {
      login: 'Συνδεθήκατε επιτυχώς',
      register: 'Εγγραφήκατε επιτυχώς',
      logout: 'Αποσυνδεθήκατε επιτυχώς',
    };
    this.success(messages[action]);
  }

  /**
   * Show authentication error message
   */
  authError(error: string): void {
    this.error('Σφάλμα ταυτοποίησης', error);
  }

  /**
   * Show file upload success message
   */
  uploadSuccess(filename: string): void {
    this.success('Επιτυχής μεταφόρτωση', `Το αρχείο "${filename}" μεταφορτώθηκε επιτυχώς`);
  }

  /**
   * Show file upload error message
   */
  uploadError(error: string): void {
    this.error('Σφάλμα μεταφόρτωσης', error);
  }

  /**
   * Show transcription completed message
   */
  transcriptionCompleted(): void {
    this.success('Μεταγραφή ολοκληρώθηκε', 'Η μεταγραφή του αρχείου σας ολοκληρώθηκε επιτυχώς');
  }

  /**
   * Show transcription error message
   */
  transcriptionError(error: string): void {
    this.error('Σφάλμα μεταγραφής', error);
  }

  /**
   * Show profile update success message
   */
  profileUpdateSuccess(): void {
    this.success('Προφίλ ενημερώθηκε', 'Τα στοιχεία του προφίλ σας ενημερώθηκαν επιτυχώς');
  }

  /**
   * Show password change success message
   */
  passwordChangeSuccess(): void {
    this.success('Κωδικός άλλαξε', 'Ο κωδικός σας άλλαξε επιτυχώς');
  }

  /**
   * Show network error message
   */
  networkError(): void {
    this.error('Σφάλμα δικτύου', 'Παρουσιάστηκε πρόβλημα σύνδεσης. Παρακαλώ δοκιμάστε ξανά');
  }

  /**
   * Show validation error message
   */
  validationError(errors: string[]): void {
    const detail = errors.join(', ');
    this.error('Σφάλμα επικύρωσης', detail);
  }

  /**
   * Show session expired message
   */
  sessionExpired(): void {
    this.warning('Η συνεδρία έληξε', 'Παρακαλώ συνδεθείτε ξανά');
  }

  /**
   * Show maintenance mode message
   */
  maintenanceMode(): void {
    this.info('Λειτουργία συντήρησης', 'Η υπηρεσία βρίσκεται σε λειτουργία συντήρησης');
  }

  /**
   * Alias methods for compatibility
   */
  showSuccess(message: string, detail?: string, options?: NotificationOptions): void {
    this.success(message, detail, options);
  }

  showError(message: string, detail?: string, options?: NotificationOptions): void {
    this.error(message, detail, options);
  }

  showWarning(message: string, detail?: string, options?: NotificationOptions): void {
    this.warning(message, detail, options);
  }

  showInfo(message: string, detail?: string, options?: NotificationOptions): void {
    this.info(message, detail, options);
  }
}
