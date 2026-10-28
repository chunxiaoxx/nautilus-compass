import React from 'react';
import { useLoading } from '@/stores/hooks';

/**
 * Global loading overlay component
 */
export const LoadingOverlay: React.FC = () => {
  const { isLoading, loadingMessage } = useLoading();

  if (!isLoading) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-xl">
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          {loadingMessage && (
            <p className="text-gray-700 dark:text-gray-300 text-sm">
              {loadingMessage}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
