import { Injectable, signal } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class SidebarService {
  private readonly _isCollapsed = signal(false);
  private readonly _isMobileOpen = signal(false);

  readonly isCollapsed = this._isCollapsed.asReadonly();
  readonly isMobileOpen = this._isMobileOpen.asReadonly();

  toggleSidebar(): void {
    this._isCollapsed.update(collapsed => !collapsed);
  }

  collapseSidebar(): void {
    this._isCollapsed.set(true);
  }

  expandSidebar(): void {
    this._isCollapsed.set(false);
  }

  openMobileSidebar(): void {
    this._isMobileOpen.set(true);
  }

  closeMobileSidebar(): void {
    this._isMobileOpen.set(false);
  }

  toggleMobileSidebar(): void {
    this._isMobileOpen.update(open => !open);
  }
}