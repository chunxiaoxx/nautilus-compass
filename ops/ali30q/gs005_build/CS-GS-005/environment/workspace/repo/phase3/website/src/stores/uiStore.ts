import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

export type Theme = 'light' | 'dark' | 'system';

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
  createdAt: number;
}

interface UIState {
  theme: Theme;
  sidebarOpen: boolean;
  notifications: Notification[];
  isLoading: boolean;
  loadingMessage: string | null;
}

interface UIActions {
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  addNotification: (notification: Omit<Notification, 'id' | 'createdAt'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
  setLoading: (isLoading: boolean, message?: string) => void;
}

type UIStore = UIState & UIActions;

// Generate unique ID for notifications
const generateId = () => `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

// Apply theme to document
const applyTheme = (theme: Theme) => {
  const root = document.documentElement;

  if (theme === 'system') {
    const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light';
    root.classList.toggle('dark', systemTheme === 'dark');
  } else {
    root.classList.toggle('dark', theme === 'dark');
  }
};

export const useUIStore = create<UIStore>()(
  persist(
    (set, get) => ({
      // Initial state
      theme: 'system',
      sidebarOpen: true,
      notifications: [],
      isLoading: false,
      loadingMessage: null,

      // Actions
      setTheme: (theme: Theme) => {
        applyTheme(theme);
        set({ theme });
      },

      toggleTheme: () => {
        const { theme } = get();
        const newTheme: Theme = theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light';
        applyTheme(newTheme);
        set({ theme: newTheme });
      },

      toggleSidebar: () => {
        set((state) => ({ sidebarOpen: !state.sidebarOpen }));
      },

      setSidebarOpen: (open: boolean) => {
        set({ sidebarOpen: open });
      },

      addNotification: (notification) => {
        const newNotification: Notification = {
          ...notification,
          id: generateId(),
          createdAt: Date.now(),
        };

        set((state) => ({
          notifications: [...state.notifications, newNotification],
        }));

        // Auto-remove notification after duration
        const duration = notification.duration || 5000;
        if (duration > 0) {
          setTimeout(() => {
            get().removeNotification(newNotification.id);
          }, duration);
        }
      },

      removeNotification: (id: string) => {
        set((state) => ({
          notifications: state.notifications.filter((n) => n.id !== id),
        }));
      },

      clearNotifications: () => {
        set({ notifications: [] });
      },

      setLoading: (isLoading: boolean, message?: string) => {
        set({
          isLoading,
          loadingMessage: isLoading ? message || null : null,
        });
      },
    }),
    {
      name: 'ui-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        theme: state.theme,
        sidebarOpen: state.sidebarOpen,
      }),
      onRehydrateStorage: () => (state) => {
        // Apply theme after rehydration
        if (state) {
          applyTheme(state.theme);
        }
      },
    }
  )
);

// Listen for system theme changes
if (typeof window !== 'undefined') {
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    const { theme } = useUIStore.getState();
    if (theme === 'system') {
      applyTheme('system');
    }
  });
}
