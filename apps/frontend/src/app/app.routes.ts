import { Routes } from '@angular/router';

import { authGuard } from './core/guards/auth.guard';
import { emailVerificationGuard, optionalEmailVerificationGuard } from './core/guards/email-verification.guard';

export const routes: Routes = [
  // Public routes
  {
    path: '',
    loadComponent: () => import('./features/landing/landing.component').then(m => m.LandingComponent)
  },
  
  
  // Authentication routes (public)
  {
    path: 'auth',
    loadChildren: () => import('./features/auth/auth.routes').then(r => r.authRoutes)
  },
  
  // Protected routes - require authentication
  {
    path: 'app',
    loadComponent: () => import('./layout/main-layout/main-layout.component').then(m => m.MainLayoutComponent),
    canActivate: [authGuard],
    children: [
      {
        path: 'dashboard',
        loadChildren: () => import('./features/dashboard/dashboard.routes').then(r => r.dashboardRoutes),
        canActivate: [optionalEmailVerificationGuard]
      },
      {
        path: 'transcriptions',
        loadChildren: () => import('./features/transcription/transcription.routes').then(r => r.transcriptionRoutes),
        canActivate: [emailVerificationGuard]
      },
      {
        path: 'profile',
        loadChildren: () => import('./features/profile/profile.routes').then(r => r.profileRoutes),
        canActivate: [optionalEmailVerificationGuard]
      },
      {
        path: 'analytics',
        loadChildren: () => import('./features/analytics/analytics.routes').then(r => r.analyticsRoutes),
        canActivate: [emailVerificationGuard]
      },
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full'
      },
      // Not found within app routes
      {
        path: '**',
        loadComponent: () => import('./shared/components/not-found/not-found.component').then(m => m.NotFoundComponent)
      }
    ]
  },
  
  // Redirect root to landing page
  {
    path: '',
    redirectTo: '',
    pathMatch: 'full'
  },
  
  // Wildcard route - must be last
  {
    path: '**',
    loadComponent: () => import('./shared/components/not-found/not-found.component').then(m => m.NotFoundComponent)
  }
];
