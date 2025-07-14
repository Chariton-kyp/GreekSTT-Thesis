import { CommonModule } from '@angular/common';
import { Component, inject, computed, ChangeDetectionStrategy, OnInit } from '@angular/core';
import { RouterModule } from '@angular/router';

import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { AvatarModule } from 'primeng/avatar';
import { DividerModule } from 'primeng/divider';

import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [
    CommonModule, 
    RouterModule,
    ButtonModule,
    CardModule,
    TagModule,
    AvatarModule,
    DividerModule
  ],
  templateUrl: './profile.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ProfileComponent implements OnInit {
  private readonly authService = inject(AuthService);

  // Use signals from AuthService
  readonly currentUser = this.authService.currentUser;
  readonly fullName = this.authService.fullName;
  readonly userInitials = this.authService.initials;
  readonly isEmailVerified = this.authService.isEmailVerified;

  readonly verificationStatus = computed(() => {
    const isVerified = this.isEmailVerified();
    return {
      text: isVerified ? 'Επιβεβαιωμένο' : 'Μη επιβεβαιωμένο',
      severity: isVerified ? 'success' as const : 'warning' as const,
      icon: isVerified ? 'pi pi-check-circle' : 'pi pi-exclamation-triangle'
    };
  });

  readonly memberSince = computed(() => {
    const user = this.currentUser();
    if (!user?.created_at) return 'Μη διαθέσιμο';
    
    const createdDate = new Date(user.created_at);
    return createdDate.toLocaleDateString('el-GR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  });

  readonly lastLoginDate = computed(() => {
    const user = this.currentUser();
    if (!user?.last_login) return 'Μη διαθέσιμο';
    
    // Handle UTC timestamp from backend
    let lastLogin = new Date(user.last_login);
    
    // If the timestamp doesn't have timezone info, treat as UTC
    if (typeof user.last_login === 'string' && !user.last_login.includes('+') && !user.last_login.includes('Z')) {
      lastLogin = new Date(user.last_login + 'Z');
    }
    
    // Calculate relative time
    const now = new Date();
    const diffMs = now.getTime() - lastLogin.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffMinutes < 60) {
      return `πριν από ${diffMinutes} λεπτά`;
    } else if (diffHours < 24) {
      return `πριν από ${diffHours} ώρες`;
    } else if (diffDays < 7) {
      return `πριν από ${diffDays} ημέρες`;
    } else {
      return lastLogin.toLocaleDateString('el-GR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  });

  async ngOnInit() {
    // Refresh user data when profile page opens
    try {
      await this.authService.refreshUserData();
    } catch (error) {
      console.warn('Failed to refresh user data:', error);
    }
  }
}