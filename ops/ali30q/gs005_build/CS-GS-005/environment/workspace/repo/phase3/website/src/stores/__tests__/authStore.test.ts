import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAuthStore } from '../authStore';
import axios from 'axios';

vi.mock('axios');

describe('authStore', () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
    vi.clearAllMocks();
  });

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useAuthStore());

    expect(result.current.user).toBeNull();
    expect(result.current.token).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should login successfully', async () => {
    const mockUser = { id: '1', email: 'test@example.com', username: 'testuser', role: 'user', createdAt: '2024-01-01' };
    const mockToken = 'mock-token';

    (axios.post as any).mockResolvedValueOnce({
      data: { data: { user: mockUser, token: mockToken } },
    });

    const { result } = renderHook(() => useAuthStore());

    await act(async () => {
      await result.current.login('test@example.com', 'password');
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.token).toBe(mockToken);
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it('should handle login error', async () => {
    (axios.post as any).mockRejectedValueOnce({
      response: { data: { error: 'Invalid credentials' } },
    });

    const { result } = renderHook(() => useAuthStore());

    await act(async () => {
      try {
        await result.current.login('test@example.com', 'wrong-password');
      } catch (error) {
        // Expected error
      }
    });

    expect(result.current.user).toBeNull();
    expect(result.current.token).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.error).toBe('Invalid credentials');
  });

  it('should logout successfully', () => {
    const { result } = renderHook(() => useAuthStore());

    act(() => {
      useAuthStore.setState({
        user: { id: '1', email: 'test@example.com', username: 'testuser', role: 'user', createdAt: '2024-01-01' },
        token: 'mock-token',
        isAuthenticated: true,
      });
    });

    act(() => {
      result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(result.current.token).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('should clear error', () => {
    const { result } = renderHook(() => useAuthStore());

    act(() => {
      useAuthStore.setState({ error: 'Some error' });
    });

    expect(result.current.error).toBe('Some error');

    act(() => {
      result.current.clearError();
    });

    expect(result.current.error).toBeNull();
  });
});
