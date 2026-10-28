import { apiClient, handleApiError, retryRequest } from './client';
import type {
  ApiResponse,
  PaginatedResponse,
  Agent,
  CreateAgentRequest,
  UpdateAgentRequest,
  AgentQueryParams,
} from './types';

/**
 * Agents API Service
 */
export const agentsApi = {
  /**
   * Get All Agents with Pagination and Filters
   */
  getAgents: async (params?: AgentQueryParams): Promise<PaginatedResponse<Agent>> => {
    try {
      const response = await retryRequest(() =>
        apiClient.get<ApiResponse<PaginatedResponse<Agent>>>('/api/agents', { params })
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.error || 'Failed to fetch agents');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Get Agent by ID
   */
  getAgentById: async (agentId: string): Promise<Agent> => {
    try {
      const response = await retryRequest(() =>
        apiClient.get<ApiResponse<Agent>>(`/api/agents/${agentId}`)
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.error || 'Failed to fetch agent');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Create New Agent
   */
  createAgent: async (agentData: CreateAgentRequest): Promise<Agent> => {
    try {
      const response = await retryRequest(() =>
        apiClient.post<ApiResponse<Agent>>('/api/agents', agentData)
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.error || 'Failed to create agent');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Update Agent
   */
  updateAgent: async (agentId: string, updates: UpdateAgentRequest): Promise<Agent> => {
    try {
      const response = await retryRequest(() =>
        apiClient.put<ApiResponse<Agent>>(`/api/agents/${agentId}`, updates)
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.error || 'Failed to update agent');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Delete Agent
   */
  deleteAgent: async (agentId: string): Promise<void> => {
    try {
      const response = await retryRequest(() =>
        apiClient.delete<ApiResponse>(`/api/agents/${agentId}`)
      );

      if (!response.data.success) {
        throw new Error(response.data.error || 'Failed to delete agent');
      }
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Get My Agents (Agents owned by current user)
   */
  getMyAgents: async (params?: Omit<AgentQueryParams, 'owner'>): Promise<PaginatedResponse<Agent>> => {
    try {
      const response = await retryRequest(() =>
        apiClient.get<ApiResponse<PaginatedResponse<Agent>>>('/api/agents/my', { params })
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.error || 'Failed to fetch my agents');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Start Agent
   */
  startAgent: async (agentId: string): Promise<Agent> => {
    try {
      const response = await retryRequest(() =>
        apiClient.post<ApiResponse<Agent>>(`/api/agents/${agentId}/start`)
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.error || 'Failed to start agent');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Stop Agent
   */
  stopAgent: async (agentId: string): Promise<Agent> => {
    try {
      const response = await retryRequest(() =>
        apiClient.post<ApiResponse<Agent>>(`/api/agents/${agentId}/stop`)
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.error || 'Failed to stop agent');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Get Agent Performance Metrics
   */
  getAgentMetrics: async (agentId: string): Promise<Agent['performance']> => {
    try {
      const response = await retryRequest(() =>
        apiClient.get<ApiResponse<Agent['performance']>>(`/api/agents/${agentId}/metrics`)
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.error || 'Failed to fetch agent metrics');
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Assign Task to Agent
   */
  assignTask: async (agentId: string, taskId: string): Promise<void> => {
    try {
      const response = await retryRequest(() =>
        apiClient.post<ApiResponse>(`/api/agents/${agentId}/assign`, { taskId })
      );

      if (!response.data.success) {
        throw new Error(response.data.error || 'Failed to assign task to agent');
      }
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Get Agent Tasks
   */
  getAgentTasks: async (agentId: string): Promise<any[]> => {
    try {
      const response = await retryRequest(() =>
        apiClient.get<ApiResponse<any[]>>(`/api/agents/${agentId}/tasks`)
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(response.data.error || 'Failed to fetch agent tasks');
    } catch (error) {
      return handleApiError(error);
    }
  },
};
