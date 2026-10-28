import { useState, useEffect, useCallback } from 'react';
import { walletService } from '../wallet';
import type { WalletState, WalletProvider } from '../types';

/**
 * Hook for wallet connection and management
 */
export function useWallet() {
  const [state, setState] = useState<WalletState>({
    address: null,
    chainId: null,
    balance: null,
    isConnecting: false,
    isConnected: false,
    error: null,
  });

  /**
   * Connect wallet
   */
  const connect = useCallback(async (provider?: WalletProvider) => {
    setState((prev) => ({ ...prev, isConnecting: true, error: null }));

    try {
      const address = await walletService.connectWallet(provider);
      const chainId = await walletService.getChainId();
      const balance = await walletService.getBalance(address);

      setState({
        address,
        chainId,
        balance,
        isConnecting: false,
        isConnected: true,
        error: null,
      });
    } catch (error) {
      setState((prev) => ({
        ...prev,
        isConnecting: false,
        isConnected: false,
        error: (error as Error).message,
      }));
    }
  }, []);

  /**
   * Disconnect wallet
   */
  const disconnect = useCallback(async () => {
    try {
      await walletService.disconnectWallet();
      setState({
        address: null,
        chainId: null,
        balance: null,
        isConnecting: false,
        isConnected: false,
        error: null,
      });
    } catch (error) {
      setState((prev) => ({
        ...prev,
        error: (error as Error).message,
      }));
    }
  }, []);

  /**
   * Switch network
   */
  const switchNetwork = useCallback(async (network: string) => {
    setState((prev) => ({ ...prev, error: null }));

    try {
      await walletService.switchNetwork(network);
      const chainId = await walletService.getChainId();

      setState((prev) => ({
        ...prev,
        chainId,
      }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        error: (error as Error).message,
      }));
    }
  }, []);

  /**
   * Refresh balance
   */
  const refreshBalance = useCallback(async () => {
    if (!state.address) return;

    try {
      const balance = await walletService.getBalance(state.address);
      setState((prev) => ({ ...prev, balance }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        error: (error as Error).message,
      }));
    }
  }, [state.address]);

  /**
   * Sign message
   */
  const signMessage = useCallback(async (message: string): Promise<string | null> => {
    setState((prev) => ({ ...prev, error: null }));

    try {
      return await walletService.signMessage(message);
    } catch (error) {
      setState((prev) => ({
        ...prev,
        error: (error as Error).message,
      }));
      return null;
    }
  }, []);

  /**
   * Setup event listeners
   */
  useEffect(() => {
    const handleAccountsChanged = (address: string) => {
      setState((prev) => ({ ...prev, address }));
      refreshBalance();
    };

    const handleChainChanged = (chainId: number) => {
      setState((prev) => ({ ...prev, chainId }));
    };

    const handleDisconnect = () => {
      setState({
        address: null,
        chainId: null,
        balance: null,
        isConnecting: false,
        isConnected: false,
        error: null,
      });
    };

    walletService.on('accountsChanged', handleAccountsChanged);
    walletService.on('chainChanged', handleChainChanged);
    walletService.on('disconnect', handleDisconnect);

    return () => {
      walletService.off('accountsChanged', handleAccountsChanged);
      walletService.off('chainChanged', handleChainChanged);
      walletService.off('disconnect', handleDisconnect);
    };
  }, [refreshBalance]);

  /**
   * Check if wallet is already connected on mount
   */
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const isConnected = await walletService.isConnected();

        if (isConnected) {
          const address = await walletService.getAddress();
          const chainId = await walletService.getChainId();
          const balance = address ? await walletService.getBalance(address) : null;

          setState({
            address,
            chainId,
            balance,
            isConnecting: false,
            isConnected: true,
            error: null,
          });
        }
      } catch (error) {
        // Silently fail if not connected
      }
    };

    checkConnection();
  }, []);

  return {
    ...state,
    connect,
    disconnect,
    switchNetwork,
    refreshBalance,
    signMessage,
  };
}
