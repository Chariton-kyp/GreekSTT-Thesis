import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { Router, NavigationEnd, RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { Subject } from 'rxjs';
import { filter, takeUntil } from 'rxjs/operators';

import { BreadcrumbService } from '../../../core/services/breadcrumb.service';

@Component({
  selector: 'app-breadcrumb',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="breadcrumb-container">
      <nav class="custom-breadcrumb">
        @for (item of breadcrumbItems(); track $index) {
          @if ($index > 0) {
            <span class="breadcrumb-separator">/</span>
          }
          @if (item.routerLink) {
            <a [routerLink]="item.routerLink" class="breadcrumb-link">
              @if (item.icon) {
                <i [class]="item.icon"></i>
              }
              {{ item.label }}
            </a>
          } @else {
            <span class="breadcrumb-current">
              @if (item.icon) {
                <i [class]="item.icon"></i>
              }
              {{ item.label }}
            </span>
          }
        }
      </nav>
    </div>
  `,
  styles: [`

    .custom-breadcrumb {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 14px;
    }

    .breadcrumb-link {
      color: #64748b;
      text-decoration: none;
      display: flex;
      align-items: center;
      gap: 0.25rem;
      transition: color 0.15s ease;
    }

    .breadcrumb-link:hover {
      color: var(--color-accent-primary);
    }

    .breadcrumb-current {
      color: #1e293b;
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 0.25rem;
    }

    .breadcrumb-separator {
      color: #94a3b8;
      margin: 0 0.25rem;
    }

    /* Dark mode */
    :host-context(.dark) .breadcrumb-link {
      color: #d1d5db;
    }

    :host-context(.dark) .breadcrumb-link:hover {
      color: var(--color-accent-primary);
    }

    :host-context(.dark) .breadcrumb-current {
      color: #f9fafb;
    }

    :host-context(.dark) .breadcrumb-separator {
      color: #9ca3af;
    }

    :host ::ng-deep .p-breadcrumb {
      background: transparent;
      border: none;
      padding: 0;
    }

    :host ::ng-deep .p-breadcrumb .p-breadcrumb-list {
      gap: 0.5rem;
    }

    /* Style for current page (no link) - make it darker/more prominent */
    :host ::ng-deep .p-breadcrumb .p-menuitem:last-child .p-menuitem-text {
      color: #1e293b; /* Dark color for current page in light mode */
      font-weight: var(--font-weight-medium);
    }

    :host-context(.dark) ::ng-deep .p-breadcrumb .p-menuitem:last-child .p-menuitem-text {
      color: #f9fafb; /* Light color for current page in dark mode */
      font-weight: var(--font-weight-medium);
    }
  `]
})
export class BreadcrumbComponent implements OnInit, OnDestroy {
  private router = inject(Router);
  protected breadcrumbService = inject(BreadcrumbService);
  private destroy$ = new Subject<void>();

  homeItem = { label: 'Αρχική', icon: 'pi pi-home', routerLink: '/app' };
  
  // Expose the signal as a computed property
  breadcrumbItems = this.breadcrumbService.getBreadcrumbs();

  ngOnInit() {
    // Generate initial breadcrumbs
    this.generateBreadcrumbs(this.router.url);

    // Listen to route changes and update breadcrumbs
    this.router.events
      .pipe(
        filter(event => event instanceof NavigationEnd),
        takeUntil(this.destroy$)
      )
      .subscribe((event: NavigationEnd) => {
        this.generateBreadcrumbs(event.url);
      });
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private generateBreadcrumbs(url: string) {
    // Only generate breadcrumbs for app routes (authenticated routes)
    if (url.startsWith('/app')) {
      this.breadcrumbService.generateFromPath(url);
    } else {
      this.breadcrumbService.clearBreadcrumbs();
    }
  }
}