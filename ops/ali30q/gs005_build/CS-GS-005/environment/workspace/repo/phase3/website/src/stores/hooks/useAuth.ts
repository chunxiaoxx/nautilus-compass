import { useEffect } from 'react';
import { useAuthStore } from '@/stores';

/**
 * Hook to initialize authentication on app mount
 * Checks if user is authenticated and validates token
 */
export const useAuthInit = () => {
  const checkAuth = useAuthStore((state) => state.checkAuth);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);
};

/**
 * Hook to protect routes - redirects to login if not authenticated
 */
export const useRequireAuth = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isLoading = useAuthStore((state) => state.isLoading);

  return { isAuthenticated, isLoading };
};

/**
 * Hook to get current user info
 */
export const useCurrentUser = () => {
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  return { user, isAuthenticated };
};
