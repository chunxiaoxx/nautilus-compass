import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios';
import type { ApiResponse } from './types';
import { tokenUtils } from '../../utils/token';

// API Configuration
// Same-origin base (nginx proxies /api/* → backend). Avoids mixed-content on
// HTTPS production and the old hard-coded http://IP:8000 (which 404'd /auth/* and
// was blocked by the browser). All apiClient call paths include the /api prefix.
const API_BASE_URL = import.meta.env.VITE_API_URL || '';
const API_TIMEOUT = 30000;
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

// Token Management
class TokenManager {
  private static readonly TOKEN_KEY = 'nautilus_token';
  private static readonly REFRESH_TOKEN_KEY = 'nautilus_refresh_token';

  static getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  static setToken(token: string): void {
    localStorage.setItem(this.TOKEN_KEY, token);
  }

  static getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  static setRefreshToken(token: string): void {
    localStorage.setItem(this.REFRESH_TOKEN_KEY, token);
  }

  static clearTokens(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
  }
}

// Create Axios Instance
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: API_TIMEOUT,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request Interceptor
  client.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      // Read from tokenUtils first (where OAuth callback / wallet / AuthContext save
      // the session token under `nautilus_auth_token`), fall back to TokenManager.
      const token = tokenUtils.get() || TokenManager.getToken();
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error: AxiosError) => {
      return Promise.reject(error);
    }
  );

  // Response Interceptor
  client.interceptors.response.use(
    (response: AxiosResponse) => {
      return response;
    },
    async (error: AxiosError) => {
      const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

      // Handle 401 Unauthorized - Token Refresh
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        try {
          const refreshToken = TokenManager.getRefreshToken();
          if (!refreshToken) {
            throw new Error('No refresh token available');
          }

          const response = await axios.post<ApiResponse<{ token: string; refreshToken: string }>>(
            `${API_BASE_URL}/api/auth/refresh`,
            { refreshToken }
          );

          if (response.data.success && response.data.data) {
            TokenManager.setToken(response.data.data.token);
            TokenManager.setRefreshToken(response.data.data.refreshToken);

            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${response.data.data.token}`;
            }

            return client(originalRequest);
          }
        } catch (refreshError) {
          TokenManager.clearTokens();
          tokenUtils.remove();
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }

      return Promise.reject(error);
    }
  );

  return client;
};

// Retry Logic
const retryRequest = async <T>(
  requestFn: () => Promise<T>,
  retries: number = MAX_RETRIES,
  delay: number = RETRY_DELAY
): Promise<T> => {
  try {
    return await requestFn();
  } catch (error) {
    if (retries === 0) {
      throw error;
    }

    const axiosError = error as AxiosError;
    const shouldRetry =
      !axiosError.response ||
      axiosError.response.status >= 500 ||
      axiosError.code === 'ECONNABORTED' ||
      axiosError.code === 'ERR_NETWORK';

    if (!shouldRetry) {
      throw error;
    }

    await new Promise((resolve) => setTimeout(resolve, delay));
    return retryRequest(requestFn, retries - 1, delay * 2);
  }
};

// Error Handler
export class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
    public data?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export const handleApiError = (error: unknown): never => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiResponse>;
    const status = axiosError.response?.status || 500;
    const message = axiosError.response?.data?.error || axiosError.message || 'Unknown error occurred';
    const data = axiosError.response?.data;

    throw new ApiError(status, message, data);
  }

  throw new ApiError(500, 'An unexpected error occurred');
};

// API Client Instance
export const apiClient = createApiClient();

// Export Token Manager
export { TokenManager };

// Export Retry Function
export { retryRequest };
