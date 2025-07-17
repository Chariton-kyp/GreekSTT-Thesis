import { Injectable, signal, computed, effect, inject } from '@angular/core';

import { StorageService } from './storage.service';
import { environment } from '../../../environments/environment';

export type Theme = 'dark' | 'light';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private readonly THEME_KEY = 'theme';
  private readonly storage = inject(StorageService);
  
  private _isDarkMode = signal<boolean>(environment.theme.default === 'dark');
  private _isSystemPreference = signal<boolean>(false);

  readonly isDarkMode = this._isDarkMode.asReadonly();
  readonly isSystemPreference = this._isSystemPreference.asReadonly();
  
  readonly currentTheme = computed<Theme>(() => this.isDarkMode() ? 'dark' : 'light');
  readonly themeIcon = computed(() => this.isDarkMode() ? 'pi-sun' : 'pi-moon');
  readonly themeLabel = computed(() => this.isDarkMode() ? 'Φωτεινό θέμα' : 'Σκοτεινό θέμα');

  constructor() {
    this.initializeTheme();
    
    effect(() => {
      this.applyTheme(this.currentTheme());
    });

    effect(() => {
      if (!this.isSystemPreference()) {
        this.saveThemePreference(this.isDarkMode());
      }
    });

    if (typeof window !== 'undefined' && window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      mediaQuery.addEventListener('change', (e) => {
        if (this.isSystemPreference()) {
          this._isDarkMode.set(e.matches);
        }
      });
    }
  }

  toggleTheme(): void {
    this._isDarkMode.update(current => !current);
    this._isSystemPreference.set(false);
  }

  setDarkMode(isDark: boolean): void {
    this._isDarkMode.set(isDark);
    this._isSystemPreference.set(false);
  }

  useSystemPreference(): void {
    this._isSystemPreference.set(true);
    if (typeof window !== 'undefined' && window.matchMedia) {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      this._isDarkMode.set(prefersDark);
    }
  }

  private initializeTheme(): void {
    const savedTheme = this.storage.getItem<string>(this.THEME_KEY);
    
    if (savedTheme === null) {
      if (environment.theme.enableSystemPreference) {
        this.useSystemPreference();
      }
    } else if (savedTheme === 'system') {
      this.useSystemPreference();
    } else {
      this._isDarkMode.set(savedTheme === 'dark');
      this._isSystemPreference.set(false);
    }
  }

  private applyTheme(theme: Theme): void {
    if (typeof document === 'undefined') return;

    const html = document.documentElement;
    
    html.classList.remove('dark', 'light');
    html.removeAttribute('data-theme');
    
    html.classList.add(theme);
    html.setAttribute('data-theme', theme);
    
    if (theme === 'dark') {
      html.classList.add('p-dark');
    } else {
      html.classList.remove('p-dark');
    }
    
    this.updateMetaThemeColor(theme);
  }

  private updateMetaThemeColor(theme: Theme): void {
    if (typeof document === 'undefined') return;

    let metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (!metaThemeColor) {
      metaThemeColor = document.createElement('meta');
      metaThemeColor.setAttribute('name', 'theme-color');
      document.head.appendChild(metaThemeColor);
    }
    
    const color = theme === 'dark' ? '#0f172a' : '#ffffff';
    metaThemeColor.setAttribute('content', color);
  }


  private saveThemePreference(isDark: boolean): void {
    this.storage.setItem(this.THEME_KEY, isDark ? 'dark' : 'light');
  }

  private saveSystemPreferenceFlag(): void {
    this.storage.setItem(this.THEME_KEY, 'system');
  }
}