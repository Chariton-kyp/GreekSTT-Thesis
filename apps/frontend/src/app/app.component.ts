import { CommonModule } from '@angular/common';
import { Component, inject, ChangeDetectionStrategy } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { MessageModule } from 'primeng/message';
import { ToastModule } from 'primeng/toast';

import { ThemeService, AuthService } from './core';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, ConfirmDialogModule, MessageModule, ToastModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    '[class.dark]': 'themeService.isDarkMode()',
    '[class.light]': '!themeService.isDarkMode()',
  },
})
export class AppComponent {
  title = 'greekstt-research-frontend';

  readonly themeService = inject(ThemeService);
  private readonly authService = inject(AuthService);
}
