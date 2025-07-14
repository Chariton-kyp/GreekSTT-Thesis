import { CommonModule } from '@angular/common';
import { Component, ChangeDetectionStrategy, signal, inject, computed } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { HeaderComponent } from '../header/header.component';
import { SidebarComponent } from '../sidebar/sidebar.component';
import { SidebarService } from '../../core/services/sidebar.service';
import { BreadcrumbComponent } from '../../shared/components/breadcrumb/breadcrumb.component';

@Component({
  selector: 'app-main-layout',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    HeaderComponent,
    SidebarComponent,
    BreadcrumbComponent
  ],
  templateUrl: './main-layout.component.html',
  styleUrl: './main-layout.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class MainLayoutComponent {
  private readonly sidebarService = inject(SidebarService);
  
  readonly isSidebarCollapsed = this.sidebarService.isCollapsed;
  readonly isMobileSidebarOpen = this.sidebarService.isMobileOpen;
  
  readonly mainContentClass = computed(() => {
    const collapsed = this.isSidebarCollapsed();
    return collapsed ? 'lg:ml-16' : 'lg:ml-64';
  });
  
  toggleSidebar(): void {
    this.sidebarService.toggleMobileSidebar();
  }
  
  closeSidebar(): void {
    this.sidebarService.closeMobileSidebar();
  }
}