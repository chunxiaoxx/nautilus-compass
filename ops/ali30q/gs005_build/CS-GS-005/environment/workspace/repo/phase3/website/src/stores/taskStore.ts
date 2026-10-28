import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import axios from 'axios';

export interface Task {
  id: string;
  title: string;
  description: string;
  type: 'data_collection' | 'data_labeling' | 'model_training' | 'validation';
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  reward: number;
  deadline: string;
  requirements: Record<string, any>;
  createdBy: string;
  assignedTo?: string;
  createdAt: string;
  updatedAt: string;
}

export interface TaskFilters {
  status?: string;
  type?: string;
  search?: string;
}

export interface Pagination {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

interface TaskState {
  tasks: Task[];
  currentTask: Task | null;
  filters: TaskFilters;
  pagination: Pagination;
  isLoading: boolean;
  error: string | null;
}

interface TaskActions {
  fetchTasks: (filters?: TaskFilters, page?: number, limit?: number) => Promise<void>;
  fetchTaskById: (id: string) => Promise<void>;
  createTask: (taskData: Partial<Task>) => Promise<Task>;
  updateTask: (id: string, updates: Partial<Task>) => Promise<void>;
  acceptTask: (id: string) => Promise<void>;
  submitResult: (id: string, result: any) => Promise<void>;
  setFilters: (filters: TaskFilters) => void;
  setCurrentTask: (task: Task | null) => void;
  clearError: () => void;
}

type TaskStore = TaskState & TaskActions;

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api';

export const useTaskStore = create<TaskStore>()(
  devtools(
    (set) => ({
      // Initial state
      tasks: [],
      currentTask: null,
      filters: {},
      pagination: {
        page: 1,
        limit: 10,
        total: 0,
        totalPages: 0,
      },
      isLoading: false,
      error: null,

      // Actions
      fetchTasks: async (filters = {}, page = 1, limit = 10) => {
        set({ isLoading: true, error: null });
        try {
          const params = new URLSearchParams({
            page: page.toString(),
            limit: limit.toString(),
            ...filters,
          });

          const response = await axios.get(`${API_BASE_URL}/tasks?${params}`);
          const { tasks, pagination } = response.data.data;

          set({
            tasks,
            pagination,
            filters,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || 'Failed to fetch tasks';
          set({
            tasks: [],
            isLoading: false,
            error: errorMessage,
          });
          throw new Error(errorMessage);
        }
      },

      fetchTaskById: async (id: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await axios.get(`${API_BASE_URL}/tasks/${id}`);
          const task = response.data.data;

          set({
            currentTask: task,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || 'Failed to fetch task';
          set({
            currentTask: null,
            isLoading: false,
            error: errorMessage,
          });
          throw new Error(errorMessage);
        }
      },

      createTask: async (taskData: Partial<Task>) => {
        set({ isLoading: true, error: null });
        try {
          const response = await axios.post(`${API_BASE_URL}/tasks`, taskData);
          const newTask = response.data.data;

          set((state) => ({
            tasks: [newTask, ...state.tasks],
            isLoading: false,
            error: null,
          }));

          return newTask;
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || 'Failed to create task';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw new Error(errorMessage);
        }
      },

      updateTask: async (id: string, updates: Partial<Task>) => {
        set({ isLoading: true, error: null });
        try {
          const response = await axios.put(`${API_BASE_URL}/tasks/${id}`, updates);
          const updatedTask = response.data.data;

          set((state) => ({
            tasks: state.tasks.map((task) =>
              task.id === id ? updatedTask : task
            ),
            currentTask: state.currentTask?.id === id ? updatedTask : state.currentTask,
            isLoading: false,
            error: null,
          }));
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || 'Failed to update task';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw new Error(errorMessage);
        }
      },

      acceptTask: async (id: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await axios.post(`${API_BASE_URL}/tasks/${id}/accept`);
          const updatedTask = response.data.data;

          set((state) => ({
            tasks: state.tasks.map((task) =>
              task.id === id ? updatedTask : task
            ),
            currentTask: state.currentTask?.id === id ? updatedTask : state.currentTask,
            isLoading: false,
            error: null,
          }));
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || 'Failed to accept task';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw new Error(errorMessage);
        }
      },

      submitResult: async (id: string, result: any) => {
        set({ isLoading: true, error: null });
        try {
          const response = await axios.post(`${API_BASE_URL}/tasks/${id}/submit`, {
            result,
          });
          const updatedTask = response.data.data;

          set((state) => ({
            tasks: state.tasks.map((task) =>
              task.id === id ? updatedTask : task
            ),
            currentTask: state.currentTask?.id === id ? updatedTask : state.currentTask,
            isLoading: false,
            error: null,
          }));
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || 'Failed to submit result';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw new Error(errorMessage);
        }
      },

      setFilters: (filters: TaskFilters) => {
        set({ filters });
      },

      setCurrentTask: (task: Task | null) => {
        set({ currentTask: task });
      },

      clearError: () => {
        set({ error: null });
      },
    }),
    { name: 'TaskStore' }
  )
);
