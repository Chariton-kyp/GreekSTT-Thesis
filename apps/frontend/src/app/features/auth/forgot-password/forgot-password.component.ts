import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';

import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';

import { BaseComponent } from '../../../core/patterns/base-component';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-forgot-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule, ButtonModule, InputTextModule],
  templateUrl: './forgot-password.component.html'
})
export class ForgotPasswordComponent extends BaseComponent {
  forgotPasswordForm: FormGroup;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService
  ) {
    super();
    this.forgotPasswordForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]]
    });
  }

  async onSubmit() {
    if (!this.validateForm(this.forgotPasswordForm)) return;

    this.loadingState.setLoading(true);
    const { email } = this.forgotPasswordForm.value;

    await this.authService.forgotPassword(email);
    this.loadingState.setLoading(false);
    this.router.navigate(['/auth/reset-password'], {
      queryParams: { email: email }
    });
  }
}