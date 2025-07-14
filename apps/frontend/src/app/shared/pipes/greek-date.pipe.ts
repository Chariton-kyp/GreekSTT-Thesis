import { formatDate } from '@angular/common';
import { Pipe, PipeTransform, inject } from '@angular/core';
import { DateService, DateFormatOptions } from '../../core/services/date.service';

@Pipe({
  name: 'greekDate',
  standalone: true
})
export class GreekDatePipe implements PipeTransform {
  private dateService = inject(DateService);

  transform(value: Date | string | number | null | undefined, format: string = 'short'): string {
    if (!value) {
      return '';
    }

    // Handle special formats with DateService
    if (format === 'relative') {
      return this.dateService.getRelativeTime(value as Date | string);
    }
    
    if (format === 'smart') {
      return this.dateService.smartFormat(value as Date | string);
    }

    // For legacy compatibility, handle specific formats
    switch (format) {
      case 'short':
        return this.dateService.formatForDisplay(value as Date | string, { format: 'short' });
      
      case 'medium':
        return this.dateService.formatForDisplay(value as Date | string, { 
          format: 'medium', 
          includeTime: true 
        });
      
      case 'long':
        return this.dateService.formatForDisplay(value as Date | string, { 
          format: 'long', 
          includeTime: true 
        });
      
      case 'full':
        return this.dateService.formatForDisplay(value as Date | string, { 
          format: 'full', 
          includeTime: true 
        });
      
      case 'time':
        return this.dateService.formatForDisplay(value as Date | string, { 
          includeTime: true,
          format: 'short'
        });
      
      case 'timeWithSeconds':
        return this.dateService.formatForDisplay(value as Date | string, { 
          includeTime: true,
          includeSeconds: true,
          format: 'short'
        });
      
      case 'dateOnly':
        return this.dateService.formatForDisplay(value as Date | string, { format: 'medium' });
      
      case 'monthYear':
      case 'dayMonth':
        // Fallback to Angular's formatDate for these specific formats
        const monthYearDate = this.dateService.parseApiDate(value as string);
        if (!monthYearDate) return '';
        const locale = 'el-GR';
        return format === 'monthYear' 
          ? formatDate(monthYearDate, 'MMMM yyyy', locale)
          : formatDate(monthYearDate, 'dd MMMM', locale);
      
      case 'dateTime':
        // Handle dateTime format specifically
        return this.dateService.formatForDisplay(value as Date | string, { 
          format: 'medium', 
          includeTime: true 
        });
      
      default:
        // For custom format strings, use Angular's formatDate
        const customDate = this.dateService.parseApiDate(value as string);
        if (!customDate) return '';
        return formatDate(customDate, format, 'el-GR');
    }
  }
}