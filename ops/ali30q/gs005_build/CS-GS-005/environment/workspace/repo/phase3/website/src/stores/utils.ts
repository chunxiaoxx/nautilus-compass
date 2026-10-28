import { useAuthStore, useTaskStore, useAgentStore, useWalletStore, useUIStore } from './index';

/**
 * Utility to get all store states (useful for debugging)
 */
export const getAllStoreStates = () => {
  return {
    auth: useAuthStore.getState(),
    task: useTaskStore.getState(),
    agent: useAgentStore.getState(),
    wallet: useWalletStore.getState(),
    ui: useUIStore.getState(),
  };
};

/**
 * Utility to reset all stores to initial state
 */
export const resetAllStores = () => {
  useAuthStore.getState().logout();
  useWalletStore.getState().disconnect();
  useUIStore.getState().clearNotifications();
  // Task and Agent stores will be cleared on logout
};

/**
 * Utility to subscribe to multiple stores
 */
export const subscribeToStores = (callback: () => void) => {
  const unsubAuth = useAuthStore.subscribe(callback);
  const unsubTask = useTaskStore.subscribe(callback);
  const unsubAgent = useAgentStore.subscribe(callback);
  const unsubWallet = useWalletStore.subscribe(callback);
  const unsubUI = useUIStore.subscribe(callback);

  return () => {
    unsubAuth();
    unsubTask();
    unsubAgent();
    unsubWallet();
    unsubUI();
  };
};

/**
 * Utility to check if user is authenticated and has wallet connected
 */
export const isFullyAuthenticated = () => {
  const { isAuthenticated } = useAuthStore.getState();
  const { isConnected } = useWalletStore.getState();
  return isAuthenticated && isConnected;
};

/**
 * Utility to handle API errors and show notifications
 */
export const handleApiError = (error: any, defaultMessage = 'An error occurred') => {
  const { addNotification } = useUIStore.getState();
  const errorMessage = error.response?.data?.error || error.message || defaultMessage;

  addNotification({
    type: 'error',
    title: 'Error',
    message: errorMessage,
    duration: 5000,
  });

  return errorMessage;
};

/**
 * Utility to show success notification
 */
export const showSuccessNotification = (message: string, title = 'Success') => {
  const { addNotification } = useUIStore.getState();
  addNotification({
    type: 'success',
    title,
    message,
    duration: 3000,
  });
};

/**
 * Utility to get user role
 */
export const getUserRole = () => {
  const { user } = useAuthStore.getState();
  return user?.role || null;
};

/**
 * Utility to check if user has specific role
 */
export const hasRole = (role: string) => {
  const userRole = getUserRole();
  return userRole === role;
};

/**
 * Utility to format balance
 */
export const formatBalance = (balance: string, decimals = 4) => {
  const num = parseFloat(balance);
  if (isNaN(num)) return '0';
  return num.toFixed(decimals);
};

/**
 * Utility to format address
 */
export const formatAddress = (address: string | null, startChars = 6, endChars = 4) => {
  if (!address) return '';
  if (address.length <= startChars + endChars) return address;
  return `${address.slice(0, startChars)}...${address.slice(-endChars)}`;
};

/**
 * Utility to get chain name
 */
export const getChainName = (chainId: number | null) => {
  const chains: Record<number, string> = {
    1: 'Ethereum Mainnet',
    5: 'Goerli Testnet',
    137: 'Polygon Mainnet',
    80001: 'Mumbai Testnet',
  };
  return chainId ? chains[chainId] || 'Unknown Chain' : 'Not Connected';
};

/**
 * Utility to check if store is loading
 */
export const isAnyStoreLoading = () => {
  const authLoading = useAuthStore.getState().isLoading;
  const taskLoading = useTaskStore.getState().isLoading;
  const agentLoading = useAgentStore.getState().isLoading;
  const walletLoading = useWalletStore.getState().isConnecting;
  const uiLoading = useUIStore.getState().isLoading;

  return authLoading || taskLoading || agentLoading || walletLoading || uiLoading;
};

/**
 * Utility to get all errors from stores
 */
export const getAllErrors = () => {
  return {
    auth: useAuthStore.getState().error,
    task: useTaskStore.getState().error,
    agent: useAgentStore.getState().error,
    wallet: useWalletStore.getState().error,
  };
};

/**
 * Utility to clear all errors
 */
export const clearAllErrors = () => {
  useAuthStore.getState().clearError();
  useTaskStore.getState().clearError();
  useAgentStore.getState().clearError();
  useWalletStore.getState().clearError();
};
