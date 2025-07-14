import { CommonModule } from '@angular/common';
import { Component, inject, signal, computed, ChangeDetectionStrategy, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterModule } from '@angular/router';

import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { MessageModule } from 'primeng/message';
import { DividerModule } from 'primeng/divider';

import { BaseComponent } from '../../../core/patterns/base-component';
import { ApiService } from '../../../core/services/api.service';
import { AuthService } from '../../../core/services/auth.service';
import { UserSettingsData } from '../../../core/models/user.model';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [
    CommonModule, 
    ReactiveFormsModule, 
    RouterModule,
    ButtonModule,
    CardModule,
    InputTextModule,
    PasswordModule,
    MessageModule,
    DividerModule
  ],
  templateUrl: './settings.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class SettingsComponent extends BaseComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly apiService = inject(ApiService);

  // Signals
  private _isUpdatingProfile = signal(false);
  private _isChangingPassword = signal(false);

  readonly isUpdatingProfile = this._isUpdatingProfile.asReadonly();
  readonly isChangingPassword = this._isChangingPassword.asReadonly();
  
  readonly currentUser = this.authService.currentUser;

  // Forms
  readonly profileForm = this.fb.group({
    first_name: ['', [Validators.required, Validators.minLength(2)]],
    last_name: ['', [Validators.required, Validators.minLength(2)]],
    email: ['', [Validators.required, Validators.email]],
    phone: [''],
    organization: ['']
  });

  readonly passwordForm = this.fb.group({
    currentPassword: ['', Validators.required],
    newPassword: ['', [Validators.required, Validators.minLength(5)]],
    confirmPassword: ['', Validators.required]
  }, { validators: this.passwordMatchValidator });

  constructor() {
    super();
    // Form initialization is handled in ngOnInit() with proper settings data
    // No need for effect() that would overwrite with masked data
  }

  passwordMatchValidator(form: FormGroup) {
    const newPassword = form.get('newPassword');
    const confirmPassword = form.get('confirmPassword');

    if (newPassword && confirmPassword && newPassword.value !== confirmPassword.value) {
      confirmPassword.setErrors({ passwordMismatch: true });
      return { passwordMismatch: true };
    }

    return null;
  }

  async onUpdateProfile() {
    if (!this.validateForm(this.profileForm)) return;

    this._isUpdatingProfile.set(true);
    
    try {
      const formData = this.profileForm.value;
      // Convert to backend expected format (snake_case)
      const updateData = {
        first_name: formData.first_name,
        last_name: formData.last_name,
        email: formData.email,
        phone: formData.phone,
        organization: formData.organization,
      };

      const response = await this.apiPatterns.update('/users/profile', updateData);
      const updatedData = (response as any)?.data || response;
      
      // Update form with fresh data from backend (no need to call /users/me)
      this.profileForm.patchValue({
        first_name: updatedData.first_name || '',
        last_name: updatedData.last_name || '',
        email: updatedData.email || '',
        phone: updatedData.phone || '',
        organization: updatedData.organization || ''
      });
      
      // No need to refresh user data - the profile page will refresh on navigation
      // and the update response contains everything we need for the form
      
    } catch (error) {
      console.error('Profile update failed:', error);
    } finally {
      this._isUpdatingProfile.set(false);
    }
  }

  async onChangePassword() {
    if (!this.validateForm(this.passwordForm)) return;

    this._isChangingPassword.set(true);
    await this.apiPatterns.create('/users/change-password', {
      current_password: this.passwordForm.value.currentPassword,
      new_password: this.passwordForm.value.newPassword,
    });
    this.passwordForm.reset();
    this._isChangingPassword.set(false);
  }

  async ngOnInit() {
    // Load full user data for settings form (includes unmasked email/phone)
    try {
      const response = await this.apiPatterns.read<UserSettingsData>('/users/me/settings');
      const settingsData = (response as any)?.data || response;
      
      // Populate form with full data for editing
      this.profileForm.patchValue({
        first_name: settingsData.first_name || '',
        last_name: settingsData.last_name || '',
        email: settingsData.email || '',
        phone: settingsData.phone || '',
        organization: settingsData.organization || ''
      });
    } catch (error) {
      console.warn('Failed to load settings data:', error);
      // Fallback to auth service data if settings endpoint fails
      await this.authService.refreshUserData();
    }
  }
}
