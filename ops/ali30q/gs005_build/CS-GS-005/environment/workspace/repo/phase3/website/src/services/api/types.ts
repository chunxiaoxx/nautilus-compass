// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data: T | null;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}

// Auth Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  username: string;
}

export interface AuthResponse {
  token: string;
  refreshToken: string;
  user: User;
}

export interface User {
  id: string;
  email: string;
  username: string;
  avatar?: string;
  role: 'user' | 'admin';
  createdAt: string;
}

// Task Types
export interface Task {
  id: string;
  title: string;
  description: string;
  type: 'data_collection' | 'annotation' | 'verification' | 'computation';
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  reward: number;
  deadline?: string;
  requirements: Record<string, any>;
  createdBy: string;
  assignedTo?: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreateTaskRequest {
  title: string;
  description: string;
  type: Task['type'];
  reward: number;
  deadline?: string;
  requirements?: Record<string, any>;
}

export interface UpdateTaskRequest {
  title?: string;
  description?: string;
  status?: Task['status'];
  reward?: number;
  deadline?: string;
  requirements?: Record<string, any>;
}

export interface TaskResult {
  taskId: string;
  result: Record<string, any>;
  submittedAt: string;
}

// Agent Types
export interface Agent {
  id: string;
  name: string;
  type: 'worker' | 'validator' | 'coordinator';
  status: 'active' | 'inactive' | 'busy';
  capabilities: string[];
  performance: {
    tasksCompleted: number;
    successRate: number;
    averageTime: number;
  };
  owner: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreateAgentRequest {
  name: string;
  type: Agent['type'];
  capabilities: string[];
}

export interface UpdateAgentRequest {
  name?: string;
  status?: Agent['status'];
  capabilities?: string[];
}

// User Stats Types
export interface UserStats {
  tasksCompleted: number;
  tasksInProgress: number;
  totalEarnings: number;
  successRate: number;
  rank: number;
  agentsOwned: number;
}

export interface UserHistory {
  tasks: Task[];
  earnings: {
    date: string;
    amount: number;
  }[];
}

// Query Parameters
export interface TaskQueryParams {
  page?: number;
  limit?: number;
  status?: Task['status'];
  type?: Task['type'];
  sortBy?: 'createdAt' | 'reward' | 'deadline';
  order?: 'asc' | 'desc';
}

export interface AgentQueryParams {
  page?: number;
  limit?: number;
  status?: Agent['status'];
  type?: Agent['type'];
}
