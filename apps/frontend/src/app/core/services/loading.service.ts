import { Injectable, signal, computed } from '@angular/core';

export interface LoadingState {
  isLoading: boolean;
  message?: string;
  progress?: number;
}

@Injectable({
  providedIn: 'root'
})
export class LoadingService {
  // Private writable signals
  private _globalLoading = signal<boolean>(false);
  private _loadingMessage = signal<string>('');
  private _loadingProgress = signal<number>(0);
  private _loadingStates = signal<Map<string, LoadingState>>(new Map());

  // Public readonly signals
  readonly isGlobalLoading = this._globalLoading.asReadonly();
  readonly loadingMessage = this._loadingMessage.asReadonly();
  readonly loadingProgress = this._loadingProgress.asReadonly();

  // Computed signals
  readonly hasAnyLoading = computed(() => {
    const states = this._loadingStates();
    return this.isGlobalLoading() || Array.from(states.values()).some(state => state.isLoading);
  });

  readonly loadingCount = computed(() => {
    const states = this._loadingStates();
    let count = this.isGlobalLoading() ? 1 : 0;
    count += Array.from(states.values()).filter(state => state.isLoading).length;
    return count;
  });

  constructor() {}

  /**
   * Show global loading
   */
  showGlobal(message: string = 'Φόρτωση...', progress?: number): void {
    this._globalLoading.set(true);
    this._loadingMessage.set(message);
    if (progress !== undefined) {
      this._loadingProgress.set(progress);
    }
  }

  /**
   * Hide global loading
   */
  hideGlobal(): void {
    this._globalLoading.set(false);
    this._loadingMessage.set('');
    this._loadingProgress.set(0);
  }

  /**
   * Update global loading progress
   */
  updateGlobalProgress(progress: number, message?: string): void {
    this._loadingProgress.set(Math.max(0, Math.min(100, progress)));
    if (message) {
      this._loadingMessage.set(message);
    }
  }

  /**
   * Show loading for specific key
   */
  show(key: string, message: string = 'Φόρτωση...', progress?: number): void {
    this._loadingStates.update(states => {
      const newStates = new Map(states);
      newStates.set(key, {
        isLoading: true,
        message,
        progress
      });
      return newStates;
    });
  }

  /**
   * Hide loading for specific key
   */
  hide(key: string): void {
    this._loadingStates.update(states => {
      const newStates = new Map(states);
      newStates.delete(key);
      return newStates;
    });
  }

  /**
   * Update loading progress for specific key
   */
  updateProgress(key: string, progress: number, message?: string): void {
    this._loadingStates.update(states => {
      const newStates = new Map(states);
      const existingState = newStates.get(key);
      if (existingState) {
        newStates.set(key, {
          ...existingState,
          progress: Math.max(0, Math.min(100, progress)),
          message: message || existingState.message
        });
      }
      return newStates;
    });
  }

  /**
   * Check if specific key is loading
   */
  isLoading(key: string): boolean {
    return this._loadingStates().get(key)?.isLoading || false;
  }

  /**
   * Get loading state for specific key
   */
  getLoadingState(key: string): LoadingState | undefined {
    return this._loadingStates().get(key);
  }

  /**
   * Clear all loading states
   */
  clearAll(): void {
    this._globalLoading.set(false);
    this._loadingMessage.set('');
    this._loadingProgress.set(0);
    this._loadingStates.set(new Map());
  }

  /**
   * Show authentication loading
   */
  showAuth(action: 'login' | 'register' | 'logout' | 'refresh'): void {
    const messages = {
      login: 'Σύνδεση...',
      register: 'Εγγραφή...',
      logout: 'Αποσύνδεση...',
      refresh: 'Ανανέωση...'
    };
    this.show('auth', messages[action]);
  }

  /**
   * Hide authentication loading
   */
  hideAuth(): void {
    this.hide('auth');
  }

  /**
   * Show file upload loading
   */
  showUpload(filename: string, progress?: number): void {
    const message = `Μεταφόρτωση: ${filename}`;
    this.show('upload', message, progress);
  }

  /**
   * Update file upload progress
   */
  updateUploadProgress(progress: number): void {
    this.updateProgress('upload', progress);
  }

  /**
   * Hide file upload loading
   */
  hideUpload(): void {
    this.hide('upload');
  }

  /**
   * Show transcription loading
   */
  showTranscription(filename?: string): void {
    const message = filename ? `Μεταγραφή: ${filename}` : 'Επεξεργασία μεταγραφής...';
    this.show('transcription', message);
  }

  /**
   * Update transcription progress
   */
  updateTranscriptionProgress(progress: number, status?: string): void {
    const message = status ? `Μεταγραφή: ${status}` : undefined;
    this.updateProgress('transcription', progress, message);
  }

  /**
   * Hide transcription loading
   */
  hideTranscription(): void {
    this.hide('transcription');
  }

  /**
   * Show data loading
   */
  showData(type: string): void {
    const messages: Record<string, string> = {
      dashboard: 'Φόρτωση πίνακα ελέγχου...',
      transcriptions: 'Φόρτωση μεταγραφών...',
      profile: 'Φόρτωση προφίλ...',
      templates: 'Φόρτωση προτύπων...',
      usage: 'Φόρτωση στατιστικών...'
    };
    this.show(`data-${type}`, messages[type] || `Φόρτωση ${type}...`);
  }

  /**
   * Hide data loading
   */
  hideData(type: string): void {
    this.hide(`data-${type}`);
  }

  /**
   * Show save loading
   */
  showSave(type: string = ''): void {
    const message = type ? `Αποθήκευση ${type}...` : 'Αποθήκευση...';
    this.show('save', message);
  }

  /**
   * Hide save loading
   */
  hideSave(): void {
    this.hide('save');
  }
}