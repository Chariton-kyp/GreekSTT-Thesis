import { Routes } from '@angular/router';

export const profileRoutes: Routes = [
  {
    path: '',
    loadComponent: () => import('./profile.component').then(m => m.ProfileComponent)
  },
  {
    path: 'settings',
    loadComponent: () => import('./settings/settings.component').then(m => m.SettingsComponent)
  },
];