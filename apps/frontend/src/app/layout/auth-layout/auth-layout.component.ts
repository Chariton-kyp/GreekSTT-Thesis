import { CommonModule } from '@angular/common';
import { Component, inject, computed } from '@angular/core';
import { RouterOutlet, RouterModule } from '@angular/router';
import { ButtonModule } from 'primeng/button';

import { ThemeService } from '../../core/services/theme.service';
import { LogoComponent } from '../../shared/components/logo/logo.component';

@Component({
  selector: 'app-auth-layout',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterModule, ButtonModule, LogoComponent],
  templateUrl: './auth-layout.component.html'
})
export class AuthLayoutComponent {
  private readonly themeService = inject(ThemeService);

  readonly isDarkMode = this.themeService.isDarkMode;

  toggleTheme(): void {
    this.themeService.toggleTheme();
  }
}