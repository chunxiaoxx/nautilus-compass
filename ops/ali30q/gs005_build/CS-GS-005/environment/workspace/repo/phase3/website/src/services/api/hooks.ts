import { QueryClient, useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authApi, tasksApi, agentsApi, usersApi } from './index';
import type {
  LoginRequest,
  RegisterRequest,
  CreateTaskRequest,
  UpdateTaskRequest,
  CreateAgentRequest,
  UpdateAgentRequest,
  TaskQueryParams,
  AgentQueryParams,
  User,
} from './types';

/**
 * React Query Configuration
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
      retry: 3,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
});

/**
 * Query Keys Factory
 */
export const queryKeys = {
  auth: {
    profile: ['auth', 'profile'] as const,
  },
  tasks: {
    all: ['tasks'] as const,
    list: (params?: TaskQueryParams) => ['tasks', 'list', params] as const,
    detail: (id: string) => ['tasks', 'detail', id] as const,
    my: (params?: TaskQueryParams) => ['tasks', 'my', params] as const,
    available: (params?: TaskQueryParams) => ['tasks', 'available', params] as const,
    results: (id: string) => ['tasks', 'results', id] as const,
  },
  agents: {
    all: ['agents'] as const,
    list: (params?: AgentQueryParams) => ['agents', 'list', params] as const,
    detail: (id: string) => ['agents', 'detail', id] as const,
    my: (params?: AgentQueryParams) => ['agents', 'my', params] as const,
    metrics: (id: string) => ['agents', 'metrics', id] as const,
    tasks: (id: string) => ['agents', 'tasks', id] as const,
  },
  users: {
    profile: ['users', 'profile'] as const,
    stats: ['users', 'stats'] as const,
    history: (params?: { startDate?: string; endDate?: string }) => ['users', 'history', params] as const,
    detail: (id: string) => ['users', 'detail', id] as const,
    userStats: (id: string) => ['users', 'stats', id] as const,
    leaderboard: (params?: { limit?: number; offset?: number }) => ['users', 'leaderboard', params] as const,
  },
};

/**
 * Auth Hooks
 */
export const useLogin = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (credentials: LoginRequest) => authApi.login(credentials),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.auth.profile });
    },
  });
};

export const useRegister = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userData: RegisterRequest) => authApi.register(userData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.auth.profile });
    },
  });
};

export const useLogout = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => authApi.logout(),
    onSuccess: () => {
      queryClient.clear();
    },
  });
};

export const useProfile = () => {
  return useQuery({
    queryKey: queryKeys.auth.profile,
    queryFn: () => authApi.getProfile(),
    enabled: authApi.isAuthenticated(),
  });
};

/**
 * Tasks Hooks
 */
export const useTasks = (params?: TaskQueryParams) => {
  return useQuery({
    queryKey: queryKeys.tasks.list(params),
    queryFn: () => tasksApi.getTasks(params),
  });
};

export const useTask = (taskId: string) => {
  return useQuery({
    queryKey: queryKeys.tasks.detail(taskId),
    queryFn: () => tasksApi.getTaskById(taskId),
    enabled: !!taskId,
  });
};

export const useMyTasks = (params?: TaskQueryParams) => {
  return useQuery({
    queryKey: queryKeys.tasks.my(params),
    queryFn: () => tasksApi.getMyTasks(params),
  });
};

export const useAvailableTasks = (params?: TaskQueryParams) => {
  return useQuery({
    queryKey: queryKeys.tasks.available(params),
    queryFn: () => tasksApi.getAvailableTasks(params),
  });
};

export const useCreateTask = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (taskData: CreateTaskRequest) => tasksApi.createTask(taskData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all });
    },
  });
};

export const useUpdateTask = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ taskId, updates }: { taskId: string; updates: UpdateTaskRequest }) =>
      tasksApi.updateTask(taskId, updates),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.detail(variables.taskId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all });
    },
  });
};

export const useDeleteTask = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (taskId: string) => tasksApi.deleteTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all });
    },
  });
};

export const useAcceptTask = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (taskId: string) => tasksApi.acceptTask(taskId),
    onSuccess: (_, taskId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.detail(taskId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.my() });
    },
  });
};

export const useSubmitTaskResult = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ taskId, result }: { taskId: string; result: Record<string, any> }) =>
      tasksApi.submitResult(taskId, result),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.detail(variables.taskId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.results(variables.taskId) });
    },
  });
};

/**
 * Agents Hooks
 */
export const useAgents = (params?: AgentQueryParams) => {
  return useQuery({
    queryKey: queryKeys.agents.list(params),
    queryFn: () => agentsApi.getAgents(params),
  });
};

export const useAgent = (agentId: string) => {
  return useQuery({
    queryKey: queryKeys.agents.detail(agentId),
    queryFn: () => agentsApi.getAgentById(agentId),
    enabled: !!agentId,
  });
};

export const useMyAgents = (params?: AgentQueryParams) => {
  return useQuery({
    queryKey: queryKeys.agents.my(params),
    queryFn: () => agentsApi.getMyAgents(params),
  });
};

export const useCreateAgent = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (agentData: CreateAgentRequest) => agentsApi.createAgent(agentData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.agents.all });
    },
  });
};

export const useUpdateAgent = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ agentId, updates }: { agentId: string; updates: UpdateAgentRequest }) =>
      agentsApi.updateAgent(agentId, updates),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.agents.detail(variables.agentId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.agents.all });
    },
  });
};

export const useDeleteAgent = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (agentId: string) => agentsApi.deleteAgent(agentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.agents.all });
    },
  });
};

export const useStartAgent = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (agentId: string) => agentsApi.startAgent(agentId),
    onSuccess: (_, agentId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.agents.detail(agentId) });
    },
  });
};

export const useStopAgent = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (agentId: string) => agentsApi.stopAgent(agentId),
    onSuccess: (_, agentId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.agents.detail(agentId) });
    },
  });
};

/**
 * Users Hooks
 */
export const useUserProfile = () => {
  return useQuery({
    queryKey: queryKeys.users.profile,
    queryFn: () => usersApi.getProfile(),
  });
};

export const useUpdateProfile = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (updates: Partial<Omit<User, 'id' | 'createdAt'>>) => usersApi.updateProfile(updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users.profile });
    },
  });
};

export const useUserStats = () => {
  return useQuery({
    queryKey: queryKeys.users.stats,
    queryFn: () => usersApi.getStats(),
  });
};

export const useUserHistory = (params?: { startDate?: string; endDate?: string }) => {
  return useQuery({
    queryKey: queryKeys.users.history(params),
    queryFn: () => usersApi.getHistory(params),
  });
};

export const useUploadAvatar = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => usersApi.uploadAvatar(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users.profile });
    },
  });
};

export const useLeaderboard = (params?: { limit?: number; offset?: number }) => {
  return useQuery({
    queryKey: queryKeys.users.leaderboard(params),
    queryFn: () => usersApi.getLeaderboard(params),
  });
};
