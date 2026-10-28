import { apiClient, handleApiError, retryRequest } from './client';
import type {
  ApiResponse,
  PaginatedResponse,
  Task,
  CreateTaskRequest,
  UpdateTaskRequest,
  TaskResult,
  TaskQueryParams,
} from './types';

/**
 * Tasks API Service
 */
export const tasksApi = {
  /**
   * Get All Tasks with Pagination and Filters
   */
  getTasks: async (params?: TaskQueryParams): Promise<PaginatedResponse<Task>> => {
    try {
      const response = await retryRequest(() =>
        apiClient.get<ApiResponse<PaginatedResponse<Task>>>('/api/tasks', { params })
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.error || 'Failed to fetch tasks');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Get Task by ID
   */
  getTaskById: async (taskId: string): Promise<Task> => {
    try {
      const response = await retryRequest(() =>
        apiClient.get<ApiResponse<Task>>(`/api/tasks/${taskId}`)
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.error || 'Failed to fetch task');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Create New Task
   */
  createTask: async (taskData: CreateTaskRequest): Promise<Task> => {
    try {
      const response = await retryRequest(() =>
        apiClient.post<ApiResponse<Task>>('/api/tasks', taskData)
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.error || 'Failed to create task');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Update Task
   */
  updateTask: async (taskId: string, updates: UpdateTaskRequest): Promise<Task> => {
    try {
      const response = await retryRequest(() =>
        apiClient.put<ApiResponse<Task>>(`/api/tasks/${taskId}`, updates)
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.error || 'Failed to update task');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Delete Task
   */
  deleteTask: async (taskId: string): Promise<void> => {
    try {
      const response = await retryRequest(() =>
        apiClient.delete<ApiResponse>(`/api/tasks/${taskId}`)
      );

      if (!response.data.success) {
        throw new Error(response.data.error || 'Failed to delete task');
      }
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Accept Task (Assign to Current User)
   */
  acceptTask: async (taskId: string): Promise<Task> => {
    try {
      const response = await retryRequest(() =>
        apiClient.post<ApiResponse<Task>>(`/api/tasks/${taskId}/accept`)
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.error || 'Failed to accept task');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Submit Task Result
   */
  submitResult: async (taskId: string, result: Record<string, any>): Promise<TaskResult> => {
    try {
      const response = await retryRequest(() =>
        apiClient.post<ApiResponse<TaskResult>>(`/api/tasks/${taskId}/submit`, { result })
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.error || 'Failed to submit result');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Get My Tasks (Tasks assigned to current user)
   */
  getMyTasks: async (params?: Omit<TaskQueryParams, 'assignedTo'>): Promise<PaginatedResponse<Task>> => {
    try {
      const response = await retryRequest(() =>
        apiClient.get<ApiResponse<PaginatedResponse<Task>>>('/api/tasks/my', { params })
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.error || 'Failed to fetch my tasks');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Get Available Tasks (Not assigned)
   */
  getAvailableTasks: async (params?: TaskQueryParams): Promise<PaginatedResponse<Task>> => {
    try {
      const response = await retryRequest(() =>
        apiClient.get<ApiResponse<PaginatedResponse<Task>>>('/api/tasks/available', { params })
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.error || 'Failed to fetch available tasks');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Cancel Task (Unassign from current user)
   */
  cancelTask: async (taskId: string): Promise<Task> => {
    try {
      const response = await retryRequest(() =>
        apiClient.post<ApiResponse<Task>>(`/api/tasks/${taskId}/cancel`)
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.error || 'Failed to cancel task');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Get Task Results
   */
  getTaskResults: async (taskId: string): Promise<TaskResult[]> => {
    try {
      const response = await retryRequest(() =>
        apiClient.get<ApiResponse<TaskResult[]>>(`/api/tasks/${taskId}/results`)
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.error || 'Failed to fetch task results');
    } catch (error) {
      return handleApiError(error);
    }
  },
};
