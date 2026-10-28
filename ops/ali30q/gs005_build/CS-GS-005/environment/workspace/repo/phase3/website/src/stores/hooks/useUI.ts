import { useCallback } from 'react';
import { useUIStore } from '@/stores';

/**
 * Hook to manage theme
 */
export const useTheme = () => {
  const { theme, setTheme, toggleTheme } = useUIStore();

  return {
    theme,
    setTheme,
    toggleTheme,
  };
};

/**
 * Hook to manage sidebar
 */
export const useSidebar = () => {
  const { sidebarOpen, toggleSidebar, setSidebarOpen } = useUIStore();

  return {
    sidebarOpen,
    toggleSidebar,
    setSidebarOpen,
  };
};

/**
 * Hook to manage notifications
 */
export const useNotifications = () => {
  const { notifications, addNotification, removeNotification, clearNotifications } = useUIStore();

  const showSuccess = useCallback((title: string, message: string, duration = 3000) => {
    addNotification({ type: 'success', title, message, duration });
  }, [addNotification]);

  const showError = useCallback((title: string, message: string, duration = 5000) => {
    addNotification({ type: 'error', title, message, duration });
  }, [addNotification]);

  const showWarning = useCallback((title: string, message: string, duration = 4000) => {
    addNotification({ type: 'warning', title, message, duration });
  }, [addNotification]);

  const showInfo = useCallback((title: string, message: string, duration = 3000) => {
    addNotification({ type: 'info', title, message, duration });
  }, [addNotification]);

  return {
    notifications,
    addNotification,
    removeNotification,
    clearNotifications,
    showSuccess,
    showError,
    showWarning,
    showInfo,
  };
};

/**
 * Hook to manage loading state
 */
export const useLoading = () => {
  const { isLoading, loadingMessage, setLoading } = useUIStore();

  const startLoading = useCallback((message?: string) => {
    setLoading(true, message);
  }, [setLoading]);

  const stopLoading = useCallback(() => {
    setLoading(false);
  }, [setLoading]);

  return {
    isLoading,
    loadingMessage,
    startLoading,
    stopLoading,
  };
};

/**
 * Hook to show toast notifications with auto-dismiss
 */
export const useToast = () => {
  const addNotification = useUIStore((state) => state.addNotification);

  const toast = useCallback((
    type: 'success' | 'error' | 'warning' | 'info',
    message: string,
    title?: string,
    duration = 3000
  ) => {
    addNotification({
      type,
      title: title || type.charAt(0).toUpperCase() + type.slice(1),
      message,
      duration,
    });
  }, [addNotification]);

  return toast;
};
