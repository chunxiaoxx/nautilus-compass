import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useUIStore } from '../uiStore';

describe('uiStore', () => {
  beforeEach(() => {
    useUIStore.setState({
      theme: 'system',
      sidebarOpen: true,
      notifications: [],
      isLoading: false,
      loadingMessage: null,
    });
  });

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useUIStore());

    expect(result.current.theme).toBe('system');
    expect(result.current.sidebarOpen).toBe(true);
    expect(result.current.notifications).toEqual([]);
    expect(result.current.isLoading).toBe(false);
  });

  it('should set theme', () => {
    const { result } = renderHook(() => useUIStore());

    act(() => {
      result.current.setTheme('dark');
    });

    expect(result.current.theme).toBe('dark');
  });

  it('should toggle theme', () => {
    const { result } = renderHook(() => useUIStore());

    act(() => {
      result.current.setTheme('light');
    });

    act(() => {
      result.current.toggleTheme();
    });

    expect(result.current.theme).toBe('dark');

    act(() => {
      result.current.toggleTheme();
    });

    expect(result.current.theme).toBe('system');
  });

  it('should toggle sidebar', () => {
    const { result } = renderHook(() => useUIStore());

    expect(result.current.sidebarOpen).toBe(true);

    act(() => {
      result.current.toggleSidebar();
    });

    expect(result.current.sidebarOpen).toBe(false);

    act(() => {
      result.current.toggleSidebar();
    });

    expect(result.current.sidebarOpen).toBe(true);
  });

  it('should add notification', () => {
    const { result } = renderHook(() => useUIStore());

    act(() => {
      result.current.addNotification({
        type: 'success',
        title: 'Success',
        message: 'Operation completed',
        duration: 3000,
      });
    });

    expect(result.current.notifications).toHaveLength(1);
    expect(result.current.notifications[0].type).toBe('success');
    expect(result.current.notifications[0].title).toBe('Success');
  });

  it('should remove notification', () => {
    const { result } = renderHook(() => useUIStore());

    act(() => {
      result.current.addNotification({
        type: 'info',
        title: 'Info',
        message: 'Information',
      });
    });

    const notificationId = result.current.notifications[0].id;

    act(() => {
      result.current.removeNotification(notificationId);
    });

    expect(result.current.notifications).toHaveLength(0);
  });

  it('should clear all notifications', () => {
    const { result } = renderHook(() => useUIStore());

    act(() => {
      result.current.addNotification({
        type: 'success',
        title: 'Success 1',
        message: 'Message 1',
      });
      result.current.addNotification({
        type: 'error',
        title: 'Error 1',
        message: 'Message 2',
      });
    });

    expect(result.current.notifications).toHaveLength(2);

    act(() => {
      result.current.clearNotifications();
    });

    expect(result.current.notifications).toHaveLength(0);
  });

  it('should set loading state', () => {
    const { result } = renderHook(() => useUIStore());

    act(() => {
      result.current.setLoading(true, 'Loading data...');
    });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.loadingMessage).toBe('Loading data...');

    act(() => {
      result.current.setLoading(false);
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.loadingMessage).toBeNull();
  });

  it('should set sidebar open state', () => {
    const { result } = renderHook(() => useUIStore());

    act(() => {
      result.current.setSidebarOpen(false);
    });

    expect(result.current.sidebarOpen).toBe(false);

    act(() => {
      result.current.setSidebarOpen(true);
    });

    expect(result.current.sidebarOpen).toBe(true);
  });
});
