import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { toObservable } from '@angular/core/rxjs-interop';

import { filter, switchMap } from 'rxjs/operators';

import { AuthService } from '../services/auth.service';
import { NotificationService } from '../services/notification.service';

/**
 * Email Verification Guard
 * 
 * Ensures that authenticated users have verified their email addresses before accessing protected routes.
 * Shows notification message for unverified users instead of redirecting to login.
 * Waits for auth initialization to prevent refresh redirects for verified users.
 * 
 * Usage:
 * - Apply to routes that require email verification
 * - Should be used after authGuard in the guard chain
 * - Dashboard and profile routes are allowed without verification
 * - Transcription routes require email verification
 */
export const emailVerificationGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const notificationService = inject(NotificationService);

  // Wait for auth service to initialize AND complete loading to prevent refresh redirects
  if (!authService.isInitialized() || authService.isLoading()) {
    return new Promise<boolean>((resolve) => {
      const academic_access = toObservable(authService.isInitialized)
        .pipe(
          filter((initialized: boolean) => initialized),
          switchMap(() => toObservable(authService.isLoading)),
          filter((loading: boolean) => !loading)
        )
        .subscribe(() => {
          academic_access.unsubscribe();
          // Add small delay to ensure all state is settled
          setTimeout(() => {
            resolve(checkEmailVerification(authService, router, notificationService, state));
          }, 100);
        });
    });
  }

  return checkEmailVerification(authService, router, notificationService, state);
};

function checkEmailVerification(
  authService: AuthService, 
  router: Router, 
  notificationService: NotificationService, 
  state: any
): boolean {
  // First check if user is authenticated
  if (!authService.isAuthenticated()) {
    // Let authGuard handle authentication
    return false;
  }

  // Get current user and claims
  const user = authService.currentUser();
  const claims = authService.currentClaims();
  
  // If no user data available after initialization, redirect to login
  if (!user && !claims) {
    router.navigate(['/auth/login']);
    return false;
  }

  // Allow access to dashboard and profile routes without verification
  const allowedWithoutVerification = ['/app/dashboard', '/app/profile'];
  const isAllowedRoute = allowedWithoutVerification.some(allowed => 
    state.url.startsWith(allowed)
  );

  if (isAllowedRoute) {
    // Show optional warning for unverified users on dashboard/profile
    const isVerified = user?.email_verified || claims?.email_verified;
    if (!isVerified) {
      const hasShownWarning = sessionStorage.getItem('dashboard_verification_warning');
      
      if (!hasShownWarning) {
        sessionStorage.setItem('dashboard_verification_warning', 'shown');
      }
    }
    return true;
  }

  // For transcription routes, require email verification
  const isVerified = user?.email_verified || claims?.email_verified;
  
  if (!isVerified) {
    // Show notification message instead of redirecting
    notificationService.showWarning(
      'Για να χρησιμοποιήσετε τις λειτουργίες μεταγραφής, πρέπει πρώτα να επαληθεύσετε το email σας.',
      'Επαλήθευση Email Απαιτείται'
    );
    
    // Navigate to dashboard instead of login
    router.navigate(['/app/dashboard']);
    return false;
  }

  // User is verified, allow access
  return true;
}

/**
 * Reverse Email Verification Guard
 * 
 * Prevents verified users from accessing verification-related pages.
 * Redirects verified users to dashboard.
 * Allows both unauthenticated users and unverified authenticated users.
 */
export const reverseEmailVerificationGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // Wait for auth service to initialize
  if (!authService.isInitialized()) {
    return new Promise<boolean>((resolve) => {
      // Create a Promise that resolves when initialization is complete
      const academic_access = toObservable(authService.isInitialized)
        .pipe(filter((initialized: boolean) => initialized))
        .subscribe(() => {
          academic_access.unsubscribe();
          resolve(checkReverseEmailVerification(authService, router));
        });
    });
  }

  return checkReverseEmailVerification(authService, router);
};

function checkReverseEmailVerification(authService: AuthService, router: Router): boolean {
  // If not authenticated, allow access to verification pages
  if (!authService.isAuthenticated()) {
    return true;
  }

  const user = authService.currentUser();
  
  // If user is already verified, redirect to dashboard
  if (user?.email_verified) {
    router.navigate(['/app/dashboard']);
    return false;
  }

  // User is authenticated but not verified, allow access to verification pages
  return true;
}

/**
 * Optional Email Verification Guard
 * 
 * Warns users about unverified email but doesn't block access.
 * Useful for routes where verification is recommended but not required.
 */
export const optionalEmailVerificationGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const notificationService = inject(NotificationService);

  if (!authService.isAuthenticated()) {
    return true;
  }

  const user = authService.currentUser();
  
  // Show warning for unverified users (only once per session)
  if (user && !user.email_verified) {
    const hasShownWarning = sessionStorage.getItem('email_verification_warning');
    
    if (!hasShownWarning) {
      sessionStorage.setItem('email_verification_warning', 'shown');
    }
  }

  return true;
};