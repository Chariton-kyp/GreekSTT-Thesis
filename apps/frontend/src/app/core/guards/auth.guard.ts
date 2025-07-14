import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { toObservable } from '@angular/core/rxjs-interop';

import { from, of, firstValueFrom } from 'rxjs';
import { map, take, filter, switchMap } from 'rxjs/operators';

import { AuthService } from '../services/auth.service';
export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // Wait for auth service to initialize using toObservable
  if (!authService.isInitialized()) {
    // Create a Promise that resolves when initialization is complete
    return new Promise<boolean>((resolve) => {
      // Convert signal to observable and watch for initialization
      const academic_access = toObservable(authService.isInitialized)
        .pipe(filter((initialized: boolean) => initialized))
        .subscribe(() => {
          academic_access.unsubscribe();
          resolve(checkAuthentication(authService, router, state));
        });
    });
  }

  return checkAuthentication(authService, router, state);
};

/**
 * Helper function to check authentication after initialization is complete
 */
function checkAuthentication(authService: AuthService, router: Router, state: any): boolean {
  // Check if user is authenticated
  if (!authService.isAuthenticated()) {
    router.navigate(['/auth/login'], { queryParams: { returnUrl: state.url } });
    return false;
  }

  return true;
}

/**
 * Simple authenticated guard
 */
export const authenticatedGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (!authService.isAuthenticated()) {
    router.navigate(['/auth/login'], { queryParams: { returnUrl: state.url } });
    return false;
  }

  return true;
};

// Research level guards removed for thesis simplification - only authentication matters

/**
 * Guard for guest users (not authenticated)
 * Redirects to dashboard if already logged in
 */
export const guestGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // Wait for auth service to initialize
  if (!authService.isInitialized()) {
    return new Promise<boolean>((resolve) => {
      const academic_access = toObservable(authService.isInitialized)
        .pipe(filter((initialized: boolean) => initialized))
        .subscribe(() => {
          academic_access.unsubscribe();
          resolve(checkGuestAccess(authService, router));
        });
    });
  }

  return checkGuestAccess(authService, router);
};

function checkGuestAccess(authService: AuthService, router: Router): boolean {
  if (authService.isAuthenticated()) {
    router.navigate(['/app/dashboard']);
    return false;
  }

  return true;
}

// Legacy guard aliases - all simplified to authentication only for thesis
export const advancedGuard = authenticatedGuard;
export const premiumGuard = authenticatedGuard;
export const professionalGuard = authenticatedGuard;
export const researcherGuard = authenticatedGuard;
export const advancedResearchGuard = authenticatedGuard;