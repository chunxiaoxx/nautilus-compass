import { apiClient, handleApiError, retryRequest } from './client';
import type {
  ApiResponse,
  User,
  UserStats,
  UserHistory,
} from './types';

/**
 * Users API Service
 */
export const usersApi = {
  /**
   * Get Current User Profile
   */
  getProfile: async (): Promise<User> => {
    try {
      const response = await retryRequest(() =>
        apiClient.get<ApiResponse<User>>('/api/users/profile')
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
   * Update User Profile
   */
  updateProfile: async (updates: Partial<Omit<User, 'id' | 'createdAt'>>): Promise<User> => {
    try {
      const response = await retryRequest(() =>
        apiClient.put<ApiResponse<User>>('/api/users/profile', updates)
   );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.error || 'Failed to update profile');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Get User Statistics
   */
  getStats: async (): Promise<UserStats> => {
    try {
      const response = await retryRequest(() =>
        apiClient.get<ApiResponse<UserStats>>('/api/users/stats')
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
    }

      throw new Error(response.data.error || 'Failed to fetch stats');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Get User History
   */
  getHistory: async (params?: { startDate?: string; endDate?: string }): Promise<UserHistory> => {
    try {
      const response = await retryRequest(() =>
      apiClient.get<ApiResponse<UserHistory>>('/api/users/history', { params })
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

   throw new Error(response.data.error || 'Failed to fetch history');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Upload User Avatar
   */
  uploadAvatar: async (file: File): Promise<string> => {
    try {
      const formData = new FormData();
      formData.append('avatar', file);

      const response = await retryRequest(() =>
        apiClient.post<ApiResponse<{ url: string }>>('/api/users/avatar', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })
      );

      if (response.data.success && response.data.data) {
        return response.data.data.url;
      }

      throw new Error(response.data.error || 'Failed to upload avatar');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Delete User Avatar
   */
  deleteAvatar: async (): Promise<void> => {
    try {
      const response = await retryRequest(() =>
        apiClient.delete<ApiResponse>('/api/users/avatar')
      );

      if (!response.data.success) {
        throw new Error(response.data.error || 'Failed to delete avatar');
      }
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Get User by ID (Public Profile)
   */
  getUserById: async (userId: string): Promise<Omit<User, 'email'>> => {
    try {
      const response = await retryRequest(() =>
        apiClient.get<ApiResponse<Omit<User, 'email'>>>(`/api/users/${userId}`)
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.error || 'Failed to fetch user');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Get User Stats by ID (Public)
   */
  getUserStats: async (userId: string): Promise<UserStats> => {
    try {
      const response = await retryRequest(() =>
        apiClient.get<ApiResponse<UserStats>>(`/api/users/${userId}/stats`)
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.error || 'Failed to fetch user stats');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Change Password
   */
  changePassword: async (currentPassword: string, newPassword: string): Promise<void> => {
    try {
      const response = await retryRequest(() =>
        apiClient.post<ApiResponse>('/api/users/change-password', {
          currentPassword,
          newPassword,
    })
      );

      if (!response.data.success) {
        throw new Error(response.data.error || 'Failed to change password');
      }
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Delete User Account
   */
  deleteAccount: async (password: string): Promise<void> => {
  try {
      const response = await retryRequest(() =>
        apiClient.post<ApiResponse>('/api/users/delete-account', { password })
      );

      if (!response.data.success) {
    throw new Error(response.data.error || 'Failed to delete account');
      }
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Get Leaderboard
   */
  getLeaderboard: async (params?: { limit?: number; offset?: number }): Promise<Array<{
    userId: string;
  username: string;
    avatar?: string;
    rank: number;
    stats: UserStats;
  }>> => {
    try {
      const response = await retryRequest(() =>
        apiClient.get<ApiResponse<Array<any>>>('/api/users/leaderboard', { params })
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.error || 'Failed to fetch leaderboard');
    } catch (error) {
      return handleApiError(error);
    }
  },
};
