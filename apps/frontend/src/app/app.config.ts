import { registerLocaleData } from '@angular/common';
import { provideHttpClient, withInterceptors, withFetch } from '@angular/common/http';
import localeEl from '@angular/common/locales/el';
import { ApplicationConfig, provideExperimentalZonelessChangeDetection, LOCALE_ID, ErrorHandler, APP_INITIALIZER } from '@angular/core';
import { provideClientHydration, withEventReplay } from '@angular/platform-browser';
import { provideAnimations } from '@angular/platform-browser/animations';
import { provideRouter, withComponentInputBinding, withPreloading, PreloadAllModules } from '@angular/router';

import Lara from '@primeng/themes/lara';
import { MessageService, ConfirmationService } from 'primeng/api';
import { providePrimeNG } from 'primeng/config';
import { DialogService } from 'primeng/dynamicdialog';

import { routes } from './app.routes';
import { authInterceptor, errorInterceptor, loadingInterceptor } from './core/interceptors';
import { ThemeService } from './core/services/theme.service';
import { CooldownService } from './core/services/cooldown.service';

registerLocaleData(localeEl);

class GlobalErrorHandler implements ErrorHandler {
  handleError(error: any): void {
    console.error('Global error:', error);
  }
}

export const appConfig: ApplicationConfig = {
  providers: [
    provideExperimentalZonelessChangeDetection(),
    
    provideRouter(
      routes,
      withComponentInputBinding(),
      withPreloading(PreloadAllModules)
    ),
    
    provideHttpClient(
      withInterceptors([authInterceptor, errorInterceptor, loadingInterceptor]),
      withFetch()
    ),
    
    provideAnimations(),
    provideClientHydration(withEventReplay()),
    
    { provide: LOCALE_ID, useValue: 'el-GR' },
    
    { provide: ErrorHandler, useClass: GlobalErrorHandler },
    
    providePrimeNG({ 
      theme: {
        preset: Lara
      }
    }),
    MessageService,
    ConfirmationService,
    DialogService,
    
    {
      provide: APP_INITIALIZER,
      useFactory: (themeService: ThemeService) => () => {
        return new Promise<void>((resolve) => {
          resolve();
        });
      },
      deps: [ThemeService],
      multi: true
    },
    
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
