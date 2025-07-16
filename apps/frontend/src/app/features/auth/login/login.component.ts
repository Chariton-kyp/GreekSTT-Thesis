import { CommonModule } from '@angular/common';
import { Component, signal } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterModule, ActivatedRoute } from '@angular/router';
import { toObservable } from '@angular/core/rxjs-interop';

import { filter } from 'rxjs/operators';

import { ButtonModule } from 'primeng/button';
import { CheckboxModule } from 'primeng/checkbox';
import { DividerModule } from 'primeng/divider';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { RippleModule } from 'primeng/ripple';

import { BaseComponent } from '../../../core/patterns/base-component';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-login',
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
  templateUrl: './login.component.html',
})
export class LoginComponent extends BaseComponent {
  loginForm: FormGroup;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private route: ActivatedRoute
  ) {
    super();
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(5)]],
      remember_me: [false],
    });
  }

  async onSubmit() {
    if (!this.validateForm(this.loginForm)) {
      return;
    }

    this.loadingState.setLoading(true);
    const { email, password, remember_me } = this.loginForm.value;

    try {
      await this.authService.login({ email, password, remember_me });

      await this.waitForAuthInitialization();

      const currentUser = this.authService.currentUser();
      
      console.log('[LoginComponent] Post-login user state:', {
        hasUser: !!currentUser,
        emailVerified: currentUser?.email_verified,
        isAuthenticated: this.authService.isAuthenticated(),
        userId: currentUser?.id
      });
      
      if (currentUser && !currentUser.email_verified) {
        const returnUrl = this.route.snapshot.queryParamMap.get('returnUrl') || '/app/dashboard';
        
        this.router.navigate(['/auth/verify-email'], {
          queryParams: {
            reason: 'login_verification_required',
            email: email,
            returnUrl: returnUrl
          },
        });
        return;
      }

      const returnUrl = this.route.snapshot.queryParamMap.get('returnUrl') || '/app/dashboard';
      
      console.log('[LoginComponent] Navigating to:', returnUrl);
      
      this.router.navigate([returnUrl]);
    } finally {
      this.loadingState.setLoading(false);
    }
  }

  private async waitForAuthInitialization(): Promise<void> {
    return new Promise<void>((resolve) => {
      if (this.authService.isInitialized()) {
        resolve();
        return;
      }

      const academic_access = toObservable(this.authService.isInitialized)
        .pipe(filter((initialized: boolean) => initialized))
        .subscribe(() => {
          academic_access.unsubscribe();
          resolve();
        });
    });
  }
}
