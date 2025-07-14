import { isPlatformBrowser } from '@angular/common';
import { Injectable, PLATFORM_ID, inject } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class StorageService {
  private readonly PREFIX = 'greekstt-research_';
  private readonly platformId = inject(PLATFORM_ID);
  private readonly isBrowser = isPlatformBrowser(this.platformId);

  constructor() {}

  /**
   * Get item from localStorage with type safety
   */
  getItem<T>(key: string): T | null {
    if (!this.isBrowser) {
      return null;
    }
    try {
      const item = localStorage.getItem(this.PREFIX + key);
      if (item === null || item === undefined || item === 'undefined') {
        return null;
      }
      return JSON.parse(item);
    } catch (error) {
      console.error('Error getting item from localStorage:', error);
      return null;
    }
  }

  /**
   * Set item in localStorage with type safety
   */
  setItem<T>(key: string, value: T): boolean {
    if (!this.isBrowser) {
      return false;
    }
    try {
      // Enhanced debug logging
      if (key === 'refresh_token' || key === 'token') {
        console.log(`[StorageService] Setting ${key}:`, {
          key: this.PREFIX + key,
          originalValue: value,
          valueType: typeof value,
          isUndefined: value === undefined,
          isNull: value === null
        });
      }
      
      const serialized = JSON.stringify(value);
      localStorage.setItem(this.PREFIX + key, serialized);
      
      // Verify storage
      const stored = localStorage.getItem(this.PREFIX + key);
      if (key === 'refresh_token' || key === 'token') {
        console.log(`[StorageService] Verification for ${key}:`, {
          serialized: serialized,
          stored: stored,
          parsedBack: stored ? JSON.parse(stored) : null
        });
      }
      
      return true;
    } catch (error) {
      console.error('Error setting item in localStorage:', error);
      return false;
    }
  }

  /**
   * Remove item from localStorage
   */
  removeItem(key: string): boolean {
    if (!this.isBrowser) {
      return false;
    }
    try {
      localStorage.removeItem(this.PREFIX + key);
      return true;
    } catch (error) {
      console.error('Error removing item from localStorage:', error);
      return false;
    }
  }

  /**
   * Clear all GreekSTT Research Platform items from localStorage
   */
  clear(): boolean {
    if (!this.isBrowser) {
      return false;
    }
    try {
      const keys = Object.keys(localStorage);
      keys.forEach(key => {
        if (key.startsWith(this.PREFIX)) {
          localStorage.removeItem(key);
        }
      });
      return true;
    } catch (error) {
      console.error('Error clearing localStorage:', error);
      return false;
    }
  }

  /**
   * Get item from sessionStorage with type safety
   */
  getSessionItem<T>(key: string): T | null {
    if (!this.isBrowser) {
      return null;
    }
    try {
      const item = sessionStorage.getItem(this.PREFIX + key);
      return item ? JSON.parse(item) : null;
    } catch (error) {
      console.error('Error getting item from sessionStorage:', error);
      return null;
    }
  }

  /**
   * Set item in sessionStorage with type safety
   */
  setSessionItem<T>(key: string, value: T): boolean {
    if (!this.isBrowser) {
      return false;
    }
    try {
      sessionStorage.setItem(this.PREFIX + key, JSON.stringify(value));
      return true;
    } catch (error) {
      console.error('Error setting item in sessionStorage:', error);
      return false;
    }
  }

  /**
   * Remove item from sessionStorage
   */
  removeSessionItem(key: string): boolean {
    if (!this.isBrowser) {
      return false;
    }
    try {
      sessionStorage.removeItem(this.PREFIX + key);
      return true;
    } catch (error) {
      console.error('Error removing item from sessionStorage:', error);
      return false;
    }
  }

  /**
   * Check if localStorage is available
   */
  isLocalStorageAvailable(): boolean {
    if (!this.isBrowser) {
      return false;
    }
    try {
      const test = '__localStorage_test__';
      localStorage.setItem(test, test);
      localStorage.removeItem(test);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Check if sessionStorage is available
   */
  isSessionStorageAvailable(): boolean {
    if (!this.isBrowser) {
      return false;
    }
    try {
      const test = '__sessionStorage_test__';
      sessionStorage.setItem(test, test);
      sessionStorage.removeItem(test);
      return true;
    } catch {
      return false;
    }
  }
}