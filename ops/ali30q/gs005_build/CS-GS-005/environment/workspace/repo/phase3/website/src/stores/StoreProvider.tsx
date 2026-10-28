import React from 'react';
import { useAuthInit } from '@/stores/hooks';

/**
 * Provider component to initialize stores on app mount
 */
export const StoreProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  useAuthInit();

  return <>{children}</>;
};
