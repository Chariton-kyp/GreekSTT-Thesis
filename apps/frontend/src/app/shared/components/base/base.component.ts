import { Component, inject, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { ApiPatternsService } from '../../../core/services/api-patterns.service';
import { NotificationService } from '../../../core/services/notification.service';

/**
 * Base component class with standardized patterns
 * All components should extend this to get automatic API handling
 */
@Component({ template: '' })
export abstract class BaseComponent implements OnDestroy {
  // Core services available to all components
  protected readonly router = inject(Router);
  protected readonly notificationService = inject(NotificationService);
  protected readonly apiPatterns = inject(ApiPatternsService);

  // Destruction management
  protected readonly destroy$ = new Subject<void>();

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Subscribe to observables with automatic cleanup
   * Note: For signals, use effect() or toObservable() instead
   */
  protected subscribe<T>(observable: any, callback: (value: T) => void): void {
    if (observable && typeof observable.pipe === 'function') {
      observable.pipe(takeUntil(this.destroy$)).subscribe(callback);
    } else {
      console.warn('BaseComponent.subscribe: Expected an Observable, got:', typeof observable);
    }
  }

  /**
   * Standard form validation helper
   * Returns false if form is invalid and marks fields as touched
   */
  protected validateForm(form: any): boolean {
    if (form.invalid) {
      this.markFormGroupTouched(form);
      return false;
    }
    return true;
  }

  /**
   * Mark all form fields as touched
   */
  markFormGroupTouched(formGroup: any): void {
    Object.keys(formGroup.controls).forEach(key => {
      const control = formGroup.get(key);
      control?.markAsTouched();

      if (control?.controls) {
        this.markFormGroupTouched(control);
      }
    });
  }

  /**
   * Get field error message
   */
  getFieldError(form: any, fieldName: string): string {
    const field = form.get(fieldName);
    if (field?.errors && field.touched) {
      if (field.errors['required']) return 'Αυτό το πεδίο είναι υποχρεωτικό';
      if (field.errors['email']) return 'Μη έγκυρη διεύθυνση email';
      if (field.errors['minlength']) return `Ελάχιστο μήκος: ${field.errors['minlength'].requiredLength} χαρακτήρες`;
      if (field.errors['maxlength']) return `Μέγιστο μήκος: ${field.errors['maxlength'].requiredLength} χαρακτήρες`;
      if (field.errors['pattern']) return 'Μη έγκυρη μορφή';
      if (field.errors['min']) return `Ελάχιστη τιμή: ${field.errors['min'].min}`;
      if (field.errors['max']) return `Μέγιστη τιμή: ${field.errors['max'].max}`;
    }
    return '';
  }


  /**
   * Safe navigation (simplified for thesis)
   */
  protected navigateIfAllowed(route: string[]): void {
    // All navigation allowed for authenticated users in thesis version
    this.router.navigate(route);
  }
}

/**
 * Specialized base component for CRUD operations
 */
export abstract class BaseCrudComponent<T = any> extends BaseComponent {
  protected items: T[] = [];
  protected selectedItem: T | null = null;
  protected abstract entityName: string; // e.g., 'transcription', 'user', etc.

  /**
   * Load all items
   */
  protected async loadItems(): Promise<void> {
    const items = await this.apiPatterns.read<T[]>(this.getEndpoint()).toPromise();
    this.items = items || [];
  }

  /**
   * Create new item
   */
  protected async createItem(data: Partial<T>): Promise<boolean> {
    try {
      const newItem = await this.apiPatterns.create<T>(
        this.getEndpoint(), 
        data
      ).toPromise();
      
      if (newItem) {
        this.items.push(newItem);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Create item error:', error);
      return false;
    }
  }

  /**
   * Update existing item
   */
  protected async updateItem(id: string | number, data: Partial<T>): Promise<boolean> {
    try {
      const updatedItem = await this.apiPatterns.update<T>(
        `${this.getEndpoint()}/${id}`, 
        data
      ).toPromise();
      
      if (updatedItem) {
        const index = this.items.findIndex((item: any) => item.id === id);
        if (index !== -1) {
          this.items[index] = updatedItem;
        }
        return true;
      }
      return false;
    } catch (error) {
      console.error('Update item error:', error);
      return false;
    }
  }

  /**
   * Delete item
   */
  protected async deleteItem(id: string | number, name?: string): Promise<boolean> {
    try {
      await this.apiPatterns.delete(
        `${this.getEndpoint()}/${id}`
      ).toPromise();
      
      this.items = this.items.filter((item: any) => item.id !== id);
      if (this.selectedItem && (this.selectedItem as any).id === id) {
        this.selectedItem = null;
      }
      return true;
    } catch (error) {
      console.error('Delete item error:', error);
      return false;
    }
  }

  /**
   * Get the base endpoint for this entity
   */
  protected abstract getEndpoint(): string;
}

/**
 * Specialized base component for forms
 */
export abstract class BaseFormComponent<T = any> extends BaseComponent {
  protected abstract form: any; // FormGroup
  protected isEditMode = false;
  protected itemId: string | number | null = null;

  /**
   * Save form data
   */
  protected async save(): Promise<boolean> {
    if (!this.validateForm(this.form)) {
      return false;
    }

    const formData = this.form.value;
    
    try {
      if (this.isEditMode && this.itemId) {
        await this.apiPatterns.update(
          `${this.getEndpoint()}/${this.itemId}`, 
          formData
        ).toPromise();
      } else {
        await this.apiPatterns.create(
          this.getEndpoint(), 
          formData
        ).toPromise();
      }
      
      this.onSaveSuccess();
      return true;
    } catch (error) {
      console.error('Save error:', error);
      return false;
    }
  }

  /**
   * Load item for editing
   */
  protected async loadForEdit(id: string | number): Promise<void> {
    this.itemId = id;
    this.isEditMode = true;
    
    try {
      const item = await this.apiPatterns.read<T>(`${this.getEndpoint()}/${id}`).toPromise();
      if (item) {
        this.populateForm(item);
      }
    } catch (error) {
      console.error('Load for edit error:', error);
    }
  }

  /**
   * Populate form with item data
   */
  protected abstract populateForm(item: T): void;

  /**
   * Get the base endpoint
   */
  protected abstract getEndpoint(): string;

  /**
   * Called after successful save
   */
  protected onSaveSuccess(): void {
    // Override in components if needed
    this.router.navigate(['../']);
  }
}