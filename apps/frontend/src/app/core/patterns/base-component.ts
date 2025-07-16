import { inject, OnDestroy, Component } from '@angular/core';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { ApiPatterns, createLoadingState, createPaginationState } from './api-patterns';
import { MessageService } from '../services/message.service';

@Component({ template: '' })
export abstract class BaseComponent implements OnDestroy {
  protected readonly router = inject(Router);
  protected readonly messageService = inject(MessageService);
  protected readonly apiPatterns = new ApiPatterns();

  protected readonly loadingState = createLoadingState();
  protected readonly paginationState = createPaginationState();

  protected readonly destroy$ = new Subject<void>();

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  protected subscribe<T>(observable: any, callback: (value: T) => void): void {
    if (observable && typeof observable.pipe === 'function') {
      observable.pipe(takeUntil(this.destroy$)).subscribe(callback);
    } else {
      console.warn('BaseComponent.subscribe: Expected an Observable, got:', typeof observable);
    }
  }

  protected validateForm(form: any): boolean {
    if (form.invalid) {
      this.markFormGroupTouched(form);
      return false;
    }
    return true;
  }

  markFormGroupTouched(formGroup: any): void {
    Object.keys(formGroup.controls).forEach(key => {
      const control = formGroup.get(key);
      control?.markAsTouched();

      if (control?.controls) {
        this.markFormGroupTouched(control);
      }
    });
  }

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

  protected navigateIfAllowed(route: string[]): void {
    this.router.navigate(route);
  }
}

export abstract class BaseCrudComponent<T = any> extends BaseComponent {
  protected items: T[] = [];
  protected selectedItem: T | null = null;
  protected abstract entityName: string;

  protected async loadItems(): Promise<void> {
    this.loadingState.setLoading(true);
    this.items = await this.apiPatterns.read<T[]>(this.getEndpoint()) || [];
    this.loadingState.setLoading(false);
  }

  protected async createItem(data: Partial<T>): Promise<boolean> {
    const newItem = await this.apiPatterns.create<T>(
      this.getEndpoint(), 
      data
    );
    
    if (newItem) {
      this.items.push(newItem);
      return true;
    }
    return false;
  }

  protected async updateItem(id: string | number, data: Partial<T>): Promise<boolean> {
    const updatedItem = await this.apiPatterns.update<T>(
      `${this.getEndpoint()}/${id}`, 
      data
    );
    
    if (updatedItem) {
      const index = this.items.findIndex((item: any) => item.id === id);
      if (index !== -1) {
        this.items[index] = updatedItem;
      }
      return true;
    }
    return false;
  }

  protected async deleteItem(id: string | number, name?: string): Promise<boolean> {
    await this.apiPatterns.delete(
      `${this.getEndpoint()}/${id}`
    );
    
    this.items = this.items.filter((item: any) => item.id !== id);
    if (this.selectedItem && (this.selectedItem as any).id === id) {
      this.selectedItem = null;
    }
    return true;
  }

  protected abstract getEndpoint(): string;
}

export abstract class BaseFormComponent<T = any> extends BaseComponent {
  protected abstract form: any;
  protected isEditMode = false;
  protected itemId: string | number | null = null;

  protected async save(): Promise<boolean> {
    if (!this.validateForm(this.form)) {
      return false;
    }

    const formData = this.form.value;
    
    if (this.isEditMode && this.itemId) {
      await this.apiPatterns.update(
        `${this.getEndpoint()}/${this.itemId}`, 
        formData
      );
    } else {
      await this.apiPatterns.create(
        this.getEndpoint(), 
        formData
      );
    }
    
    this.onSaveSuccess();
    return true;
  }

  protected async loadForEdit(id: string | number): Promise<void> {
    this.itemId = id;
    this.isEditMode = true;
    
    const item = await this.apiPatterns.read<T>(`${this.getEndpoint()}/${id}`);
    if (item) {
      this.populateForm(item);
    }
  }

  protected abstract populateForm(item: T): void;

  protected abstract getEndpoint(): string;

  protected onSaveSuccess(): void {
    this.router.navigate(['../']);
  }
}