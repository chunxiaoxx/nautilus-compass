import { useEffect, useCallback } from 'react';
import { useTaskStore } from '@/stores';
import type { TaskFilters } from '@/stores';

/**
 * Hook to fetch and manage tasks with filters and pagination
 */
export const useTasks = (initialFilters?: TaskFilters, page = 1, limit = 10) => {
  const { tasks, pagination, isLoading, error, fetchTasks, setFilters } = useTaskStore();

  useEffect(() => {
    fetchTasks(initialFilters, page, limit);
  }, []);

  const refetch = useCallback(() => {
    const currentFilters = useTaskStore.getState().filters;
    const currentPage = useTaskStore.getState().pagination.page;
    fetchTasks(currentFilters, currentPage, limit);
  }, [limit]);

  const applyFilters = useCallback((filters: TaskFilters) => {
    setFilters(filters);
    fetchTasks(filters, 1, limit);
  }, [limit, setFilters, fetchTasks]);

  const nextPage = useCallback(() => {
    const { filters, pagination } = useTaskStore.getState();
    if (pagination.page < pagination.totalPages) {
      fetchTasks(filters, pagination.page + 1, limit);
    }
  }, [limit, fetchTasks]);

  const prevPage = useCallback(() => {
    const { filters, pagination } = useTaskStore.getState();
    if (pagination.page > 1) {
      fetchTasks(filters, pagination.page - 1, limit);
    }
  }, [limit, fetchTasks]);

  return {
    tasks,
    pagination,
    isLoading,
    error,
    refetch,
    applyFilters,
    nextPage,
    prevPage,
  };
};

/**
 * Hook to manage a single task
 */
export const useTask = (taskId?: string) => {
  const { currentTask, isLoading, error, fetchTaskById, acceptTask, submitResult } = useTaskStore();

  useEffect(() => {
    if (taskId) {
      fetchTaskById(taskId);
    }
  }, [taskId]);

  const accept = useCallback(async () => {
    if (taskId) {
      await acceptTask(taskId);
    }
  }, [taskId, acceptTask]);

  const submit = useCallback(async (result: any) => {
    if (taskId) {
      await submitResult(taskId, result);
    }
  }, [taskId, submitResult]);

  return {
    task: currentTask,
    isLoading,
    error,
    accept,
    submit,
  };
};
