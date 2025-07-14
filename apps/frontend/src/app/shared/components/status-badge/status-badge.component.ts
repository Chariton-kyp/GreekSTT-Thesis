import { CommonModule } from '@angular/common';
import { Component, Input, computed, ChangeDetectionStrategy } from '@angular/core';

export type StatusType = 'pending' | 'processing' | 'completed' | 'failed' | 'uploading' | 'cancelled';

@Component({
  selector: 'app-status-badge',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './status-badge.component.html',
  styleUrl: './status-badge.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class StatusBadgeComponent {
  @Input() status: StatusType = 'pending';
  @Input() size: 'small' | 'medium' | 'large' = 'medium';
  @Input() showIcon: boolean = true;
  @Input() customText?: string;
  @Input() customTooltip?: string;
  @Input() severity?: 'success' | 'info' | 'warning' | 'danger';
  @Input() label?: string;
  @Input() icon?: string;

  // Computed properties
  statusClass = computed(() => {
    const baseClass = `status-${this.status}`;
    const sizeClass = this.size !== 'medium' ? this.size : '';
    return [baseClass, sizeClass].filter(Boolean).join(' ');
  });

  iconClass = computed(() => {
    if (!this.showIcon) return '';
    
    if (this.icon) {
      return this.icon;
    }
    
    const iconMap: Record<StatusType, string> = {
      pending: 'pi pi-clock',
      processing: 'pi pi-spin pi-spinner',
      uploading: 'pi pi-upload',
      completed: 'pi pi-check-circle',
      failed: 'pi pi-times-circle',
      cancelled: 'pi pi-ban'
    };
    
    return iconMap[this.status] || 'pi pi-circle';
  });

  statusText = computed(() => {
    if (this.label) {
      return this.label;
    }
    
    if (this.customText) {
      return this.customText;
    }

    const textMap: Record<StatusType, string> = {
      pending: 'Εκκρεμεί',
      processing: 'Επεξεργασία',
      uploading: 'Μεταφόρτωση',
      completed: 'Ολοκληρώθηκε',
      failed: 'Αποτυχία',
      cancelled: 'Ακυρώθηκε'
    };
    
    return textMap[this.status] || 'Άγνωστο';
  });

  tooltip = computed(() => {
    if (this.customTooltip) {
      return this.customTooltip;
    }

    const tooltipMap: Record<StatusType, string> = {
      pending: 'Αναμένει επεξεργασία',
      processing: 'Επεξεργάζεται...',
      uploading: 'Γίνεται μεταφόρτωση...',
      completed: 'Ολοκληρώθηκε επιτυχώς',
      failed: 'Απέτυχε η επεξεργασία',
      cancelled: 'Ακυρώθηκε από τον χρήστη'
    };
    
    return tooltipMap[this.status] || '';
  });
}