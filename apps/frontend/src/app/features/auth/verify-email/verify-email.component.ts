import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, RouterModule } from '@angular/router';

import { ButtonModule } from 'primeng/button';
import { InputOtpModule } from 'primeng/inputotp';

import { BaseComponent } from '../../../core/patterns/base-component';
import { AuthService } from '../../../core/services/auth.service';
import { CooldownService } from '../../../core/services/cooldown.service';
import { LoadingSpinnerComponent } from '../../../shared/components/loading-spinner/loading-spinner.component';

@Component({
  selector: 'app-verify-email',
  standalone: true,
  imports: [CommonModule, RouterModule, ReactiveFormsModule, ButtonModule, InputOtpModule, LoadingSpinnerComponent],
  templateUrl: './verify-email.component.html'
})
export class VerifyEmailComponent extends BaseComponent implements OnInit {
  readonly authService = inject(AuthService);
  private readonly cooldownService = inject(CooldownService);
  private readonly route = inject(ActivatedRoute);
  private readonly fb = inject(FormBuilder);


  // Forms
  codeForm: FormGroup;

  // State signals
  readonly isVerified = signal(false);
  readonly isCodeMode = signal(true);
  readonly expiresIn = signal(600); // 10 minutes default
  
  // Cooldown management
  readonly resendCooldown = this.cooldownService.getCooldownSignal('email_verification_resend');

  // Context from query parameters
  readonly verificationReason = signal<string>('registration');
  readonly userEmail = signal<string | null>(null);
  readonly returnUrl = signal<string | null>(null);

  // Legacy token support
  private token: string | null = null;

  constructor() {
    super();
    this.codeForm = this.fb.group({
      code: ['', [Validators.required, Validators.minLength(6), Validators.maxLength(6)]]
    });
  }

  ngOnInit() {
    // Initialize cooldown service
    this.cooldownService.initializeCooldowns();
    
    // Parse query parameters
    this.parseQueryParameters();

    // Check for legacy token in route
    this.token = this.route.snapshot.paramMap.get('token') || 
                 this.route.snapshot.queryParamMap.get('token');

    if (this.token) {
      // Legacy token verification
      this.verifyLegacyToken();
    } else {
      // New 6-digit code mode
      this.isCodeMode.set(true);
      this.checkAuthenticationStatus();
      this.checkExistingCooldown();
    }
  }

  private parseQueryParameters() {
    const params = this.route.snapshot.queryParamMap;
    
    // Set verification reason (registration, login, profile-update, etc.)
    const reason = params.get('reason') || 'registration';
    this.verificationReason.set(reason);
    
    // Set email if provided
    const email = params.get('email');
    this.userEmail.set(email);
    
    // Set return URL
    const returnUrl = params.get('returnUrl') || '/app/dashboard';
    this.returnUrl.set(returnUrl);
  }

  private async verifyLegacyToken() {
    this.loadingState.setLoading(true);
    this.isCodeMode.set(false);

    await this.authService.verifyEmail(this.token!);
    this.isVerified.set(true);
    this.loadingState.setLoading(false);
    
    // Redirect to dashboard after 2 seconds
    setTimeout(() => {
      this.router.navigate(['/app/dashboard']);
    }, 2000);
  }

  private async checkAuthenticationStatus() {
    const reason = this.verificationReason();
    
    // Wait for auth service to initialize if not yet initialized
    if (!this.authService.isInitialized()) {
      // Wait for initialization to complete
      await this.waitForAuthInitialization();
    }
    
    // Always require authentication for OTP verification
    if (!this.authService.isAuthenticated()) {
      this.router.navigate(['/auth/login'], {
        queryParams: { 
          returnUrl: '/auth/verify-email',
          reason: reason,
          email: this.userEmail() || undefined
        }
      });
      return;
    }

    // Check if already verified (prefer JWT claims)
    const isVerified = this.authService.isEmailVerified();
    if (isVerified) {
      this.isVerified.set(true);
      this.navigateToReturnUrl();
      return;
    }
    
    // Set user email for display (try JWT claims first, then user data)
    if (!this.userEmail()) {
      const claims = this.authService.currentClaims();
      const user = this.authService.currentUser();
      const email = claims?.email || user?.email;
      if (email) {
        this.userEmail.set(email);
      }
    }
  }

  /**
   * Wait for auth service to complete initialization
   */
  private async waitForAuthInitialization(): Promise<void> {
    return new Promise<void>((resolve) => {
      if (this.authService.isInitialized()) {
        resolve();
        return;
      }

      // Use setTimeout to avoid infinite loops
      const checkInterval = setInterval(() => {
        if (this.authService.isInitialized()) {
          clearInterval(checkInterval);
          resolve();
        }
      }, 100);
      
      // Timeout after 10 seconds
      setTimeout(() => {
        clearInterval(checkInterval);
        resolve();
      }, 10000);
    });
  }

  private checkExistingCooldown() {
    // Check if there's an active cooldown from a previous resend
    const cooldownState = this.cooldownService.getCooldownState('email_verification_resend');
    if (cooldownState.isActive) {
      // Cooldown is already active and will be displayed via the signal
      console.log(`Resend cooldown active: ${cooldownState.remainingSeconds} seconds remaining`);
    }
  }

  async onCodeComplete() {
    const code = this.codeForm.get('code')?.value;
    if (!code || code.length !== 6) return;

    console.log('[VerifyEmailComponent] Starting verification with code:', code.substring(0, 2) + '****');

    this.loadingState.setLoading(true);

    // Always use session token for verification (user must be logged in)
    if (!this.authService.isAuthenticated()) {
      this.router.navigate(['/auth/login'], {
        queryParams: { 
          returnUrl: '/auth/verify-email',
          reason: this.verificationReason(),
          email: this.userEmail() || undefined
        }
      });
      return;
    }
    
    console.log('[VerifyEmailComponent] User is authenticated, calling backend...');
    
    try {
      await this.authService.verifyEmailWithCode(code);
      
      console.log('[VerifyEmailComponent] Verification successful!');
      
      this.isVerified.set(true);
      this.loadingState.setLoading(false);
      
      // Update user data to reflect verification status
      await this.authService.getCurrentUser();
      
      // Redirect after success
      setTimeout(() => {
        this.navigateToReturnUrl();
      }, 1500);
    } catch (error) {
      console.log('[VerifyEmailComponent] Verification failed:', error);
      this.loadingState.setLoading(false);
      // Error message is automatically shown by ApiService
    }
  }

  onCodeChange() {
    const code = this.codeForm.get('code')?.value;
    if (code && code.length === 6) {
      this.onCodeComplete();
    }
  }

  async onResendCode() {
    if (!this.authService.isAuthenticated()) {
      this.router.navigate(['/auth/login'], {
        queryParams: { 
          returnUrl: '/auth/verify-email',
          reason: this.verificationReason(),
          email: this.userEmail() || undefined
        }
      });
      return;
    }

    this.loadingState.setLoading(true);

    // Use session token for resend (no email needed)
    await this.authService.resendVerificationCode();
    this.loadingState.setLoading(false);
    
    this.cooldownService.startCooldown('email_verification_resend', 120); // 2 minutes
    this.codeForm.get('code')?.setValue('');
  }





  private navigateToReturnUrl() {
    const returnUrl = this.returnUrl() || '/app/dashboard';
    this.router.navigate([returnUrl]);
  }

  navigateToLogin() {
    this.router.navigate(['/auth/login']);
  }

  navigateToDashboard() {
    this.navigateToReturnUrl();
  }

  getHeaderMessage(): string {
    const reason = this.verificationReason();
    
    switch (reason) {
      case 'registration':
        return 'Ολοκληρώστε την εγγραφή σας';
      case 'login':
        return 'Επιβεβαιώστε την ταυτότητά σας';
      case 'profile-update':
        return 'Επιβεβαιώστε το νέο email';
      case 'security':
        return 'Επιβεβαίωση ασφαλείας';
      default:
        return 'Επαλήθευση Email';
    }
  }

  getSubHeaderMessage(): string {
    const reason = this.verificationReason();
    const email = this.userEmail() || this.authService.currentUser()?.email || '';
    
    switch (reason) {
      case 'registration':
        return `Έχουμε στείλει έναν κωδικό επαλήθευσης στο ${email}. Εισάγετέ τον για να ολοκληρώσετε την εγγραφή σας.`;
      case 'login':
        return `Για την ασφάλειά σας, παρακαλώ επιβεβαιώστε την ταυτότητά σας εισάγοντας τον κωδικό που στείλαμε στο ${email}.`;
      case 'profile-update':
        return `Παρακαλώ επιβεβαιώστε το νέο σας email εισάγοντας τον κωδικό που στείλαμε στο ${email}.`;
      case 'security':
        return `Για λόγους ασφαλείας, παρακαλώ εισάγετε τον κωδικό που στείλαμε στο ${email}.`;
      default:
        return `Έχουμε στείλει έναν 6ψήφιο κωδικό επαλήθευσης στο ${email}.`;
    }
  }

  override getFieldError(form: any, fieldName: string): string {
    const field = form.get(fieldName);
    if (field?.errors && field.touched) {
      if (field.errors['required']) return 'Ο κωδικός είναι υποχρεωτικός';
      if (field.errors['pattern']) return 'Ο κωδικός πρέπει να έχει 6 ψηφία';
      if (field.errors['minlength']) return 'Ο κωδικός πρέπει να έχει 6 ψηφία';
      if (field.errors['maxlength']) return 'Ο κωδικός πρέπει να έχει 6 ψηφία';
    }
    return '';
  }

  formatCooldown(seconds: number): string {
    return this.cooldownService.formatCooldown(seconds);
  }

  // Template getters for unified loading state
  isLoading(): boolean {
    return this.loadingState.isLoading();
  }

  errorMessage(): string | null {
    return this.loadingState.error();
  }

}