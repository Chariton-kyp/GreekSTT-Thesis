import { Injectable } from '@angular/core';

export interface DateFormatOptions {
  includeTime?: boolean;
  includeSeconds?: boolean;
  format?: 'short' | 'medium' | 'long' | 'full';
  locale?: string;
}

export interface LocaleConfig {
  locale: string;
  dateFormats: {
    short: Intl.DateTimeFormatOptions;
    medium: Intl.DateTimeFormatOptions;
    long: Intl.DateTimeFormatOptions;
    full: Intl.DateTimeFormatOptions;
  };
  relativeTimeStrings: {
    justNow: string;
    minutesAgo: (n: number) => string;
    hoursAgo: (n: number) => string;
    daysAgo: (n: number) => string;
    weeksAgo: (n: number) => string;
    monthsAgo: (n: number) => string;
    yearsAgo: (n: number) => string;
    inMinutes: (n: number) => string;
    inHours: (n: number) => string;
    inDays: (n: number) => string;
  };
}

@Injectable({
  providedIn: 'root'
})
export class DateService {
  private readonly serverTimezone = 'Europe/Athens';
  
  // Locale configurations for international support
  private readonly localeConfigs: Record<string, LocaleConfig> = {
    'el-GR': {
      locale: 'el-GR',
      dateFormats: {
        short: { day: '2-digit', month: '2-digit', year: '2-digit' },
        medium: { day: '2-digit', month: '2-digit', year: 'numeric' },
        long: { day: 'numeric', month: 'long', year: 'numeric' },
        full: { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }
      },
      relativeTimeStrings: {
        justNow: 'πριν από λίγο',
        minutesAgo: (n: number) => `πριν από ${n} ${n === 1 ? 'λεπτό' : 'λεπτά'}`,
        hoursAgo: (n: number) => `πριν από ${n} ${n === 1 ? 'ώρα' : 'ώρες'}`,
        daysAgo: (n: number) => `πριν από ${n} ${n === 1 ? 'ημέρα' : 'ημέρες'}`,
        weeksAgo: (n: number) => `πριν από ${n} ${n === 1 ? 'εβδομάδα' : 'εβδομάδες'}`,
        monthsAgo: (n: number) => `πριν από ${n} ${n === 1 ? 'μήνα' : 'μήνες'}`,
        yearsAgo: (n: number) => `πριν από ${n} ${n === 1 ? 'έτος' : 'έτη'}`,
        inMinutes: (n: number) => `σε ${n} ${n === 1 ? 'λεπτό' : 'λεπτά'}`,
        inHours: (n: number) => `σε ${n} ${n === 1 ? 'ώρα' : 'ώρες'}`,
        inDays: (n: number) => `σε ${n} ${n === 1 ? 'ημέρα' : 'ημέρες'}`
      }
    },
    'en-US': {
      locale: 'en-US',
      dateFormats: {
        short: { day: '2-digit', month: '2-digit', year: '2-digit' },
        medium: { day: '2-digit', month: '2-digit', year: 'numeric' },
        long: { day: 'numeric', month: 'long', year: 'numeric' },
        full: { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }
      },
      relativeTimeStrings: {
        justNow: 'just now',
        minutesAgo: (n: number) => `${n} minute${n !== 1 ? 's' : ''} ago`,
        hoursAgo: (n: number) => `${n} hour${n !== 1 ? 's' : ''} ago`,
        daysAgo: (n: number) => `${n} day${n !== 1 ? 's' : ''} ago`,
        weeksAgo: (n: number) => `${n} week${n !== 1 ? 's' : ''} ago`,
        monthsAgo: (n: number) => `${n} month${n !== 1 ? 's' : ''} ago`,
        yearsAgo: (n: number) => `${n} year${n !== 1 ? 's' : ''} ago`,
        inMinutes: (n: number) => `in ${n} minute${n !== 1 ? 's' : ''}`,
        inHours: (n: number) => `in ${n} hour${n !== 1 ? 's' : ''}`,
        inDays: (n: number) => `in ${n} day${n !== 1 ? 's' : ''}`
      }
    },
    'en-GB': {
      locale: 'en-GB',
      dateFormats: {
        short: { day: '2-digit', month: '2-digit', year: '2-digit' },
        medium: { day: '2-digit', month: '2-digit', year: 'numeric' },
        long: { day: 'numeric', month: 'long', year: 'numeric' },
        full: { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }
      },
      relativeTimeStrings: {
        justNow: 'just now',
        minutesAgo: (n: number) => `${n} minute${n !== 1 ? 's' : ''} ago`,
        hoursAgo: (n: number) => `${n} hour${n !== 1 ? 's' : ''} ago`,
        daysAgo: (n: number) => `${n} day${n !== 1 ? 's' : ''} ago`,
        weeksAgo: (n: number) => `${n} week${n !== 1 ? 's' : ''} ago`,
        monthsAgo: (n: number) => `${n} month${n !== 1 ? 's' : ''} ago`,
        yearsAgo: (n: number) => `${n} year${n !== 1 ? 's' : ''} ago`,
        inMinutes: (n: number) => `in ${n} minute${n !== 1 ? 's' : ''}`,
        inHours: (n: number) => `in ${n} hour${n !== 1 ? 's' : ''}`,
        inDays: (n: number) => `in ${n} day${n !== 1 ? 's' : ''}`
      }
    },
    'de-DE': {
      locale: 'de-DE',
      dateFormats: {
        short: { day: '2-digit', month: '2-digit', year: '2-digit' },
        medium: { day: '2-digit', month: '2-digit', year: 'numeric' },
        long: { day: 'numeric', month: 'long', year: 'numeric' },
        full: { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }
      },
      relativeTimeStrings: {
        justNow: 'gerade eben',
        minutesAgo: (n: number) => `vor ${n} Minute${n !== 1 ? 'n' : ''}`,
        hoursAgo: (n: number) => `vor ${n} Stunde${n !== 1 ? 'n' : ''}`,
        daysAgo: (n: number) => `vor ${n} Tag${n !== 1 ? 'en' : ''}`,
        weeksAgo: (n: number) => `vor ${n} Woche${n !== 1 ? 'n' : ''}`,
        monthsAgo: (n: number) => `vor ${n} Monat${n !== 1 ? 'en' : ''}`,
        yearsAgo: (n: number) => `vor ${n} Jahr${n !== 1 ? 'en' : ''}`,
        inMinutes: (n: number) => `in ${n} Minute${n !== 1 ? 'n' : ''}`,
        inHours: (n: number) => `in ${n} Stunde${n !== 1 ? 'n' : ''}`,
        inDays: (n: number) => `in ${n} Tag${n !== 1 ? 'en' : ''}`
      }
    },
    'fr-FR': {
      locale: 'fr-FR',
      dateFormats: {
        short: { day: '2-digit', month: '2-digit', year: '2-digit' },
        medium: { day: '2-digit', month: '2-digit', year: 'numeric' },
        long: { day: 'numeric', month: 'long', year: 'numeric' },
        full: { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }
      },
      relativeTimeStrings: {
        justNow: 'à l\'instant',
        minutesAgo: (n: number) => `il y a ${n} minute${n !== 1 ? 's' : ''}`,
        hoursAgo: (n: number) => `il y a ${n} heure${n !== 1 ? 's' : ''}`,
        daysAgo: (n: number) => `il y a ${n} jour${n !== 1 ? 's' : ''}`,
        weeksAgo: (n: number) => `il y a ${n} semaine${n !== 1 ? 's' : ''}`,
        monthsAgo: (n: number) => `il y a ${n} mois`,
        yearsAgo: (n: number) => `il y a ${n} an${n !== 1 ? 's' : ''}`,
        inMinutes: (n: number) => `dans ${n} minute${n !== 1 ? 's' : ''}`,
        inHours: (n: number) => `dans ${n} heure${n !== 1 ? 's' : ''}`,
        inDays: (n: number) => `dans ${n} jour${n !== 1 ? 's' : ''}`
      }
    }
  };
  
  /**
   * Get user's preferred locale (can be extended to check user settings)
   */
  private getUserLocale(): string {
    // For now, detect from browser language with Greek as fallback
    // In the future, this could check user preferences from backend
    const browserLang = navigator.language;
    
    // Check if we have a specific locale config
    if (this.localeConfigs[browserLang]) {
      return browserLang;
    }
    
    // Check if we have a language config (e.g., 'en' from 'en-US')
    const langCode = browserLang.split('-')[0];
    const matchingLocale = Object.keys(this.localeConfigs).find(locale => 
      locale.startsWith(langCode)
    );
    
    if (matchingLocale) {
      return matchingLocale;
    }
    
    // Default to Greek for now (can be changed to 'en-US' for international default)
    return 'el-GR';
  }
  
  /**
   * Get locale configuration
   */
  private getLocaleConfig(): LocaleConfig {
    const userLocale = this.getUserLocale();
    return this.localeConfigs[userLocale] || this.localeConfigs['el-GR'];
  }
  
  /**
   * Parse API date string to Date object
   * Handles ISO strings from backend properly
   */
  parseApiDate(dateString: string | null | undefined): Date | null {
    if (!dateString) return null;
    
    try {
      // Backend sends ISO strings in UTC, create Date object
      const date = new Date(dateString);
      
      // Validate the date
      if (isNaN(date.getTime())) {
        console.warn('Invalid date string received from API:', dateString);
        return null;
      }
      
      return date;
    } catch (error) {
      console.error('Error parsing date from API:', dateString, error);
      return null;
    }
  }

  /**
   * Format date for display to user
   * Always displays in user's local timezone with proper localization
   */
  formatForDisplay(
    date: Date | string | null | undefined, 
    options: DateFormatOptions = {}
  ): string {
    const parsedDate = typeof date === 'string' ? this.parseApiDate(date) : date;
    
    if (!parsedDate) return '-';

    const {
      includeTime = false,
      includeSeconds = false,
      format = 'medium',
      locale
    } = options;

    try {
      const localeConfig = this.getLocaleConfig();
      const targetLocale = locale || localeConfig.locale;
      
      // Get base format options from locale config
      const formatOptions: Intl.DateTimeFormatOptions = {
        ...localeConfig.dateFormats[format],
        timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone, // User's timezone
      };

      // Always use dd/mm/yyyy format for medium and short formats in this app
      if (format === 'medium' || format === 'short') {
        const day = parsedDate.getDate().toString().padStart(2, '0');
        const month = (parsedDate.getMonth() + 1).toString().padStart(2, '0');
        const year = parsedDate.getFullYear();
        
        let dateString = `${day}/${month}/${year}`;
        
        // Add time formatting if requested
        if (includeTime) {
          const hours = parsedDate.getHours().toString().padStart(2, '0');
          const minutes = parsedDate.getMinutes().toString().padStart(2, '0');
          
          if (includeSeconds) {
            const seconds = parsedDate.getSeconds().toString().padStart(2, '0');
            dateString += `, ${hours}:${minutes}:${seconds}`;
          } else {
            dateString += `, ${hours}:${minutes}`;
          }
        }
        
        return dateString;
      }

      // Add time formatting if requested (for non-Greek locales)
      if (includeTime) {
        formatOptions.hour = '2-digit';
        formatOptions.minute = '2-digit';
        // Use 24-hour format for most locales (can be customized per locale if needed)
        formatOptions.hour12 = false;
        
        if (includeSeconds) {
          formatOptions.second = '2-digit';
        }
      }

      return new Intl.DateTimeFormat(targetLocale, formatOptions).format(parsedDate);
    } catch (error) {
      console.error('Error formatting date:', parsedDate, error);
      // Fallback to browser default
      return parsedDate.toLocaleDateString();
    }
  }

  /**
   * Format date for API requests
   * Always sends in YYYY-MM-DD format in user's local timezone
   */
  formatForApi(date: Date | null | undefined): string | null {
    if (!date) return null;
    
    try {
      // Format as YYYY-MM-DD using local timezone (not UTC)
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      
      return `${year}-${month}-${day}`;
    } catch (error) {
      console.error('Error formatting date for API:', date, error);
      return null;
    }
  }

  /**
   * Get relative time in user's locale
   * "πριν από 2 ώρες", "2 hours ago", etc.
   */
  getRelativeTime(date: Date | string | null | undefined): string {
    const parsedDate = typeof date === 'string' ? this.parseApiDate(date) : date;
    
    if (!parsedDate) return '-';

    try {
      const localeConfig = this.getLocaleConfig();
      const strings = localeConfig.relativeTimeStrings;
      
      const now = new Date();
      const diffInSeconds = Math.floor((now.getTime() - parsedDate.getTime()) / 1000);
      const isPast = diffInSeconds > 0;
      const absDiff = Math.abs(diffInSeconds);

      // Less than a minute
      if (absDiff < 60) {
        return strings.justNow;
      }

      const units = [
        { seconds: 31536000, pastFn: strings.yearsAgo, futureFn: strings.inDays },
        { seconds: 2592000, pastFn: strings.monthsAgo, futureFn: strings.inDays },
        { seconds: 604800, pastFn: strings.weeksAgo, futureFn: strings.inDays },
        { seconds: 86400, pastFn: strings.daysAgo, futureFn: strings.inDays },
        { seconds: 3600, pastFn: strings.hoursAgo, futureFn: strings.inHours },
        { seconds: 60, pastFn: strings.minutesAgo, futureFn: strings.inMinutes },
      ];

      for (const unit of units) {
        const value = Math.floor(absDiff / unit.seconds);
        if (value >= 1) {
          return isPast ? unit.pastFn(value) : unit.futureFn(value);
        }
      }

      return strings.justNow;
    } catch (error) {
      console.error('Error calculating relative time:', parsedDate, error);
      return '-';
    }
  }

  /**
   * Check if a date is today (in user's timezone)
   */
  isToday(date: Date | string | null | undefined): boolean {
    const parsedDate = typeof date === 'string' ? this.parseApiDate(date) : date;
    if (!parsedDate) return false;

    const today = new Date();
    return (
      parsedDate.getDate() === today.getDate() &&
      parsedDate.getMonth() === today.getMonth() &&
      parsedDate.getFullYear() === today.getFullYear()
    );
  }

  /**
   * Check if a date is yesterday (in user's timezone)
   */
  isYesterday(date: Date | string | null | undefined): boolean {
    const parsedDate = typeof date === 'string' ? this.parseApiDate(date) : date;
    if (!parsedDate) return false;

    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    
    return (
      parsedDate.getDate() === yesterday.getDate() &&
      parsedDate.getMonth() === yesterday.getMonth() &&
      parsedDate.getFullYear() === yesterday.getFullYear()
    );
  }

  /**
   * Get user's timezone
   */
  getUserTimezone(): string {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  }

  /**
   * Get server timezone info for display
   */
  getServerTimezone(): string {
    return this.serverTimezone;
  }

  /**
   * Convert date range for API filters
   * Ensures both dates are in YYYY-MM-DD format using local timezone
   */
  formatDateRangeForApi(startDate: Date | null, endDate: Date | null): {
    start_date?: string;
    end_date?: string;
  } {
    const result: { start_date?: string; end_date?: string } = {};
    
    if (startDate) {
      const formattedStart = this.formatForApi(startDate);
      if (formattedStart) {
        result.start_date = formattedStart;
      }
    }
    
    if (endDate) {
      const formattedEnd = this.formatForApi(endDate);
      if (formattedEnd) {
        result.end_date = formattedEnd;
      }
    }
    
    return result;
  }

  /**
   * Smart date display - shows time if today, date if not
   * Automatically localized based on user's locale
   */
  smartFormat(date: Date | string | null | undefined): string {
    const parsedDate = typeof date === 'string' ? this.parseApiDate(date) : date;
    if (!parsedDate) return '-';

    const localeConfig = this.getLocaleConfig();
    const isGreek = localeConfig.locale.startsWith('el');

    if (this.isToday(parsedDate)) {
      return this.formatForDisplay(parsedDate, { includeTime: true });
    } else if (this.isYesterday(parsedDate)) {
      const yesterdayLabel = isGreek ? 'Χθες' : 'Yesterday';
      return `${yesterdayLabel} ${this.formatForDisplay(parsedDate, { includeTime: true })}`;
    } else {
      return this.formatForDisplay(parsedDate, { format: 'medium' });
    }
  }

  /**
   * Add support for more locales
   * Easy to extend for new countries/languages
   */
  addLocaleSupport(locale: string, config: LocaleConfig): void {
    this.localeConfigs[locale] = config;
  }

  /**
   * Get available locales
   */
  getAvailableLocales(): string[] {
    return Object.keys(this.localeConfigs);
  }

  /**
   * Get current user locale
   */
  getCurrentLocale(): string {
    return this.getUserLocale();
  }

  /**
   * Force a specific locale (useful for testing or user preferences)
   */
  setLocale(locale: string): void {
    if (this.localeConfigs[locale]) {
      // In a real implementation, this would store the preference
      // For now, we just validate it exists
      console.log(`Locale ${locale} is available`);
    } else {
      console.warn(`Locale ${locale} is not configured`);
    }
  }
}