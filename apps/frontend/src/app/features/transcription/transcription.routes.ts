import { Routes } from '@angular/router';

export const transcriptionRoutes: Routes = [
  {
    path: '',
    loadComponent: () => import('./transcription-home/transcription-home.component').then(m => m.TranscriptionHomeComponent)
  },
  {
    path: ':id',
    loadComponent: () => import('./view/transcription-view.component').then(m => m.TranscriptionViewComponent)
  },
];