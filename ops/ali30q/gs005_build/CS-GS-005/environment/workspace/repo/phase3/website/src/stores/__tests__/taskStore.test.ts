import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useTaskStore } from '../taskStore';
import axios from 'axios';

vi.mock('axios');

describe('taskStore', () => {
  const mockTasks = [
    {
      id: '1',
      title: 'Task 1',
      description: 'Description 1',
      type: 'data_collection' as const,
      status: 'pending' as const,
      reward: 100,
      deadline: '2024-12-31',
      requirements: {},
      createdBy: 'user1',
      createdAt: '2024-01-01',
      updatedAt: '2024-01-01',
    },
    {
      id: '2',
      title: 'Task 2',
      description: 'Description 2',
      type: 'data_labeling' as const,
      status: 'in_progress' as const,
      reward: 200,
      deadline: '2024-12-31',
      requirements: {},
      createdBy: 'user1',
      assignedTo: 'user2',
      createdAt: '2024-01-01',
      updatedAt: '2024-01-01',
    },
  ];

  beforeEach(() => {
    useTaskStore.setState({
      tasks: [],
      currentTask: null,
      filters: {},
      pagination: { page: 1, limit: 10, total: 0, totalPages: 0 },
      isLoading: false,
      error: null,
    });
    vi.clearAllMocks();
  });

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useTaskStore());

    expect(result.current.tasks).toEqual([]);
    expect(result.current.currentTask).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should fetch tasks successfully', async () => {
    (axios.get as any).mockResolvedValueOnce({
      data: {
        data: {
          tasks: mockTasks,
          pagination: { page: 1, limit: 10, total: 2, totalPages: 1 },
        },
      },
    });

    const { result } = renderHook(() => useTaskStore());

    await act(async () => {
      await result.current.fetchTasks();
    });

    expect(result.current.tasks).toEqual(mockTasks);
    expect(result.current.pagination.total).toBe(2);
    expect(result.current.error).toBeNull();
  });

  it('should handle fetch tasks error', async () => {
    (axios.get as any).mockRejectedValueOnce({
      response: { data: { error: 'Failed to fetch' } },
    });

    const { result } = renderHook(() => useTaskStore());

    await act(async () => {
      try {
        await result.current.fetchTasks();
      } catch (error) {
        // Expected error
      }
    });

    expect(result.current.tasks).toEqual([]);
    expect(result.current.error).toBe('Failed to fetch');
  });

  it('should create task successfully', async () => {
    const newTask = mockTasks[0];

    (axios.post as any).mockResolvedValueOnce({
      data: { data: newTask },
    });

    const { result } = renderHook(() => useTaskStore());

    await act(async () => {
      await result.current.createTask({ title: 'Task 1', description: 'Description 1' });
    });

    expect(result.current.tasks).toContainEqual(newTask);
  });

  it('should update task successfully', async () => {
    const updatedTask = { ...mockTasks[0], title: 'Updated Task' };

    (axios.put as any).mockResolvedValueOnce({
      data: { data: updatedTask },
    });

    const { result } = renderHook(() => useTaskStore());

    act(() => {
      useTaskStore.setState({ tasks: [mockTasks[0]] });
    });

    await act(async () => {
      await result.current.updateTask('1', { title: 'Updated Task' });
    });

    expect(result.current.tasks[0].title).toBe('Updated Task');
  });

  it('should accept task successfully', async () => {
    const acceptedTask = { ...mockTasks[0], status: 'in_progress' as const, assignedTo: 'user2' };

    (axios.post as any).mockResolvedValueOnce({
      data: { data: acceptedTask },
    });

    const { result } = renderHook(() => useTaskStore());

    act(() => {
      useTaskStore.setState({ tasks: [mockTasks[0]] });
    });

    await act(async () => {
      await result.current.acceptTask('1');
    });

    expect(result.current.tasks[0].status).toBe('in_progress');
  });

  it('should set filters', () => {
    const { result } = renderHook(() => useTaskStore());

    act(() => {
      result.current.setFilters({ status: 'pending', type: 'data_collection' });
    });

    expect(result.current.filters).toEqual({ status: 'pending', type: 'data_collection' });
  });

  it('should set current task', () => {
    const { result } = renderHook(() => useTaskStore());

    act(() => {
      result.current.setCurrentTask(mockTasks[0]);
    });

    expect(result.current.currentTask).toEqual(mockTasks[0]);
  });
});
