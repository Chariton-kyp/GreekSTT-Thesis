import { CommonModule, DOCUMENT } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Router } from '@angular/router';

import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { CarouselModule } from 'primeng/carousel';
import { ScrollTopModule } from 'primeng/scrolltop';

import { AuthService } from '../../core/services/auth.service';
import { ThemeService } from '../../core/services/theme.service';
import { LogoComponent } from '../../shared/components/logo/logo.component';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [CommonModule, ButtonModule, CardModule, CarouselModule, ScrollTopModule, LogoComponent],
  templateUrl: './landing.component.html',
  styleUrl: './landing.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LandingComponent {
  readonly themeService = inject(ThemeService);
  readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly document = inject(DOCUMENT);

  readonly academicFeatures = [
    {
      name: 'Whisper Large V3',
      category: 'ASR Model',
      icon: 'pi pi-microphone',
      iconColor: 'blue',
      description: 'Πρωτοποριακό μοντέλο OpenAI με εξαιρετική ακρίβεια στην ελληνική γλώσσα και αντοχή στον θόρυβο.'
    },
    {
      name: 'Wav2Vec2 XLS-R',
      category: 'ASR Model',
      icon: 'pi pi-chart-line',
      iconColor: 'green',
      description: 'Εξειδικευμένο μοντέλο Facebook Research για πολύγλωσση αναγνώριση ομιλίας με έμφαση στην ελληνική.'
    },
    {
      name: 'Συγκριτική Ανάλυση',
      category: 'Research Tool',
      icon: 'pi pi-chart-bar',
      iconColor: 'purple',
      description: 'Εργαλεία για παράλληλη σύγκριση της απόδοσης των μοντέλων με μετρήσεις WER και ταχύτητας.'
    }
  ];

  readonly carouselResponsiveOptions = [
    {
      breakpoint: '768px',
      numVisible: 1,
      numScroll: 1
    },
    {
      breakpoint: '1024px',
      numVisible: 2,
      numScroll: 1
    }
  ];
  
  onLogin(): void {
    this.router.navigate(['/auth/login']);
  }

  onRegister(): void {
    this.router.navigate(['/auth/register']);
  }

  onGetStarted(): void {
    if (this.authService.isAuthenticated()) {
      this.router.navigate(['/app/dashboard']);
    } else {
      this.router.navigate(['/auth/register']);
    }
  }

  onLearnMore(): void {
    // Scroll to features section
    const featuresSection = this.document.querySelector('section');
    featuresSection?.scrollIntoView({ behavior: 'smooth' });
  }

  onDashboard(): void {
    this.router.navigate(['/app/dashboard']);
  }

  onComparisonDemo(): void {
    if (this.authService.isAuthenticated()) {
      this.router.navigate(['/app/transcriptions']);
    } else {
      this.router.navigate(['/auth/register']);
    }
  }
}
