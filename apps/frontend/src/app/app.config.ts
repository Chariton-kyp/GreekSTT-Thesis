import { registerLocaleData } from '@angular/common';
import { provideHttpClient, withInterceptors, withFetch } from '@angular/common/http';
import localeEl from '@angular/common/locales/el';
import { ApplicationConfig, provideExperimentalZonelessChangeDetection, LOCALE_ID, ErrorHandler, APP_INITIALIZER } from '@angular/core';
import { provideClientHydration, withEventReplay } from '@angular/platform-browser';
import { provideAnimations } from '@angular/platform-browser/animations';
import { provideRouter, withComponentInputBinding, withPreloading, PreloadAllModules } from '@angular/router';

// PrimeNG
import Lara from '@primeng/themes/lara';
import { MessageService, ConfirmationService } from 'primeng/api';
import { providePrimeNG } from 'primeng/config';
import { DialogService } from 'primeng/dynamicdialog';

// Routes and Core
import { routes } from './app.routes';
import { authInterceptor, errorInterceptor, loadingInterceptor } from './core/interceptors';
import { ThemeService } from './core/services/theme.service';
import { CooldownService } from './core/services/cooldown.service';

// Register Greek locale
registerLocaleData(localeEl);

// Global error handler
class GlobalErrorHandler implements ErrorHandler {
  handleError(error: any): void {
    console.error('Global error:', error);
    // TODO: Send error to logging service
  }
}

export const appConfig: ApplicationConfig = {
  providers: [
    // Zoneless change detection (Angular 20 ready)
    provideExperimentalZonelessChangeDetection(),
    
    // Routing with modern features
    provideRouter(
      routes,
      withComponentInputBinding(),
      withPreloading(PreloadAllModules)
    ),
    
    // HTTP and Interceptors
    provideHttpClient(
      withInterceptors([authInterceptor, errorInterceptor, loadingInterceptor]),
      withFetch()
    ),
    
    // Browser features
    provideAnimations(),
    provideClientHydration(withEventReplay()),
    
    // Localization
    { provide: LOCALE_ID, useValue: 'el-GR' },
    
    // Error handling
    { provide: ErrorHandler, useClass: GlobalErrorHandler },
    
    // PrimeNG configuration
    providePrimeNG({ 
      theme: {
        preset: Lara
      }
    }),
    MessageService,
    ConfirmationService,
    DialogService,
    
    // Theme initialization
    {
      provide: APP_INITIALIZER,
      useFactory: (themeService: ThemeService) => () => {
        return new Promise<void>((resolve) => {
          // Theme service is initialized in constructor
          resolve();
        });
      },
      deps: [ThemeService],
      multi: true
    },
    
    // Cooldown service initialization
    {
      provide: APP_INITIALIZER,
      useFactory: (cooldownService: CooldownService) => () => {
        return new Promise<void>((resolve) => {
          cooldownService.initializeCooldowns();
          resolve();
        });
      },
      deps: [CooldownService],
      multi: true
    }
  ]
};
