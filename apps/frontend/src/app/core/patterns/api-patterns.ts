/**
 * Standardized API patterns for consistent request/response handling
 * Use these patterns to avoid code repetition across components
 */

import { inject } from '@angular/core';
import { signal } from '@angular/core';
import { ApiService, ApiOptions, apiCall } from '../services/api.service';

/**
 * Standard loading state management
 */
export function createLoadingState() {
  const isLoading = signal(false);
  const error = signal<string | null>(null);

  const setLoading = (loading: boolean) => {
    isLoading.set(loading);
    if (loading) {
      error.set(null);
    }
  };

  const setError = (errorMessage: string) => {
    error.set(errorMessage);
    isLoading.set(false);
  };

  const clearError = () => error.set(null);

  return {
    isLoading: isLoading.asReadonly(),
    error: error.asReadonly(),
    setLoading,
    setError,
    clearError
  };
}

/**
 * Standard CRUD operations with automatic message handling
 */
export class ApiPatterns {
  private readonly api = inject(ApiService);

  /**
   * CREATE operation with automatic message handling from backend
   */
  async create<T>(
    endpoint: string, 
    data: any, 
    options: ApiOptions = {}
  ): Promise<T> {
    return apiCall<T>(this.api, 'post', endpoint, data, options);
  }

  /**
   * READ operation (silent success by default)
   */
  async read<T>(endpoint: string, options: ApiOptions = {}): Promise<T> {
    return apiCall<T>(this.api, 'get', endpoint, null, {
      showSuccessMessage: false,
      ...options
    });
  }

  /**
   * UPDATE operation with automatic message handling from backend
   */
  async update<T>(
    endpoint: string, 
    data: any, 
    options: ApiOptions = {}
  ): Promise<T> {
    return apiCall<T>(this.api, 'put', endpoint, data, options);
  }

  /**
   * PARTIAL UPDATE operation with automatic message handling from backend
   */
  async patch<T>(
    endpoint: string, 
    data: any, 
    options: ApiOptions = {}
  ): Promise<T> {
    return apiCall<T>(this.api, 'patch', endpoint, data, options);
  }

  /**
   * DELETE operation with automatic message handling from backend
   */
  async delete<T>(
    endpoint: string, 
    options: ApiOptions = {}
  ): Promise<T> {
    return apiCall<T>(this.api, 'delete', endpoint, null, options);
  }

  /**
   * Silent operation (no automatic messages)
   */
  async silent<T>(
    method: 'get' | 'post' | 'put' | 'patch' | 'delete',
    endpoint: string,
    data?: any
  ): Promise<T> {
    return apiCall<T>(this.api, method, endpoint, data, {
      silentRequest: true
    });
  }
}

/**
 * Standard form submission pattern
 */
export async function submitForm<T>(
  formData: any,
  endpoint: string,
  loadingState: ReturnType<typeof createLoadingState>,
  apiPatterns: ApiPatterns,
  isUpdate: boolean = false
): Promise<T | null> {
  if (!formData || Object.keys(formData).length === 0) {
    return null;
  }

  loadingState.setLoading(true);

  const result = isUpdate 
    ? await apiPatterns.update<T>(endpoint, formData)
    : await apiPatterns.create<T>(endpoint, formData);

  loadingState.setLoading(false);
  return result;
}

/**
 * Standard data loading pattern
 */
export async function loadData<T>(
  endpoint: string,
  loadingState: ReturnType<typeof createLoadingState>,
  apiPatterns: ApiPatterns
): Promise<T | null> {
  loadingState.setLoading(true);

  try {
    const result = await apiPatterns.read<T>(endpoint);
    loadingState.setLoading(false);
    return result;
  } catch (error: any) {
    loadingState.setLoading(false);
    // Error is automatically handled by the API service
    return null;
  }
}

/**
 * Standard delete confirmation pattern
 */
export async function deleteWithConfirmation<T>(
  itemName: string,
  endpoint: string,
  apiPatterns: ApiPatterns,
  confirmationService: any // You can inject your confirmation service
): Promise<boolean> {
  const confirmed = await confirmationService.confirm({
    message: `Είστε σίγουρος ότι θέλετε να διαγράψετε το "${itemName}";`,
    header: 'Επιβεβαίωση Διαγραφής',
    acceptLabel: 'Ναι, Διαγραφή',
    rejectLabel: 'Ακύρωση',
    acceptButtonStyleClass: 'p-button-danger'
  });

  if (confirmed) {
    await apiPatterns.delete(endpoint);
    return true;
  }

  return false;
}

/**
 * Standard pagination pattern
 */
export function createPaginationState() {
  const currentPage = signal(1);
  const pageSize = signal(10);
  const totalItems = signal(0);
  const totalPages = signal(0);

  const setPage = (page: number) => currentPage.set(page);
  const setPageSize = (size: number) => pageSize.set(size);
  const setPagination = (total: number, pages: number) => {
    totalItems.set(total);
    totalPages.set(pages);
  };

  return {
    currentPage: currentPage.asReadonly(),
    pageSize: pageSize.asReadonly(),
    totalItems: totalItems.asReadonly(),
    totalPages: totalPages.asReadonly(),
    setPage,
    setPageSize,
    setPagination
  };
}

/**
 * Standard paginated data loading
 */
export async function loadPaginatedData<T>(
  baseEndpoint: string,
  paginationState: ReturnType<typeof createPaginationState>,
  loadingState: ReturnType<typeof createLoadingState>,
  apiPatterns: ApiPatterns,
  filters?: Record<string, any>
): Promise<T[] | null> {
  loadingState.setLoading(true);

  try {
    const params = apiPatterns['api'].buildPaginationParams(
      paginationState.currentPage(),
      paginationState.pageSize(),
      filters
    );

    const response = await apiPatterns.read<{
      data: T[];
      pagination: {
        total: number;
        pages: number;
        current_page: number;
        per_page: number;
      };
    }>(baseEndpoint, { params });

    if (response.pagination) {
      paginationState.setPagination(
        response.pagination.total,
        response.pagination.pages
      );
    }

    loadingState.setLoading(false);
    return response.data || [];
  } catch (error) {
    loadingState.setLoading(false);
    return null;
  }
}