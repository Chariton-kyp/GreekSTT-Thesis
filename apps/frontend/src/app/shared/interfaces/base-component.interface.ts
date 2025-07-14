import { OnDestroy, OnInit } from '@angular/core';

import { Subject } from 'rxjs';

/**
 * Base interface for all components in the application
 * Provides common patterns and lifecycle management
 */
export interface BaseComponent extends OnInit, OnDestroy {
  /**
   * Subject for managing component lifecycle and academic_accesss
   * Use this to automatically unsubscribe when component is destroyed
   */
  readonly destroy$: Subject<void>;

  /**
   * Initialize component
   * Override this method to add initialization logic
   */
  ngOnInit(): void;

  /**
   * Cleanup component
   * Override this method to add cleanup logic
   * The destroy$ subject will be automatically completed
   */
  ngOnDestroy(): void;
}

/**
 * Abstract base class implementing BaseComponent interface
 * Extend this class for components that need lifecycle management
 */
export abstract class BaseComponentImpl implements BaseComponent {
  readonly destroy$ = new Subject<void>();

  ngOnInit(): void {
    // Override in child components
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}

/**
 * Interface for components that handle loading states
 */
export interface LoadingStateComponent {
  readonly isLoading: boolean;
  readonly loadingMessage?: string;
}

/**
 * Interface for components that handle error states
 */
export interface ErrorStateComponent {
  readonly hasError: boolean;
  readonly errorMessage?: string;
  
  clearError?(): void;
}

/**
 * Interface for form components
 */
export interface FormComponent {
  readonly isValid: boolean;
  readonly isDirty: boolean;
  
  reset?(): void;
  submit?(): void;
}