import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';

import { ButtonModule } from 'primeng/button';
import { InputOtpModule } from 'primeng/inputotp';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';

import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-reset-password',
  standalone: true,
  imports: [
    CommonModule, 
    ReactiveFormsModule, 
    RouterModule, 
    ButtonModule,
    InputTextModule,
    PasswordModule,
    InputOtpModule
  ],
  templateUrl: './reset-password.component.html'
})
export class ResetPasswordComponent {
  codeVerificationForm: FormGroup;
  resetPasswordForm: FormGroup;
  isLoading = false;
  isCodeVerified = false;
  email: string | null = null;
  canResendCode = true;
  resendCountdown = 0;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    private notificationService: NotificationService
  ) {
    this.email = this.route.snapshot.queryParamMap.get('email');
    
    this.codeVerificationForm = this.fb.group({
      code: ['', [Validators.required, Validators.pattern(/^\d{6}$/), Validators.minLength(6), Validators.maxLength(6)]]
    });
    
    this.resetPasswordForm = this.fb.group({
      password: ['', [Validators.required, Validators.minLength(5), this.passwordStrengthValidator]],
      confirmPassword: ['', Validators.required]
    }, { validators: this.passwordMatchValidator });

    // Real-time password matching validation
    this.resetPasswordForm.get('password')?.valueChanges.subscribe(() => {
      const confirmPasswordControl = this.resetPasswordForm.get('confirmPassword');
      if (confirmPasswordControl?.value) {
        confirmPasswordControl.updateValueAndValidity();
      }
    });

    this.resetPasswordForm.get('confirmPassword')?.valueChanges.subscribe(() => {
      this.resetPasswordForm.updateValueAndValidity();
    });
  }

  passwordMatchValidator(form: FormGroup) {
    const password = form.get('password');
    const confirmPassword = form.get('confirmPassword');
    
    if (password && confirmPassword) {
      if (password.value !== confirmPassword.value) {
        // Set error on confirmPassword field
        const errors = confirmPassword.errors || {};
        errors['passwordMismatch'] = true;
        confirmPassword.setErrors(errors);
        return { passwordMismatch: true };
      } else {
        // Clear passwordMismatch error if passwords match
        if (confirmPassword.errors && confirmPassword.errors['passwordMismatch']) {
          delete confirmPassword.errors['passwordMismatch'];
          const hasOtherErrors = Object.keys(confirmPassword.errors).length > 0;
          confirmPassword.setErrors(hasOtherErrors ? confirmPassword.errors : null);
        }
      }
    }
    
    return null;
  }

  passwordStrengthValidator(control: any) {
    const value = control.value;
    if (!value) return null;
    
    const hasUpperCase = /[A-Z]/.test(value);
    const hasLowerCase = /[a-z]/.test(value);
    const hasNumber = /[0-9]/.test(value);
    const hasSpecialChar = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(value);
    const minLength = value.length >= 5;
    
    const valid = hasUpperCase && hasLowerCase && hasNumber && hasSpecialChar && minLength;
    
    if (!valid) {
      return {
        passwordStrength: {
          hasUpperCase,
          hasLowerCase,
          hasNumber,
          hasSpecialChar,
          minLength
        }
      };
    }
    
    return null;
  }

  async onVerifyCode() {
    if (this.codeVerificationForm.invalid || !this.email) return;

    this.isLoading = true;
    const { code } = this.codeVerificationForm.value;

    try {
      await this.authService.verifyPasswordResetCode(this.email, code);
      this.isCodeVerified = true;
    } catch (error) {
      console.error('Error verifying code:', error);
    } finally {
      this.isLoading = false;
    }
  }

  async onResetPassword() {
    if (this.resetPasswordForm.invalid || !this.email || !this.isCodeVerified) return;

    this.isLoading = true;
    const { password } = this.resetPasswordForm.value;
    const { code } = this.codeVerificationForm.value;

    try {
      const result = await this.authService.resetPasswordWithCode(this.email, code, password);
      
      if (result.autoLogin) {
        // Auto-login successful, redirect to dashboard
        this.router.navigate([result.redirectTo || '/dashboard']);
      } else {
        // Fallback to login page
        this.router.navigate(['/auth/login']);
      }
    } finally {
      this.isLoading = false;
    }
  }

  async resendCode() {
    if (!this.email || !this.canResendCode) return;

    this.isLoading = true;
    try {
      await this.authService.forgotPassword(this.email);
      this.startResendCountdown();
    } finally {
      this.isLoading = false;
    }
  }

  private startResendCountdown() {
    this.canResendCode = false;
    this.resendCountdown = 60;
    
    const interval = setInterval(() => {
      this.resendCountdown--;
      if (this.resendCountdown <= 0) {
        this.canResendCode = true;
        clearInterval(interval);
      }
    }, 1000);
  }

  private getFieldDisplayName(fieldName: string): string {
    const fieldNames: { [key: string]: string } = {
      code: 'κωδικός επιβεβαίωσης',
      password: 'κωδικός πρόσβασης',
      confirmPassword: 'επιβεβαίωση κωδικού'
    };
    return fieldNames[fieldName] || fieldName;
  }

  getFieldError(fieldName: string, formGroup: FormGroup = this.resetPasswordForm): string {
    const field = formGroup.get(fieldName);
    if (field?.errors && field.touched) {
      const displayName = this.getFieldDisplayName(fieldName);
      if (field.errors['required']) return `Το πεδίο "${displayName}" είναι υποχρεωτικό`;
      if (field.errors['pattern'] && fieldName === 'code') return 'Ο κωδικός πρέπει να έχει 6 ψηφία';
      if (field.errors['minlength']) return `Ελάχιστοι χαρακτήρες: ${field.errors['minlength'].requiredLength}`;
      if (field.errors['maxlength']) return `Μέγιστοι χαρακτήρες: ${field.errors['maxlength'].requiredLength}`;
      if (field.errors['passwordMismatch']) return 'Οι κωδικοί δεν ταιριάζουν';
      if (field.errors['passwordStrength']) {
        const strength = field.errors['passwordStrength'];
        if (!strength.minLength) return 'Ο κωδικός πρέπει να έχει τουλάχιστον 5 χαρακτήρες';
        if (!strength.hasUpperCase) return 'Ο κωδικός πρέπει να περιέχει κεφαλαίο γράμμα';
        if (!strength.hasLowerCase) return 'Ο κωδικός πρέπει να περιέχει πεζό γράμμα';
        if (!strength.hasNumber) return 'Ο κωδικός πρέπει να περιέχει αριθμό';
        if (!strength.hasSpecialChar) return 'Ο κωδικός πρέπει να περιέχει ειδικό χαρακτήρα';
      }
    }
    return '';
  }
}