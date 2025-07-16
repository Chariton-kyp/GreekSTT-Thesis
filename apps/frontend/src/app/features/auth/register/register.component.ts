import { CommonModule } from '@angular/common';
import { Component, OnInit, signal } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterModule, ActivatedRoute } from '@angular/router';

import { ButtonModule } from 'primeng/button';
import { CheckboxModule } from 'primeng/checkbox';
import { DividerModule } from 'primeng/divider';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { RippleModule } from 'primeng/ripple';

import { BaseComponent } from '../../../core/patterns/base-component';
import { AuthService } from '../../../core/services/auth.service';
import { CooldownService } from '../../../core/services/cooldown.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterModule,
    ButtonModule,
    InputTextModule,
    PasswordModule,
    CheckboxModule,
    DividerModule,
    RippleModule,
  ],
  templateUrl: './register.component.html',
})
export class RegisterComponent extends BaseComponent {
  registerForm: FormGroup;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private route: ActivatedRoute,
    private cooldownService: CooldownService
  ) {
    super();
    this.registerForm = this.fb.group(
      {
        first_name: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(50)]],
        last_name: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(50)]],
        email: ['', [Validators.required, Validators.email]],
        username: [
          '',
          [
            Validators.required,
            Validators.minLength(3),
            Validators.maxLength(80),
            Validators.pattern(/^[a-zA-Z0-9._-]+$/),
          ],
        ],
        phone: ['', Validators.pattern(/^\+?[1-9]\d{1,14}$/)],
        organization: ['', Validators.maxLength(100)],
        password: ['', [Validators.required, Validators.minLength(5), this.passwordStrengthValidator]],
        confirmPassword: ['', Validators.required],
        acceptTerms: [false, Validators.requiredTrue],
      },
      { validators: this.passwordMatchValidator },
    );
  }

  passwordMatchValidator(form: FormGroup) {
    const password = form.get('password');
    const confirmPassword = form.get('confirmPassword');

    if (password && confirmPassword && password.value !== confirmPassword.value) {
      confirmPassword.setErrors({ passwordMismatch: true });
      return { passwordMismatch: true };
    }

    return null;
  }

  passwordStrengthValidator(control: any) {
    const value = control.value;
    if (!value) return null;

    const hasUpperCase = /[A-Z]/.test(value);
    const hasLowerCase = /[a-z]/.test(value);
    const hasNumber = /[0-9]/.test(value);
    const minLength = value.length >= 5;

    const valid = hasUpperCase && hasLowerCase && hasNumber && minLength;

    if (!valid) {
      return {
        passwordStrength: {
          hasUpperCase,
          hasLowerCase,
          hasNumber,
          minLength,
        },
      };
    }

    return null;
  }

  async onSubmit() {
    if (!this.validateForm(this.registerForm)) {
      return;
    }

    this.loadingState.setLoading(true);
    const formData = this.registerForm.value;

    const registerData = {
      first_name: formData.first_name.trim(),
      last_name: formData.last_name.trim(),
      email: formData.email.trim().toLowerCase(),
      username: formData.username.trim(),
      password: formData.password,
      phone: formData.phone?.trim() || undefined,
      organization: formData.organization?.trim() || undefined,
    };

    try {
      const result = await this.authService.register(registerData);

      if (result.requiresVerification) {
        this.cooldownService.startCooldown('email_verification_resend', 120);
        
        this.router.navigate(['/auth/verify-email'], {
          queryParams: {
            reason: 'registration_complete',
            email: registerData.email,
          },
        });
      } else {
        this.router.navigate(['/app/dashboard']);
      }
    } finally {
      this.loadingState.setLoading(false);
    }
  }

  private getFieldDisplayName(fieldName: string): string {
    const fieldNames: { [key: string]: string } = {
      first_name: 'όνομα',
      last_name: 'επώνυμο',
      email: 'email',
      username: 'όνομα χρήστη',
      phone: 'τηλέφωνο',
      organization: 'οργανισμός',
      password: 'κωδικός πρόσβασης',
      confirmPassword: 'επιβεβαίωση κωδικού',
      acceptTerms: 'αποδοχή όρων',
    };
    return fieldNames[fieldName] || fieldName;
  }

  override getFieldError(form: any, fieldName: string): string {
    const field = form.get(fieldName);
    if (field?.errors && field.touched) {
      const displayName = this.getFieldDisplayName(fieldName);
      if (field.errors['required']) return `Το πεδίο "${displayName}" είναι υποχρεωτικό`;
      if (field.errors['email']) return 'Μη έγκυρη διεύθυνση email';
      if (field.errors['minlength']) return `Ελάχιστοι χαρακτήρες: ${field.errors['minlength'].requiredLength}`;
      if (field.errors['maxlength']) return `Μέγιστοι χαρακτήρες: ${field.errors['maxlength'].requiredLength}`;
      if (field.errors['pattern'] && fieldName === 'username')
        return 'Μόνο γράμματα, αριθμοί, τελεία, παύλα και κάτω παύλα';
      if (field.errors['pattern'] && fieldName === 'phone') return 'Μη έγκυρος αριθμός τηλεφώνου';
      if (field.errors['passwordMismatch']) return 'Οι κωδικοί δεν ταιριάζουν';
      if (field.errors['passwordStrength']) {
        const strength = field.errors['passwordStrength'];
        if (!strength.minLength) return 'Ο κωδικός πρέπει να έχει τουλάχιστον 5 χαρακτήρες';
        if (!strength.hasUpperCase) return 'Ο κωδικός πρέπει να περιέχει κεφαλαίο γράμμα';
        if (!strength.hasLowerCase) return 'Ο κωδικός πρέπει να περιέχει πεζό γράμμα';
        if (!strength.hasNumber) return 'Ο κωδικός πρέπει να περιέχει αριθμό';
      }
      if (field.errors['requiredTrue']) return 'Πρέπει να αποδεχτείτε τους όρους χρήσης';
    }
    return '';
  }
}
