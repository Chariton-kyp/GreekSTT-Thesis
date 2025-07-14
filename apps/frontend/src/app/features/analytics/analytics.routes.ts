import { Routes } from '@angular/router';

export const analyticsRoutes: Routes = [
  {
    path: '',
    redirectTo: 'dashboard',
    pathMatch: 'full'
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./analytics-dashboard/analytics-dashboard.component').then(m => m.AnalyticsDashboardComponent),
    data: { title: 'Αναλυτικά Στατιστικά' }
  },
];