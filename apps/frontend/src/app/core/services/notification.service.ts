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

  clear(key?: string): void {
    this.messageService.clear(key);
  }

  authSuccess(action: 'login' | 'register' | 'logout'): void {
    const messages = {
      login: 'Συνδεθήκατε επιτυχώς',
      register: 'Εγγραφήκατε επιτυχώς',
      logout: 'Αποσυνδεθήκατε επιτυχώς',
    };
    this.success(messages[action]);
  }

  authError(error: string): void {
    this.error('Σφάλμα ταυτοποίησης', error);
  }

  uploadSuccess(filename: string): void {
    this.success('Επιτυχής μεταφόρτωση', `Το αρχείο "${filename}" μεταφορτώθηκε επιτυχώς`);
  }

  uploadError(error: string): void {
    this.error('Σφάλμα μεταφόρτωσης', error);
  }

  transcriptionCompleted(): void {
    this.success('Μεταγραφή ολοκληρώθηκε', 'Η μεταγραφή του αρχείου σας ολοκληρώθηκε επιτυχώς');
  }

  transcriptionError(error: string): void {
    this.error('Σφάλμα μεταγραφής', error);
  }

  profileUpdateSuccess(): void {
    this.success('Προφίλ ενημερώθηκε', 'Τα στοιχεία του προφίλ σας ενημερώθηκαν επιτυχώς');
  }

  passwordChangeSuccess(): void {
    this.success('Κωδικός άλλαξε', 'Ο κωδικός σας άλλαξε επιτυχώς');
  }

  networkError(): void {
    this.error('Σφάλμα δικτύου', 'Παρουσιάστηκε πρόβλημα σύνδεσης. Παρακαλώ δοκιμάστε ξανά');
  }

  validationError(errors: string[]): void {
    const detail = errors.join(', ');
    this.error('Σφάλμα επικύρωσης', detail);
  }

  sessionExpired(): void {
    this.warning('Η συνεδρία έληξε', 'Παρακαλώ συνδεθείτε ξανά');
  }

  maintenanceMode(): void {
    this.info('Λειτουργία συντήρησης', 'Η υπηρεσία βρίσκεται σε λειτουργία συντήρησης');
  }

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
