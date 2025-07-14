import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal, HostListener, ElementRef } from '@angular/core';
import { Router, RouterModule } from '@angular/router';

import { ButtonModule } from 'primeng/button';

import { AuthService } from '../../core/services/auth.service';
import { ThemeService } from '../../core/services/theme.service';
import { SidebarService } from '../../core/services/sidebar.service';
@Component({
    selector: 'app-header',
    standalone: true,
    imports: [CommonModule, RouterModule, ButtonModule],
    templateUrl: './header.component.html'
})
export class HeaderComponent {
    private readonly authService = inject(AuthService);
    private readonly themeService = inject(ThemeService);
    private readonly router = inject(Router);
    private readonly elementRef = inject(ElementRef);
    private readonly sidebarService = inject(SidebarService);

    private _isUserMenuOpen = signal(false);

    // Computed signals
    readonly currentUser = this.authService.currentUser;
    readonly fullName = this.authService.fullName;
    readonly userInitials = this.authService.initials;
    readonly isDarkMode = this.themeService.isDarkMode;
    readonly isUserMenuOpen = this._isUserMenuOpen.asReadonly();
    readonly isSidebarCollapsed = this.sidebarService.isCollapsed;

    readonly usageText = computed(() => {
        // Academic version - no usage limits
        return 'Δοκιμαστική Έκδοση';
    });

    toggleTheme(): void {
        this.themeService.toggleTheme();
    }

    toggleUserMenu(): void {
        this._isUserMenuOpen.update((open) => !open);
    }

    closeUserMenu(): void {
        this._isUserMenuOpen.set(false);
    }

    toggleMobileSidebar(): void {
        this.sidebarService.toggleMobileSidebar();
    }

    toggleDesktopSidebar(): void {
        this.sidebarService.toggleSidebar();
    }

    closeAllMenus(): void {
        this.closeUserMenu();
    }

    async logout(): Promise<void> {
        try {
            await this.authService.logout();
            // Backend will provide logout success message via unified response
        } catch (error) {
            // Error interceptor handles error display automatically
        }
    }

    @HostListener('document:click', ['$event'])
    onDocumentClick(event: Event): void {
        const target = event.target as HTMLElement;
        const userMenuContainer = this.elementRef.nativeElement.querySelector('.user-menu-container');
        
        // Close user menu if clicking outside of it
        if (this.isUserMenuOpen() && userMenuContainer && !userMenuContainer.contains(target)) {
            this.closeUserMenu();
        }
    }
}
