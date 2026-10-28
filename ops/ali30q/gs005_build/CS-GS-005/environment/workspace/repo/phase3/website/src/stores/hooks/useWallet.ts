import { useEffect, useCallback } from 'react';
import { useWalletStore } from '@/stores';

/**
 * Hook to manage wallet connection
 */
export const useWallet = () => {
  const {
    address,
    balance,
    chainId,
    isConnected,
    isConnecting,
    error,
    connect,
    disconnect,
    switchChain,
  } = useWalletStore();

  const connectWallet = useCallback(async () => {
    try {
      await connect();
    } catch (error) {
      console.error('Failed to connect wallet:', error);
    }
  }, [connect]);

  const disconnectWallet = useCallback(() => {
    disconnect();
  }, [disconnect]);

  const changeChain = useCallback(async (chainId: number) => {
    try {
      await switchChain(chainId);
    } catch (error) {
      console.error('Failed to switch chain:', error);
    }
  }, [switchChain]);

  return {
    address,
    balance,
    chainId,
    isConnected,
    isConnecting,
    error,
    connectWallet,
    disconnectWallet,
    changeChain,
  };
};

/**
 * Hook to auto-connect wallet on mount if previously connected
 */
export const useAutoConnectWallet = () => {
  const { isConnected, connect } = useWalletStore();

  useEffect(() => {
    if (isConnected && window.ethereum) {
      // Reconnect if was previously connected
      connect().catch((error) => {
        console.error('Auto-connect failed:', error);
      });
    }
  }, []);
};

/**
 * Hook to check if wallet is on correct chain
 */
export const useRequireChain = (requiredChainId: number) => {
  const { chainId, isConnected, switchChain } = useWalletStore();

  const isCorrectChain = isConnected && chainId === requiredChainId;

  const switchToRequiredChain = useCallback(async () => {
    if (!isCorrectChain) {
      await switchChain(requiredChainId);
    }
  }, [isCorrectChain, requiredChainId, switchChain]);

  return {
    isCorrectChain,
    currentChainId: chainId,
    requiredChainId,
    switchToRequiredChain,
  };
};

/**
 * Hook to format wallet address (shortened)
 */
export const useFormattedAddress = () => {
  const address = useWalletStore((state) => state.address);

  const formattedAddress = address
    ? `${address.slice(0, 6)}...${address.slice(-4)}`
    : null;

  return formattedAddress;
};
