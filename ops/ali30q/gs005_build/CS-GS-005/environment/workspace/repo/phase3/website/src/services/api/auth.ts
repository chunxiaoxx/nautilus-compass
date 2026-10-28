import { apiClient, TokenManager, handleApiError, retryRequest } from './client';
import type {
  ApiResponse,
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  User,
} from './types';

/**
 * Authentication API Service
 */
export const authApi = {
  /**
   * User Login
   */
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    try {
      const response = await retryRequest(() =>
        apiClient.post<ApiResponse<AuthResponse>>('/api/auth/login', credentials)
      );

      if (response.data.success && response.data.data) {
        const { token, refreshToken } = response.data.data;
        TokenManager.setToken(token);
        TokenManager.setRefreshToken(refreshToken);
        return response.data.data;
      }

      throw new Error(response.data.error || 'Login failed');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * User Registration
   */
  register: async (userData: RegisterRequest): Promise<AuthResponse> => {
    try {
      const response = await retryRequest(() =>
        apiClient.post<ApiResponse<AuthResponse>>('/api/auth/register', userData)
      );

      if (response.data.success && response.data.data) {
        const { token, refreshToken } = response.data.data;
        TokenManager.setToken(token);
        TokenManager.setRefreshToken(refreshToken);
        return response.data.data;
      }

      throw new Error(response.data.error || 'Registration failed');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * User Logout
   */
  logout: async (): Promise<void> => {
    try {
      await apiClient.post<ApiResponse>('/api/auth/logout');
    } catch (error) {
      // Continue with local logout even if API call fails
      console.error('Logout API error:', error);
    } finally {
      TokenManager.clearTokens();
    }
  },

  /**
   * Refresh Access Token
   */
  refreshToken: async (): Promise<{ token: string; refreshToken: string }> => {
    try {
      const refreshToken = TokenManager.getRefreshToken();
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await apiClient.post<ApiResponse<{ token: string; refreshToken: string }>>(
        '/api/auth/refresh',
        { refreshToken }
      );

      if (response.data.success && response.data.data) {
        TokenManager.setToken(response.data.data.token);
        TokenManager.setRefreshToken(response.data.data.refreshToken);
        return response.data.data;
      }

      throw new Error(response.data.error || 'Token refresh failed');
    } catch (error) {
      TokenManager.clearTokens();
      return handleApiError(error);
    }
  },

  /**
   * Get Current User Profile
   */
  getProfile: async (): Promise<User> => {
    try {
      const response = await retryRequest(() =>
        apiClient.get<ApiResponse<User>>('/api/auth/profile')
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.error || 'Failed to fetch profile');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Verify Token Validity
   */
  verifyToken: async (): Promise<boolean> => {
    try {
      const response = await apiClient.get<ApiResponse<{ valid: boolean }>>(
        '/api/auth/verify'
      );

      return response.data.success && response.data.data?.valid === true;
    } catch (error) {
      return false;
    }
  },

  /**
   * Request Password Reset
   */
  requestPasswordReset: async (email: string): Promise<void> => {
    try {
      const response = await retryRequest(() =>
        apiClient.post<ApiResponse>('/api/auth/password-reset/request', { email })
      );

      if (!response.data.success) {
        throw new Error(response.data.error || 'Password reset request failed');
      }
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Reset Password with Token
   */
  resetPassword: async (token: string, newPassword: string): Promise<void> => {
    try {
      const response = await retryRequest(() =>
        apiClient.post<ApiResponse>('/api/auth/password-reset/confirm', {
          token,
          password: newPassword,
        })
      );

      if (!response.data.success) {
        throw new Error(response.data.error || 'Password reset failed');
      }
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated: (): boolean => {
    return !!TokenManager.getToken();
  },
};
