/**
 * API Configuration
 *
 * Centralized configuration for API integration
 */

/**
 * Environment Variables
 */
export const ENV = {
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://43.160.239.61:8000',
  API_TIMEOUT: Number(import.meta.env.VITE_API_TIMEOUT) || 30000,
  NODE_ENV: import.meta.env.MODE || 'development',
} as const;

/**
 * API Configuration
 */
export const API_CONFIG = {
  baseURL: ENV.API_BASE_URL,
  timeout: ENV.API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
} as const;

/**
 * Retry Configuration
 */
export const RETRY_CONFIG = {
  maxRetries: 3,
  retryDelay: 1000,
  retryableStatusCodes: [408, 429, 500, 502, 503, 504],
} as const;

/**
 * Cache Configuration
 */
export const CACHE_CONFIG = {
  defaultTTL: 5 * 60 * 1000, // 5 minutes
  maxSize: 100,
  strategies: {
    tasks: {
      list: 2 * 60 * 1000, // 2 minutes
      detail: 5 * 60 * 1000, // 5 minutes
    },
    agents: {
      list: 2 * 60 * 1000, // 2 minutes
      detail: 5 * 60 * 1000, // 5 minutes
    },
    users: {
      profile: 10 * 60 * 1000, // 10 minutes
      stats: 5 * 60 * 1000, // 5 minutes
    },
  },
} as const;

/**
 * React Query Configuration
 */
export const QUERY_CONFIG = {
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
      retry: 3,
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
    },
  },
} as const;

/**
 * Token Configuration
 */
export const TOKEN_CONFIG = {
  storageKey: 'nautilus_token',
  refreshTokenKey: 'nautilus_refresh_token',
  expirationBuffer: 5 * 60 * 1000, // 5 minutes before expiration
} as const;

/**
 * Pagination Configuration
 */
export const PAGINATION_CONFIG = {
  defaultPage: 1,
  defaultLimit: 10,
  maxLimit: 100,
} as const;

/**
 * API Endpoints
 */
export const API_ENDPOINTS = {
  auth: {
    login: '/api/auth/login',
    register: '/api/auth/register',
    logout: '/api/auth/logout',
    refresh: '/api/auth/refresh',
    profile: '/api/auth/profile',
    verify: '/api/auth/verify',
    passwordReset: {
      request: '/api/auth/password-reset/request',
      confirm: '/api/auth/password-reset/confirm',
    },
  },
  tasks: {
    base: '/api/tasks',
    detail: (id: string) => `/api/tasks/${id}`,
    accept: (id: string) => `/api/tasks/${id}/accept`,
    submit: (id: string) => `/api/tasks/${id}/submit`,
    cancel: (id: string) => `/api/tasks/${id}/cancel`,
    results: (id: string) => `/api/tasks/${id}/results`,
    my: '/api/tasks/my',
    available: '/api/tasks/available',
  },
  agents: {
    base: '/api/agents',
    detail: (id: string) => `/api/agents/${id}`,
    start: (id: string) => `/api/agents/${id}/start`,
    stop: (id: string) => `/api/agents/${id}/stop`,
    metrics: (id: string) => `/api/agents/${id}/metrics`,
    assign: (id: string) => `/api/agents/${id}/assign`,
    tasks: (id: string) => `/api/agents/${id}/tasks`,
    my: '/api/agents/my',
  },
  users: {
    profile: '/api/users/profile',
    stats: '/api/users/stats',
    history: '/api/users/history',
    avatar: '/api/users/avatar',
    detail: (id: string) => `/api/users/${id}`,
    userStats: (id: string) => `/api/users/${id}/stats`,
    changePassword: '/api/users/change-password',
    deleteAccount: '/api/users/delete-account',
    leaderboard: '/api/users/leaderboard',
  },
} as const;

/**
 * Error Messages
 */
export const ERROR_MESSAGES = {
  network: 'Network error. Please check your connection.',
  timeout: 'Request timeout. Please try again.',
  unauthorized: 'Unauthorized. Please login again.',
  forbidden: 'You do not have permission to perform this action.',
  notFound: 'Resource not found.',
  serverError: 'Server error. Please try again later.',
  unknown: 'An unknown error occurred.',
} as const;

/**
 * Success Messages
 */
export const SUCCESS_MESSAGES = {
  login: 'Login successful!',
  register: 'Registration successful!',
  logout: 'Logout successful!',
  taskCreated: 'Task created successfully!',
  taskUpdated: 'Task updated successfully!',
  taskDeleted: 'Task deleted successfully!',
  taskAccepted: 'Task accepted successfully!',
  taskSubmitted: 'Task submitted successfully!',
  agentCreated: 'Agent created successfully!',
  agentUpdated: 'Agent updated successfully!',
  agentDeleted: 'Agent deleted successfully!',
  agentStarted: 'Agent started successfully!',
  agentStopped: 'Agent stopped successfully!',
  profileUpdated: 'Profile updated successfully!',
  avatarUploaded: 'Avatar uploaded successfully!',
  passwordChanged: 'Password changed successfully!',
} as const;

/**
 * Validation Rules
 */
export const VALIDATION_RULES = {
  email: {
    pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    message: 'Invalid email address',
  },
  password: {
    minLength: 8,
    pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
    message: 'Password must be at least 8 characters and contain uppercase, lowercase, and number',
  },
  username: {
    minLength: 3,
    maxLength: 20,
    pattern: /^[a-zA-Z0-9_]+$/,
    message: 'Username must be 3-20 characters and contain only letters, numbers, and underscores',
  },
} as const;

/**
 * File Upload Configuration
 */
export const UPLOAD_CONFIG = {
  avatar: {
    maxSize: 5 * 1024 * 1024, // 5MB
    allowedTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    allowedExtensions: ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
  },
} as const;

/**
 * Feature Flags
 */
export const FEATURE_FLAGS = {
  enableDevTools: ENV.NODE_ENV === 'development',
  enableCache: true,
  enableRetry: true,
  enableOptimisticUpdates: true,
  enablePrefetch: true,
} as const;
