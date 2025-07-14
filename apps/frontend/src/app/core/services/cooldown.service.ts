import { Injectable, signal, inject, WritableSignal, Signal } from '@angular/core';
import { StorageService } from './storage.service';

export interface CooldownState {
  key: string;
  expiresAt: number;
  duration: number;
  isActive: boolean;
  remainingSeconds: number;
}

@Injectable({
  providedIn: 'root'
})
export class CooldownService {
  private readonly storage = inject(StorageService);
  
  // Active timers map
  private readonly activeTimers = new Map<string, ReturnType<typeof setInterval>>();
  
  // Signals for each cooldown type
  private readonly cooldownSignals = new Map<string, WritableSignal<number>>();

  /**
   * Start a cooldown timer for a specific action
   */
  startCooldown(key: string, durationSeconds: number): void {
    const expiresAt = Date.now() + (durationSeconds * 1000);
    
    // Store in localStorage with expiration
    this.storage.setItem(`cooldown_${key}`, {
      expiresAt,
      duration: durationSeconds,
      startedAt: Date.now()
    });
    
    // Create or update signal for this cooldown
    if (!this.cooldownSignals.has(key)) {
      this.cooldownSignals.set(key, signal(durationSeconds));
    }
    
    const cooldownSignal = this.cooldownSignals.get(key);
    if (cooldownSignal) {
      cooldownSignal.set(durationSeconds);
    }
    
    // Clear existing timer if any
    this.clearTimer(key);
    
    // Start countdown
    const timer = setInterval(() => {
      const remaining = this.getRemainingSeconds(key);
      const signal = this.cooldownSignals.get(key);
      if (signal) {
        signal.set(remaining);
      }
      
      if (remaining <= 0) {
        this.clearCooldown(key);
      }
    }, 1000);
    
    this.activeTimers.set(key, timer);
  }

  /**
   * Get remaining seconds for a cooldown
   */
  getRemainingSeconds(key: string): number {
    const cooldownData = this.storage.getItem<any>(`cooldown_${key}`);
    
    if (!cooldownData) return 0;
    
    const now = Date.now();
    const remaining = Math.max(0, Math.ceil((cooldownData.expiresAt - now) / 1000));
    
    // Auto-clear if expired
    if (remaining <= 0) {
      this.clearCooldown(key);
      return 0;
    }
    
    return remaining;
  }

  /**
   * Check if a cooldown is active
   */
  isCooldownActive(key: string): boolean {
    return this.getRemainingSeconds(key) > 0;
  }

  /**
   * Get cooldown signal for reactive UI updates
   */
  getCooldownSignal(key: string): Signal<number> {
    if (!this.cooldownSignals.has(key)) {
      // Initialize with current remaining time
      const remaining = this.getRemainingSeconds(key);
      const cooldownSignal = signal(remaining);
      this.cooldownSignals.set(key, cooldownSignal);
      
      // Start timer if cooldown is active
      if (remaining > 0) {
        this.resumeCooldown(key);
      }
    }
    
    return this.cooldownSignals.get(key)!.asReadonly();
  }

  /**
   * Resume cooldown timer after page refresh
   */
  private resumeCooldown(key: string): void {
    const remaining = this.getRemainingSeconds(key);
    if (remaining <= 0) return;
    
    const cooldownSignal = this.cooldownSignals.get(key);
    if (!cooldownSignal) return;
    
    // Clear existing timer
    this.clearTimer(key);
    
    // Start new timer
    const timer = setInterval(() => {
      const currentRemaining = this.getRemainingSeconds(key);
      const signal = this.cooldownSignals.get(key);
      if (signal) {
        signal.set(currentRemaining);
      }
      
      if (currentRemaining <= 0) {
        this.clearCooldown(key);
      }
    }, 1000);
    
    this.activeTimers.set(key, timer);
  }

  /**
   * Clear a specific cooldown
   */
  clearCooldown(key: string): void {
    // Remove from storage
    this.storage.removeItem(`cooldown_${key}`);
    
    // Clear timer
    this.clearTimer(key);
    
    // Reset signal
    const cooldownSignal = this.cooldownSignals.get(key);
    if (cooldownSignal) {
      cooldownSignal.set(0);
    }
  }

  /**
   * Clear timer only (not storage)
   */
  private clearTimer(key: string): void {
    const timer = this.activeTimers.get(key);
    if (timer) {
      clearInterval(timer);
      this.activeTimers.delete(key);
    }
  }

  /**
   * Get cooldown state for debugging/display
   */
  getCooldownState(key: string): CooldownState {
    const cooldownData = this.storage.getItem<any>(`cooldown_${key}`);
    const remainingSeconds = this.getRemainingSeconds(key);
    
    return {
      key,
      expiresAt: cooldownData?.expiresAt || 0,
      duration: cooldownData?.duration || 0,
      isActive: remainingSeconds > 0,
      remainingSeconds
    };
  }

  /**
   * Format remaining time as human-readable string
   */
  formatCooldown(seconds: number): string {
    if (seconds <= 0) return '';
    
    if (seconds >= 60) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      if (remainingSeconds === 0) {
        return `${minutes}λ`;
      }
      return `${minutes}λ ${remainingSeconds}δ`;
    }
    return `${seconds}δ`;
  }

  /**
   * Cleanup all timers (call on service destroy)
   */
  cleanup(): void {
    this.activeTimers.forEach(timer => clearInterval(timer));
    this.activeTimers.clear();
  }

  /**
   * Initialize cooldowns on service startup
   */
  initializeCooldowns(): void {
    // Common cooldown keys that might exist
    const commonKeys = [
      'email_verification_resend',
      'password_reset_resend',
      'login_attempt',
      'registration_attempt'
    ];
    
    commonKeys.forEach(key => {
      const remaining = this.getRemainingSeconds(key);
      if (remaining > 0) {
        // Resume existing cooldown
        this.getCooldownSignal(key); // This will trigger resumeCooldown
      }
    });
  }
}