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
      return null;
    }
  }

  setItem<T>(key: string, value: T): boolean {
    if (!this.isBrowser) {
      return false;
    }
    try {
      
      const serialized = JSON.stringify(value);
      localStorage.setItem(this.PREFIX + key, serialized);
      
      
      return true;
    } catch (error) {
      return false;
    }
  }

  removeItem(key: string): boolean {
    if (!this.isBrowser) {
      return false;
    }
    try {
      localStorage.removeItem(this.PREFIX + key);
      return true;
    } catch (error) {
      return false;
    }
  }

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
      return false;
    }
  }

  getSessionItem<T>(key: string): T | null {
    if (!this.isBrowser) {
      return null;
    }
    try {
      const item = sessionStorage.getItem(this.PREFIX + key);
      return item ? JSON.parse(item) : null;
    } catch (error) {
      return null;
    }
  }

  setSessionItem<T>(key: string, value: T): boolean {
    if (!this.isBrowser) {
      return false;
    }
    try {
      sessionStorage.setItem(this.PREFIX + key, JSON.stringify(value));
      return true;
    } catch (error) {
      return false;
    }
  }

  removeSessionItem(key: string): boolean {
    if (!this.isBrowser) {
      return false;
    }
    try {
      sessionStorage.removeItem(this.PREFIX + key);
      return true;
    } catch (error) {
      return false;
    }
  }

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