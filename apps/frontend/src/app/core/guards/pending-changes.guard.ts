import { inject } from '@angular/core';
import { CanDeactivateFn } from '@angular/router';

import { ConfirmationService } from 'primeng/api';
import { Observable } from 'rxjs';

export interface CanComponentDeactivate {
  canDeactivate(): Observable<boolean> | Promise<boolean> | boolean;
  hasUnsavedChanges?(): boolean;
}

export const pendingChangesGuard: CanDeactivateFn<CanComponentDeactivate> = (component) => {
  const confirmationService = inject(ConfirmationService);

  // Check if component has unsaved changes
  if (component.hasUnsavedChanges && component.hasUnsavedChanges()) {
    return new Promise<boolean>((resolve) => {
      confirmationService.confirm({
        message: 'Έχετε μη αποθηκευμένες αλλαγές. Θέλετε να φύγετε χωρίς να τις αποθηκεύσετε;',
        header: 'Μη αποθηκευμένες αλλαγές',
        icon: 'pi pi-exclamation-triangle',
        acceptLabel: 'Ναι, φύγε',
        rejectLabel: 'Ακύρωση',
        accept: () => resolve(true),
        reject: () => resolve(false)
      });
    });
  }

  // Use component's own canDeactivate method if available
  if (component.canDeactivate) {
    return component.canDeactivate();
  }

  return true;
};