import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal, input } from '@angular/core';
import { Router, RouterModule, NavigationEnd } from '@angular/router';

import { filter } from 'rxjs/operators';

import { AuthService } from '../../core/services/auth.service';
import { LogoComponent } from '../../shared/components/logo/logo.component';

interface NavItem {
  label: string;
  icon: string;
  route: string;
  badge?: string;
  description?: string;
  children?: NavItem[];
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule, LogoComponent],
  templateUrl: './sidebar.component.html'
})
export class SidebarComponent {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  readonly isMobile = input<boolean>(false);
  readonly isCollapsed = input<boolean>(false);
  private _expandedSections = signal<Set<string>>(new Set(['Μεταγραφές']));

  readonly currentUser = this.authService.currentUser;

  readonly navItems: NavItem[] = [
    {
      label: 'Αρχική Σελίδα',
      icon: '🏠',
      route: '/app/dashboard'
    },
    {
      label: 'Μεταγραφές',
      icon: '🎙️',
      route: '/app/transcriptions',
      children: [
        {
          label: 'Όλες οι Μεταγραφές',
          icon: '📋',
          route: '/app/transcriptions',
          description: 'Προβολή και διαχείριση όλων των μεταγραφών'
        }
      ]
    },
    {
      label: 'Αναλυτικά Στοιχεία',
      icon: '📈',
      route: '/app/analytics',
      children: [
        {
          label: 'Αναλυτικός Πίνακας',
          icon: '🎯',
          route: '/app/analytics/dashboard',
          description: 'Dashboard με στατιστικά'
        }
      ]
    }
  ];

  readonly visibleNavItems = computed(() => {
    // Simplified for academic version - all users get same navigation
    return this.navItems.filter(item => this.authService.isAuthenticated());
  });

  readonly usageText = computed(() => {
    // Academic version - no usage limits
    return 'Δοκιμαστική Έκδοση';
  });

  getSidebarClasses(): string {
    const baseClasses = 'bg-white dark:bg-gray-800 h-screen flex flex-col border-r border-gray-200 dark:border-gray-700 transition-all duration-300';
    
    if (this.isMobile()) {
      return `${baseClasses} w-64`;
    }
    
    const width = this.isCollapsed() ? 'w-16' : 'w-64';
    const overflow = this.isCollapsed() ? 'overflow-hidden' : '';
    return `${baseClasses} ${width} ${overflow} fixed left-0 top-0 z-40`;
  }

  getNavItemClasses(): string {
    const baseClasses = 'group flex items-center py-2 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 hover:bg-cyan-50 dark:hover:bg-cyan-900/20 hover:text-cyan-700 dark:hover:text-cyan-300 transition-colors duration-150';
    
    if (this.isCollapsed() && !this.isMobile()) {
      return `${baseClasses} px-2 justify-center`; // Less padding for collapsed state
    }
    
    return `${baseClasses} px-3`; // Normal padding for expanded state
  }

  getIconClasses(): string {
    const baseClasses = 'h-5 w-5 transition-all duration-300 text-current';
    
    if (this.isCollapsed() && !this.isMobile()) {
      return baseClasses;
    }
    
    return `${baseClasses} mr-3`;
  }

  getMainChildRoute(item: NavItem): string {
    if (item.children && item.children.length > 0) {
      return item.children[0].route;
    }
    return item.route || '/app/dashboard';
  }

  getNavClasses(): string {
    const baseClasses = 'flex-1 py-6 space-y-2';
    
    if (this.isCollapsed() && !this.isMobile()) {
      return `${baseClasses} px-2 overflow-hidden`; // No scroll for collapsed state
    }
    
    return `${baseClasses} px-4 overflow-y-auto`; // Normal scroll for expanded state
  }

  constructor() {
    // Auto-expand current section based on route
    this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe(() => {
        this.updateExpandedSectionsFromRoute();
      });
  }

  toggleSection(sectionLabel: string): void {
    this._expandedSections.update(sections => {
      const newSections = new Set(sections);
      if (newSections.has(sectionLabel)) {
        newSections.delete(sectionLabel);
      } else {
        newSections.add(sectionLabel);
      }
      return newSections;
    });
  }

  isExpanded(sectionLabel: string): boolean {
    return this._expandedSections().has(sectionLabel);
  }

  getChildDescription(child: NavItem): string {
    const descriptions: Record<string, string> = {
      'Νέα Μεταγραφή': 'Δημιουργία νέας μεταγραφής',
      'Όλες οι Μεταγραφές': 'Προβολή όλων των μεταγραφών',
      'Μαζική Μεταγραφή': 'Μεταγραφή πολλαπλών αρχείων'
    };
    return descriptions[child.label] || '';
  }

  getSubmenuPosition(): number {
    // Position submenu at approximately the same height as the Μεταγραφές button
    // Header height (64px) + padding + first item (Dashboard) + second item (Μεταγραφές partial)
    return 64 + 24 + 40 + 10; // Approximately 138px from top
  }

  private updateExpandedSectionsFromRoute(): void {
    const currentUrl = this.router.url;
    
    // Auto-expand sections based on current route
    this.navItems.forEach(item => {
      if (item.children) {
        const hasActiveChild = item.children.some(child => 
          currentUrl.startsWith(child.route)
        );
        
        if (hasActiveChild) {
          this._expandedSections.update(sections => {
            const newSections = new Set(sections);
            newSections.add(item.label);
            return newSections;
          });
        }
      }
    });
  }
}