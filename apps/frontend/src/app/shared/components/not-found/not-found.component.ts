import { Component, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-not-found',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    ButtonModule,
    CardModule
  ],
  template: `
    <div class="not-found-container min-h-screen flex items-center justify-center p-4">
      <div class="max-w-2xl w-full">
        <p-card styleClass="text-center">
          <div class="space-y-6">
            <!-- 404 Icon -->
            <div class="text-center">
              <div class="text-8xl font-bold text-cyan-500 dark:text-cyan-400 mb-4">
                404
              </div>
              <i class="pi pi-exclamation-triangle text-6xl text-orange-500 dark:text-orange-400"></i>
            </div>

            <!-- Error Message -->
            <div>
              <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-4">
                Η σελίδα δεν βρέθηκε
              </h1>
              <p class="text-lg text-gray-600 dark:text-gray-300 mb-2">
                Λυπούμαστε, η σελίδα που αναζητάτε δεν υπάρχει ή έχει μετακινηθεί.
              </p>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                Παρακαλούμε ελέγξτε τη διεύθυνση URL ή επιστρέψτε στην αρχική σελίδα.
              </p>
            </div>

            <!-- Action Buttons -->
            <div class="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <p-button
                [label]="homeLabel()"
                [icon]="homeIcon()"
                [routerLink]="[homeRoute()]"
                styleClass="w-full sm:w-auto">
              </p-button>
              
              <p-button
                label="Πίσω"
                icon="pi pi-arrow-left"
                severity="secondary"
                [outlined]="true"
                (onClick)="goBack()"
                styleClass="w-full sm:w-auto">
              </p-button>
            </div>

            <!-- Academic Info -->
            <div class="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div class="flex flex-col sm:flex-row items-center gap-3">
                <i class="pi pi-graduation-cap text-blue-500 dark:text-blue-400 text-2xl"></i>
                <div class="text-center sm:text-left">
                  <h3 class="text-sm font-semibold text-blue-900 dark:text-blue-100">
                    GreekSTT Comparison Platform
                  </h3>
                  <p class="text-xs text-blue-700 dark:text-blue-200">
                    Ακαδημαϊκή πλατφόρμα για έρευνα στην ελληνική αναγνώριση ομιλίας
                  </p>
                </div>
              </div>
            </div>

            <!-- Helpful Links -->
            @if (isAuthenticated()) {
              <div class="border-t border-gray-200 dark:border-gray-700 pt-6">
                <h4 class="text-sm font-medium text-gray-900 dark:text-white mb-3">
                  Χρήσιμοι σύνδεσμοι:
                </h4>
                <div class="flex flex-wrap gap-2 justify-center">
                  <p-button
                    label="Μεταγραφές"
                    icon="pi pi-microphone"
                    [text]="true"
                    size="small"
                    [routerLink]="['/app/transcriptions']">
                  </p-button>
                  
                  <p-button
                    label="Σύγκριση Μοντέλων"
                    icon="pi pi-chart-line"
                    [text]="true"
                    size="small"
                    [routerLink]="['/app/transcriptions/compare']">
                  </p-button>
                  
                  <p-button
                    label="Αναλυτικά Στοιχεία"
                    icon="pi pi-chart-bar"
                    [text]="true"
                    size="small"
                    [routerLink]="['/app/analytics']">
                  </p-button>
                  
                  <p-button
                    label="Βοήθεια"
                    icon="pi pi-question-circle"
                    [text]="true"
                    size="small"
                    [routerLink]="['/app/help']">
                  </p-button>
                </div>
              </div>
            }
          </div>
        </p-card>
      </div>
    </div>
  `,
  styleUrl: './not-found.component.scss'
})
export class NotFoundComponent {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  
  // Check if user is authenticated
  readonly isAuthenticated = computed(() => this.authService.isAuthenticated());
  
  // Get the appropriate home route based on auth status
  readonly homeRoute = computed(() => {
    return this.isAuthenticated() ? '/app/dashboard' : '/';
  });
  
  // Get the appropriate home label based on auth status
  readonly homeLabel = computed(() => {
    return this.isAuthenticated() ? 'Πίνακας Ελέγχου' : 'Αρχική Σελίδα';
  });
  
  // Get the appropriate home icon based on auth status
  readonly homeIcon = computed(() => {
    return this.isAuthenticated() ? 'pi pi-th-large' : 'pi pi-home';
  });
  
  goBack(): void {
    // Check if there's history to go back to
    if (window.history.length > 1) {
      // Try to get the previous URL from the current router state
      const currentNavigation = this.router.getCurrentNavigation();
      const previousUrl = currentNavigation?.previousNavigation?.finalUrl?.toString();
      
      // If we have a previous URL and it's not the same page, go back
      if (previousUrl && previousUrl !== this.router.url) {
        window.history.back();
      } else {
        // Navigate to appropriate home
        this.navigateToHome();
      }
    } else {
      // No history, navigate to appropriate home
      this.navigateToHome();
    }
  }
  
  private navigateToHome(): void {
    const targetRoute = this.homeRoute();
    this.router.navigate([targetRoute]);
  }
}