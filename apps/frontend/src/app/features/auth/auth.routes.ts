import { Routes } from '@angular/router';

import { reverseEmailVerificationGuard } from '../../core/guards/email-verification.guard';

export const authRoutes: Routes = [
  {
    path: '',
    loadComponent: () => import('../../layout/auth-layout/auth-layout.component').then(m => m.AuthLayoutComponent),
    children: [
      {
        path: 'login',
        loadComponent: () => import('./login/login.component').then(m => m.LoginComponent)
      },
      {
        path: 'register',
        loadComponent: () => import('./register/register.component').then(m => m.RegisterComponent)
      },
      {
        path: 'forgot-password',
        loadComponent: () => import('./forgot-password/forgot-password.component').then(m => m.ForgotPasswordComponent)
      },
      {
        path: 'reset-password',
        loadComponent: () => import('./reset-password/reset-password.component').then(m => m.ResetPasswordComponent)
      },
      {
        path: 'verify-email',
        loadComponent: () => import('./verify-email/verify-email.component').then(m => m.VerifyEmailComponent),
        canActivate: [reverseEmailVerificationGuard]
      },
      {
        path: '',
        redirectTo: 'login',
        pathMatch: 'full'
      }
    ]
  }
];