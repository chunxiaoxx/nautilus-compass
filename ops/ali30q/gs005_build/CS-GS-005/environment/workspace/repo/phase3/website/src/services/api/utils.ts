/**
 * API Utilities
 *
 * Helper functions for API integration
 */

import type { AxiosError } from 'axios';
import { ERROR_MESSAGES } from './config';
import type { ApiResponse } from './types';

/**
 * Build Query String from Parameters
 */
export const buildQueryString = (params: Record<string, any>): string => {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      if (Array.isArray(value)) {
        value.forEach((item) => searchParams.append(key, String(item)));
      } else {
        searchParams.append(key, String(value));
      }
    }
  });

  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : '';
};

/**
 * Get Error Message from API Error
 */
export const getErrorMessage = (error: unknown): string => {
  if (!error) return ERROR_MESSAGES.unknown;

  // Axios error
  if (isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiResponse>;

    // Network error
    if (!axiosError.response) {
      return ERROR_MESSAGES.network;
    }

    // Timeout error
    if (axiosError.code === 'ECONNABORTED') {
      return ERROR_MESSAGES.timeout;
    }

    // HTTP status errors
    const status = axiosError.response.status;
    switch (status) {
      case 401:
        return ERROR_MESSAGES.unauthorized;
      case 403:
        return ERROR_MESSAGES.forbidden;
      case 404:
        return ERROR_MESSAGES.notFound;
      case 500:
      case 502:
      case 503:
      case 504:
        return ERROR_MESSAGES.serverError;
      default:
        return axiosError.response.data?.error || ERROR_MESSAGES.unknown;
    }
  }

  // Standard Error
  if (error instanceof Error) {
    return error.message;
  }

  // String error
  if (typeof error === 'string') {
    return error;
  }

  return ERROR_MESSAGES.unknown;
};

/**
 * Check if error is Axios error
 */
export const isAxiosError = (error: unknown): error is AxiosError => {
  return (error as AxiosError).isAxiosError === true;
};

/**
 * Check if error is network error
 */
export const isNetworkError = (error: unknown): boolean => {
  if (!isAxiosError(error)) return false;
  return !error.response || error.code === 'ERR_NETWORK';
};

/**
 * Check if error is timeout error
 */
export const isTimeoutError = (error: unknown): boolean => {
  if (!isAxiosError(error)) return false;
  return error.code === 'ECONNABORTED';
};

/**
 * Check if error is retryable
 */
export const isRetryableError = (error: unknown): boolean => {
  if (!isAxiosError(error)) return false;

  // Network and timeout errors are retryable
  if (isNetworkError(error) || isTimeoutError(error)) {
    return true;
  }

  // 5xx errors are retryable
  const status = error.response?.status;
  return status ? status >= 500 : false;
};

/**
 * Format Date for API
 */
export const formatDateForApi = (date: Date): string => {
  return date.toISOString();
};

/**
 * Parse Date from API
 */
export const parseDateFromApi = (dateString: string): Date => {
  return new Date(dateString);
};

/**
 * Validate Email
 */
export const validateEmail = (email: string): boolean => {
  const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return pattern.test(email);
};

/**
 * Validate Password
 */
export const validatePassword = (password: string): boolean => {
  return password.length >= 8 && /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(password);
};

/**
 * Validate Username
 */
export const validateUsername = (username: string): boolean => {
  return username.length >= 3 && username.length <= 20 && /^[a-zA-Z0-9_]+$/.test(username);
};

/**
 * Format File Size
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};

/**
 * Validate File Type
 */
export const validateFileType = (file: File, allowedTypes: string[]): boolean => {
  return allowedTypes.includes(file.type);
};

/**
 * Validate File Size
 */
export const validateFileSize = (file: File, maxSize: number): boolean => {
  return file.size <= maxSize;
};

/**
 * Debounce Function
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout | null = null;

  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

/**
 * Throttle Function
 */
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean = false;

  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

/**
 * Deep Clone Object
 */
export const deepClone = <T>(obj: T): T => {
  return JSON.parse(JSON.stringify(obj));
};

/**
 * Merge Objects
 */
export const mergeObjects = <T extends Record<string, any>>(
  target: T,
  ...sources: Partial<T>[]
): T => {
  return Object.assign({}, target, ...sources);
};

/**
 * Pick Properties from Object
 */
export const pick = <T extends Record<string, any>, K extends keyof T>(
  obj: T,
  keys: K[]
): Pick<T, K> => {
  const result = {} as Pick<T, K>;
  keys.forEach((key) => {
    if (key in obj) {
      result[key] = obj[key];
    }
  });
  return result;
};

/**
 * Omit Properties from Object
 */
export const omit = <T extends Record<string, any>, K extends keyof T>(
  obj: T,
  keys: K[]
): Omit<T, K> => {
  const result = { ...obj };
  keys.forEach((key) => {
    delete result[key];
  });
  return result;
};

/**
 * Generate Random ID
 */
export const generateId = (): string => {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
};

/**
 * Sleep Function
 */
export const sleep = (ms: number): Promise<void> => {
  return new Promise((resolve) => setTimeout(resolve, ms));
};

/**
 * Retry with Exponential Backoff
 */
export const retryWithBackoff = async <T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> => {
  let lastError: Error;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;

      if (i < maxRetries - 1) {
        const delay = baseDelay * Math.pow(2, i);
        await sleep(delay);
      }
    }
  }

  throw lastError!;
};

/**
 * Format Currency
 */
export const formatCurrency = (amount: number, currency: string = 'USD'): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(amount);
};

/**
 * Format Percentage
 */
export const formatPercentage = (value: number, decimals: number = 2): string => {
  return `${(value * 100).toFixed(decimals)}%`;
};

/**
 * Truncate String
 */
export const truncate = (str: string, maxLength: number, suffix: string = '...'): string => {
  if (str.length <= maxLength) return str;
  return str.substring(0, maxLength - suffix.length) + suffix;
};

/**
 * Capitalize First Letter
 */
export const capitalize = (str: string): string => {
  return str.charAt(0).toUpperCase() + str.slice(1);
};

/**
 * Convert to Title Case
 */
export const toTitleCase = (str: string): string => {
  return str
    .toLowerCase()
    .split(' ')
    .map((word) => capitalize(word))
    .join(' ');
};
