import React, { createContext, useContext, useEffect, useState } from 'react';
import { authApi } from './auth';
import { TokenManager } from './client';
import type { User } from './types';

/**
 * Auth Context Type
 */
interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, username: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

/**
 * Auth Context
 */
const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Auth Provider Component
 *
 * Provides authentication state and methods to the entire app
 *
 * @example
 * ```tsx
 * import { AuthProvider } from './services/api/auth-context';
 *
 * function App() {
 *   return (
 *     <AuthProvider>
 *       <YourApp />
 *     </AuthProvider>
 *   );
 * }
 * ```
 */
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check authentication status on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        if (authApi.isAuthenticated()) {
          const profile = await authApi.getProfile();
          setUser(profile);
        }
      } catch (error) {
        console.error('Failed to fetch user profile:', error);
        TokenManager.clearTokens();
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const result = await authApi.login({ email, password });
      setUser(result.user);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string, username: string) => {
    setIsLoading(true);
    try {
      const result = await authApi.register({ email, password, username });
      setUser(result.user);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await authApi.logout();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshUser = async () => {
    try {
      const profile = await authApi.getProfile();
      setUser(profile);
    } catch (error) {
      console.error('Failed to refresh user:', error);
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * useAuth Hook
 *
 * Access authentication state and methods
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { user, isAuthenticated, login, logout } = useAuth();
 *
 *   if (!isAuthenticated) {
 *     return <LoginForm onLogin={login} />;
 *   }
 *
 *   return (
 *     <div>
 *       <h1>Welcome, {user?.username}!</h1>
 *       <button onClick={logout}>Logout</button>
 *     </div>
 *   );
 * }
 * ```
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

/**
 * Protected Route Component
 *
 * Redirects to login if user is not authenticated
 *
 * @example
 * ```tsx
 * import { ProtectedRoute } from './services/api/auth-context';
 *
 * function App() {
 *   return (
 *     <Routes>
 *       <Route path="/login" element={<Login />} />
 *       <Route
 *         path="/dashboard"
 *         element={
 *           <ProtectedRoute>
 *             <Dashboard />
 *           </ProtectedRoute>
 *         }
 *       />
 *     </Routes>
 *   );
 * }
 * ```
 */
export const ProtectedRoute: React.FC<{
  children: React.ReactNode;
  redirectTo?: string;
}> = ({ children, redirectTo = '/login' }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        Loading...
      </div>
    );
  }

  if (!isAuthenticated) {
    window.location.href = redirectTo;
    return null;
  }

  return <>{children}</>;
};

/**
 * Public Route Component
 *
 * Redirects to dashboard if user is already authenticated
 *
 * @example
 * ```tsx
 * import { PublicRoute } from './services/api/auth-context';
 *
 * function App() {
 *   return (
 *     <Routes>
 *       <Route
 *         path="/login"
 *         element={
 *           <PublicRoute>
 *             <Login />
 *           </PublicRoute>
 *         }
 *       />
 *       <Route path="/dashboard" element={<Dashboard />} />
 *     </Routes>
 *   );
 * }
 * ```
 */
export const PublicRoute: React.FC<{
  children: React.ReactNode;
  redirectTo?: string;
}> = ({ children, redirectTo = '/dashboard' }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        Loading...
      </div>
    );
  }

  if (isAuthenticated) {
    window.location.href = redirectTo;
    return null;
  }

  return <>{children}</>;
};
