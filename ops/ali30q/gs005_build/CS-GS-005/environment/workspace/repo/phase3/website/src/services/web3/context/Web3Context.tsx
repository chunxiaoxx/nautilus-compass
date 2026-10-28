import { createContext, useContext } from 'react';
import { useWallet as useWalletHook } from '../hooks/useWallet';
import type { WalletState, WalletProvider } from '../types';

interface Web3ContextValue extends WalletState {
  connect: (provider?: WalletProvider) => Promise<void>;
  disconnect: () => Promise<void>;
  switchNetwork: (network: string) => Promise<void>;
  refreshBalance: () => Promise<void>;
  signMessage: (message: string) => Promise<string | null>;
}

const Web3Context = createContext<Web3ContextValue | null>(null);

/**
 * Web3 Provider Component
 * Wraps the application with Web3 context
 */
export function Web3Provider({ children }: { children: React.ReactNode }) {
  const wallet = useWalletHook();

  const value: Web3ContextValue = {
    address: wallet.address,
    chainId: wallet.chainId,
    balance: wallet.balance,
    isConnecting: wallet.isConnecting,
    isConnected: wallet.isConnected,
    error: wallet.error,
    connect: wallet.connect,
    disconnect: wallet.disconnect,
    switchNetwork: wallet.switchNetwork,
    refreshBalance: wallet.refreshBalance,
    signMessage: wallet.signMessage,
  };

  return <Web3Context.Provider value={value}>{children}</Web3Context.Provider>;
}

/**
 * Hook to access Web3 context
 */
export function useWeb3() {
  const context = useContext(Web3Context);

  if (!context) {
    throw new Error('useWeb3 must be used within Web3Provider');
  }

  return context;
}
