import { StateCreator } from 'zustand';

// Logger middleware for development
export const logger = <T extends object>(
  config: StateCreator<T>
): StateCreator<T> => {
  return (set, get, api) =>
    config(
      (args) => {
        if (import.meta.env.DEV) {
          console.log('  applying', args);
        }
        set(args);
        if (import.meta.env.DEV) {
          console.log('  new state', get());
        }
      },
      get,
      api
    );
};

// Error handler middleware
export const errorHandler = <T extends object>(
  config: StateCreator<T>
): StateCreator<T> => {
  return (set, get, api) =>
    config(
      (args) => {
        try {
          set(args);
        } catch (error) {
          console.error('State update error:', error);
          // Optionally notify user via UI store
          if (typeof window !== 'undefined') {
            const event = new CustomEvent('store-error', {
              detail: { error, state: get() },
            });
            window.dispatchEvent(event);
          }
        }
      },
      get,
      api
    );
};

// Reset middleware - adds a reset function to any store
export const resetters = new Set<() => void>();

export const resetAllStores = () => {
  resetters.forEach((resetter) => resetter());
};

export const createResetMiddleware = <T extends object>(
  initialState: T
) => {
  return (config: StateCreator<T>): StateCreator<T> => {
    return (set, get, api) => {
      resetters.add(() => set(initialState));
      return config(set, get, api);
    };
  };
};

// Immer middleware for immutable updates (optional, requires immer package)
// Uncomment if you install immer: npm install immer
/*
import { produce, Draft } from 'immer';

export const immer = <T extends object>(
  config: StateCreator<T>
): StateCreator<T> => {
  return (set, get, api) =>
    config(
      (partial, replace) => {
        const nextState =
          typeof partial === 'function'
            ? produce(partial as (state: Draft<T>) => void)
            : partial;
        return set(nextState, replace);
      },
      get,
      api
    );
};
*/
