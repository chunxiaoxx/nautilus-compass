import { apiClient } from './client';
import type { ApiResponse } from './types';

/**
 * Cache Configuration
 */
interface CacheConfig {
  ttl: number; // Time to live in milliseconds
  maxSize: number; // Maximum number of cached items
}

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

/**
 * Simple In-Memory Cache
 */
class ApiCache {
  private cache: Map<string, CacheEntry<any>>;
  private config: CacheConfig;

  constructor(config: Partial<CacheConfig> = {}) {
    this.cache = new Map();
    this.config = {
      ttl: config.ttl || 5 * 60 * 1000, // Default 5 minutes
      maxSize: config.maxSize || 100,
    };
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);

    if (!entry) {
      return null;
    }

    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      return null;
    }

    return entry.data as T;
  }

  set<T>(key: string, data: T, ttl?: number): void {
    // Enforce max size
    if (this.cache.size >= this.config.maxSize) {
      const firstKey = this.cache.keys().next().value as string;
      if (firstKey) {
        this.cache.delete(firstKey);
      }
    }

    const expiresAt = Date.now() + (ttl || this.config.ttl);
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      expiresAt,
    });
  }

  delete(key: string): void {
    this.cache.delete(key);
  }

  clear(): void {
    this.cache.clear();
  }

  has(key: string): boolean {
    const entry = this.cache.get(key);
    if (!entry) {
      return false;
    }

    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      return false;
    }

    return true;
  }

  invalidatePattern(pattern: string): void {
    const regex = new RegExp(pattern);
    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        this.cache.delete(key);
      }
    }
  }
}

/**
 * Global Cache Instance
 */
export const apiCache = new ApiCache({
  ttl: 5 * 60 * 1000, // 5 minutes
  maxSize: 100,
});

/**
 * Cached Request Wrapper
 */
export const cachedRequest = async <T>(
  key: string,
  requestFn: () => Promise<{ data: ApiResponse<T> }>,
  ttl?: number
): Promise<T> => {
  // Check cache first
  const cached = apiCache.get<T>(key);
  if (cached !== null) {
    return cached;
  }

  // Make request
  const { data: response } = await requestFn();

  if (response.success && response.data) {
    apiCache.set(key, response.data, ttl);
    return response.data;
  }

  throw new Error(response.error || 'Request failed');
};

/**
 * Cache Invalidation Helpers
 */
export const cacheInvalidation = {
  // Invalidate all task-related cache
  tasks: () => {
    apiCache.invalidatePattern('^tasks');
  },

  // Invalidate specific task
  task: (taskId: string) => {
    apiCache.delete(`tasks:${taskId}`);
    apiCache.invalidatePattern('^tasks:list');
  },

  // Invalidate all agent-related cache
  agents: () => {
    apiCache.invalidatePattern('^agents');
  },

  // Invalidate specific agent
  agent: (agentId: string) => {
    apiCache.delete(`agents:${agentId}`);
    apiCache.invalidatePattern('^agents:list');
  },

  // Invalidate user profile
  profile: () => {
    apiCache.delete('users:profile');
    apiCache.delete('users:stats');
  },

  // Clear all cache
  all: () => {
    apiCache.clear();
  },
};

/**
 * Prefetch Helpers
 */
export const prefetch = {
  // Prefetch tasks
  tasks: async (params?: any) => {
    const key = `tasks:list:${JSON.stringify(params || {})}`;
    if (!apiCache.has(key)) {
      await cachedRequest(
        key,
        () => apiClient.get('/api/tasks', { params })
      );
    }
  },

  // Prefetch task detail
  task: async (taskId: string) => {
    const key = `tasks:${taskId}`;
    if (!apiCache.has(key)) {
      await cachedRequest(
        key,
        () => apiClient.get(`/api/tasks/${taskId}`)
      );
    }
  },

  // Prefetch agents
  agents: async (params?: any) => {
    const key = `agents:list:${JSON.stringify(params || {})}`;
    if (!apiCache.has(key)) {
      await cachedRequest(
        key,
        () => apiClient.get('/api/agents', { params })
      );
    }
  },

  // Prefetch agent detail
  agent: async (agentId: string) => {
    const key = `agents:${agentId}`;
    if (!apiCache.has(key)) {
      await cachedRequest(
        key,
        () => apiClient.get(`/api/agents/${agentId}`)
      );
    }
  },

  // Prefetch user profile
  profile: async () => {
    const key = 'users:profile';
    if (!apiCache.has(key)) {
      await cachedRequest(
        key,
        () => apiClient.get('/api/users/profile')
      );
    }
  },
};

/**
 * Cache Statistics
 */
export const getCacheStats = () => {
  const entries = Array.from(apiCache['cache'].entries());
  const now = Date.now();

  return {
    size: entries.length,
    maxSize: apiCache['config'].maxSize,
    entries: entries.map(([key, entry]) => ({
      key,
      age: now - entry.timestamp,
      ttl: entry.expiresAt - now,
      expired: now > entry.expiresAt,
    })),
  };
};
