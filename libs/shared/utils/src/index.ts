// Date utilities
export function formatDate(date: string | Date, locale: string = 'el-GR'): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return dateObj.toLocaleDateString(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  } else {
    return `${secs}s`;
  }
}

// File utilities
export function formatFileSize(bytes: number): string {
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  if (bytes === 0) return '0 B';
  
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  const size = bytes / Math.pow(1024, i);
  
  return `${size.toFixed(1)} ${sizes[i]}`;
}

export function getFileExtension(filename: string): string {
  return filename.split('.').pop()?.toLowerCase() || '';
}

export function isAudioFile(filename: string): boolean {
  const audioExtensions = ['wav', 'mp3', 'm4a', 'flac', 'ogg', 'wma', 'aac', 'opus', 'webm'];
  return audioExtensions.includes(getFileExtension(filename));
}

// Validation utilities
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

export function isValidGreekPhone(phone: string): boolean {
  // Greek phone number validation (mobile and landline)
  const phoneRegex = /^(\+30|0030)?[2-9]\d{8,9}$/;
  return phoneRegex.test(phone.replace(/\s+/g, ''));
}

export function validatePassword(password: string): {
  isValid: boolean;
  errors: string[];
} {
  const errors: string[] = [];
  
  if (password.length < 8) {
    errors.push('Ο κωδικός πρέπει να έχει τουλάχιστον 8 χαρακτήρες');
  }
  
  if (!/[A-Z]/.test(password)) {
    errors.push('Ο κωδικός πρέπει να περιέχει τουλάχιστον ένα κεφαλαίο γράμμα');
  }
  
  if (!/[a-z]/.test(password)) {
    errors.push('Ο κωδικός πρέπει να περιέχει τουλάχιστον ένα μικρό γράμμα');
  }
  
  if (!/\d/.test(password)) {
    errors.push('Ο κωδικός πρέπει να περιέχει τουλάχιστον έναν αριθμό');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
}

// String utilities
export function truncateText(text: string, maxLength: number, suffix: string = '...'): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - suffix.length) + suffix;
}

export function capitalizeFirst(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
}

export function camelToKebab(str: string): string {
  return str.replace(/([a-z0-9]|(?=[A-Z]))([A-Z])/g, '$1-$2').toLowerCase();
}

export function kebabToCamel(str: string): string {
  return str.replace(/-([a-z])/g, (g) => g[1].toUpperCase());
}

// Array utilities
export function groupBy<T>(array: T[], key: keyof T): Record<string, T[]> {
  return array.reduce((groups, item) => {
    const groupKey = String(item[key]);
    (groups[groupKey] = groups[groupKey] || []).push(item);
    return groups;
  }, {} as Record<string, T[]>);
}

export function uniqueBy<T>(array: T[], key: keyof T): T[] {
  const seen = new Set();
  return array.filter(item => {
    const value = item[key];
    if (seen.has(value)) {
      return false;
    }
    seen.add(value);
    return true;
  });
}

export function sortBy<T>(array: T[], key: keyof T, direction: 'asc' | 'desc' = 'asc'): T[] {
  return [...array].sort((a, b) => {
    const aVal = a[key];
    const bVal = b[key];
    
    if (aVal < bVal) return direction === 'asc' ? -1 : 1;
    if (aVal > bVal) return direction === 'asc' ? 1 : -1;
    return 0;
  });
}

// URL utilities
export function buildUrl(base: string, params: Record<string, any>): string {
  const url = new URL(base);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined) {
      url.searchParams.append(key, String(value));
    }
  });
  return url.toString();
}

export function parseQueryParams(search: string): Record<string, string> {
  const params = new URLSearchParams(search);
  const result: Record<string, string> = {};
  
  for (const [key, value] of params.entries()) {
    result[key] = value;
  }
  
  return result;
}

// Local storage utilities with type safety
export function setStorageItem<T>(key: string, value: T): void {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.warn('Failed to save to localStorage:', error);
  }
}

export function getStorageItem<T>(key: string): T | null {
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : null;
  } catch (error) {
    console.warn('Failed to read from localStorage:', error);
    return null;
  }
}

export function removeStorageItem(key: string): void {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.warn('Failed to remove from localStorage:', error);
  }
}

// Debounce utility
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  
  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Retry utility
export async function retry<T>(
  fn: () => Promise<T>,
  attempts: number = 3,
  delay: number = 1000
): Promise<T> {
  try {
    return await fn();
  } catch (error) {
    if (attempts <= 1) {
      throw error;
    }
    
    await new Promise(resolve => setTimeout(resolve, delay));
    return retry(fn, attempts - 1, delay * 2); // Exponential backoff
  }
}

// Greek text utilities
export function normalizeGreekText(text: string): string {
  // Normalize Greek diacritics and special characters
  return text
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // Remove diacritics
    .replace(/ς/g, 'σ') // Replace final sigma with regular sigma
    .toLowerCase();
}

export function isGreekText(text: string): boolean {
  const greekRegex = /[\u0370-\u03FF\u1F00-\u1FFF]/;
  return greekRegex.test(text);
}

// Error handling utilities
export function extractErrorMessage(error: any): string {
  if (typeof error === 'string') return error;
  if (error?.message) return error.message;
  if (error?.error?.message) return error.error.message;
  if (error?.data?.message) return error.data.message;
  return 'Παρουσιάστηκε ένα σφάλμα';
}

export function isNetworkError(error: any): boolean {
  return (
    error?.name === 'NetworkError' ||
    error?.message?.includes('fetch') ||
    error?.message?.includes('network') ||
    error?.code === 'NETWORK_ERROR'
  );
}