import { Injectable, inject } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';

import { NotificationService } from './notification.service';

export type MessageType = 'success' | 'error' | 'warning' | 'info' | 'validation';

export interface UnifiedMessage {
  message: string;
  type: MessageType;
  details?: any;
}

@Injectable({
  providedIn: 'root'
})
export class MessageService {
  private readonly notificationService = inject(NotificationService);

  /**
   * Handle any HTTP response or error and show appropriate toast
   */
  handleResponse(responseOrError: any, showNotification: boolean = true): UnifiedMessage {
    const result = this.extractMessage(responseOrError);
    
    if (showNotification) {
      this.showMessage(result);
    }
    
    return result;
  }

  /**
   * Extract message and type from any response or error
   */
  extractMessage(responseOrError: any): UnifiedMessage {
    // Handle successful responses
    if (this.isSuccessResponse(responseOrError)) {
      return this.extractFromSuccessResponse(responseOrError);
    }
    
    // Handle error responses
    return this.extractFromErrorResponse(responseOrError);
  }

  /**
   * Show success message with extracted data
   */
  showSuccess(response: any): void {
    const result = this.extractFromSuccessResponse(response);
    this.showMessage(result);
  }

  /**
   * Show error message with extracted data
   */
  showError(error: any): void {
    const result = this.extractFromErrorResponse(error);
    this.showMessage(result);
  }

  /**
   * Check if response is a success response
   */
  private isSuccessResponse(response: any): boolean {
    // Check for HTTP error response
    if (response instanceof HttpErrorResponse || response?.status >= 400) {
      return false;
    }
    
    // Check for explicit success field
    if (response?.success !== undefined) {
      return response.success === true;
    }
    
    // Check for error field (indicates error response)
    if (response?.error !== undefined) {
      return false;
    }
    
    // Default to success if no clear indicators
    return true;
  }

  /**
   * Extract message from success response
   */
  private extractFromSuccessResponse(response: any): UnifiedMessage {
    let message = 'Η ενέργεια ολοκληρώθηκε επιτυχώς';
    let type: MessageType = 'success';
    let details: any;

    // Extract from unified response format
    if (response?.message) {
      message = response.message;
    }
    
    if (response?.message_type) {
      type = response.message_type as MessageType;
    }
    
    if (response?.data) {
      details = response.data;
    }

    return { message, type, details };
  }

  /**
   * Extract message from error response
   */
  private extractFromErrorResponse(error: any): UnifiedMessage {
    let message = 'Παρουσιάστηκε ένα σφάλμα';
    let type: MessageType = 'error';
    let details: any;

    // Handle HttpErrorResponse
    if (error instanceof HttpErrorResponse) {
      const errorData = error.error;
      
      // Extract from unified response format
      if (errorData?.message) {
        message = errorData.message;
      }
      
      if (errorData?.message_type) {
        type = errorData.message_type as MessageType;
      } else {
        // Fallback: determine type from status code
        type = this.getMessageTypeFromStatus(error.status);
      }
      
      if (errorData?.details || errorData?.errors) {
        details = errorData.details || errorData.errors;
      }
    }
    // Handle direct error objects
    else if (error?.error) {
      const errorData = error.error;
      
      if (errorData?.message) {
        message = errorData.message;
      }
      
      if (errorData?.message_type) {
        type = errorData.message_type as MessageType;
      }
      
      if (errorData?.details || errorData?.errors) {
        details = errorData.details || errorData.errors;
      }
    }
    // Handle simple error objects
    else if (error?.message) {
      message = error.message;
      
      if (error?.message_type) {
        type = error.message_type as MessageType;
      }
    }
    // Handle string errors
    else if (typeof error === 'string') {
      message = error;
    }

    return { message, type, details };
  }

  /**
   * Determine message type from HTTP status code
   */
  private getMessageTypeFromStatus(status: number): MessageType {
    if (status >= 500) {
      return 'error';
    } else if (status === 422 || status === 400) {
      return 'validation';
    } else if (status === 401 || status === 403) {
      return 'error';
    } else if (status === 404 || status === 410) {
      return 'warning';
    } else if (status === 429) {
      return 'warning';
    } else {
      return 'error';
    }
  }

  /**
   * Show message using notification service based on type
   */
  private showMessage(result: UnifiedMessage): void {
    const { message, type, details } = result;
    
    switch (type) {
      case 'success':
        this.notificationService.showSuccess(message);
        break;
      case 'error':
        this.notificationService.showError(message);
        break;
      case 'warning':
        this.notificationService.showWarning(message);
        break;
      case 'info':
        this.notificationService.showInfo(message);
        break;
      case 'validation':
        if (details) {
          // Format validation errors
          const validationErrors = this.formatValidationErrors(details);
          this.notificationService.showError(message, validationErrors);
        } else {
          this.notificationService.showWarning(message);
        }
        break;
      default:
        this.notificationService.showError(message);
    }
  }

  /**
   * Format validation errors for display
   */
  private formatValidationErrors(details: any): string {
    if (typeof details === 'string') {
      return details;
    }
    
    if (Array.isArray(details)) {
      return details.join(', ');
    }
    
    if (typeof details === 'object') {
      const errors: string[] = [];
      Object.entries(details).forEach(([field, fieldErrors]) => {
        if (Array.isArray(fieldErrors)) {
          fieldErrors.forEach((error: string) => {
            errors.push(`${field}: ${error}`);
          });
        } else if (typeof fieldErrors === 'string') {
          errors.push(`${field}: ${fieldErrors}`);
        }
      });
      return errors.join(', ');
    }
    
    return '';
  }
}