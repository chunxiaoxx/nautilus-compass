import { useState, useCallback } from 'react';
import { ethers } from 'ethers';
import { web3Provider } from '../provider';
import type { TransactionState } from '../types';

/**
 * Hook for managing transaction state and execution
 */
export function useTransaction() {
  const [state, setState] = useState<TransactionState>({
    hash: null,
    status: 'idle',
    error: null,
  });

  /**
   * Execute a transaction
   */
  const executeTransaction = useCallback(
    async (
      transactionFn: () => Promise<ethers.ContractTransactionResponse>
    ): Promise<ethers.TransactionReceipt | null> => {
      setState({
        hash: null,
        status: 'pending',
        error: null,
      });

      try {
        // Execute transaction
        const tx = await transactionFn();

        setState((prev) => ({
          ...prev,
          hash: tx.hash,
        }));

        // Wait for confirmation
        const receipt = await tx.wait();

        if (receipt && receipt.status === 1) {
          setState({
            hash: receipt.hash,
            status: 'success',
            error: null,
          });
          return receipt;
        } else {
          setState({
            hash: receipt?.hash || null,
            status: 'error',
            error: 'Transaction failed',
          });
          return null;
        }
      } catch (error: any) {
        const errorMessage = parseTransactionError(error);
        setState({
          hash: null,
          status: 'error',
          error: errorMessage,
        });
        throw new Error(errorMessage);
      }
    },
    []
  );

  /**
   * Wait for transaction confirmation
   */
  const waitForTransaction = useCallback(
    async (txHash: string, confirmations: number = 1): Promise<ethers.TransactionReceipt | null> => {
      setState({
        hash: txHash,
        status: 'pending',
        error: null,
      });

      try {
        const receipt = await web3Provider.waitForTransaction(txHash, confirmations);

        if (receipt && receipt.status === 1) {
          setState({
            hash: receipt.hash,
            status: 'success',
            error: null,
          });
          return receipt;
        } else {
          setState({
            hash: receipt?.hash || null,
            status: 'error',
            error: 'Transaction failed',
          });
          return null;
        }
      } catch (error) {
        const errorMessage = (error as Error).message;
        setState({
          hash: txHash,
          status: 'error',
          error: errorMessage,
        });
        return null;
      }
    },
    []
  );

  /**
   * Reset transaction state
   */
  const reset = useCallback(() => {
    setState({
      hash: null,
      status: 'idle',
      error: null,
    });
  }, []);

  /**
   * Get transaction receipt
   */
  const getReceipt = useCallback(async (txHash: string) => {
    try {
      const provider = web3Provider.getProvider();
      return await provider.getTransactionReceipt(txHash);
    } catch (error) {
      throw new Error(`Failed to get receipt: ${(error as Error).message}`);
    }
  }, []);

  /**
   * Get transaction details
   */
  const getTransaction = useCallback(async (txHash: string) => {
    try {
      const provider = web3Provider.getProvider();
      return await provider.getTransaction(txHash);
    } catch (error) {
      throw new Error(`Failed to get transaction: ${(error as Error).message}`);
    }
  }, []);

  return {
    ...state,
    executeTransaction,
    waitForTransaction,
    reset,
    getReceipt,
    getTransaction,
  };
}

/**
 * Parse transaction error messages
 */
function parseTransactionError(error: any): string {
  // User rejected transaction
  if (error.code === 4001 || error.code === 'ACTION_REJECTED') {
    return 'Transaction rejected by user';
  }

  // Insufficient funds
  if (error.code === 'INSUFFICIENT_FUNDS') {
    return 'Insufficient funds for transaction';
  }

  // Gas estimation failed
  if (error.code === 'UNPREDICTABLE_GAS_LIMIT') {
    return 'Cannot estimate gas; transaction may fail or require manual gas limit';
  }

  // Network error
  if (error.code === 'NETWORK_ERROR') {
    return 'Network error occurred';
  }

  // Nonce too low
  if (error.code === 'NONCE_EXPIRED') {
    return 'Transaction nonce expired';
  }

  // Replacement transaction underpriced
  if (error.code === 'REPLACEMENT_UNDERPRICED') {
    return 'Replacement transaction underpriced';
  }

  // Transaction reverted
  if (error.code === 'CALL_EXCEPTION') {
    return error.reason || 'Transaction reverted';
  }

  // Generic error
  return error.message || 'Transaction failed';
}

/**
 * Hook for tracking multiple transactions
 */
export function useTransactionHistory() {
  const [transactions, setTransactions] = useState<
    Array<{
      hash: string;
      status: 'pending' | 'success' | 'error';
      timestamp: number;
      description?: string;
    }>
  >([]);

  /**
   * Add transaction to history
   */
  const addTransaction = useCallback(
    (hash: string, description?: string) => {
      setTransactions((prev) => [
        ...prev,
        {
          hash,
          status: 'pending',
          timestamp: Date.now(),
          description,
        },
      ]);
    },
    []
  );

  /**
   * Update transaction status
   */
  const updateTransaction = useCallback(
    (hash: string, status: 'pending' | 'success' | 'error') => {
      setTransactions((prev) =>
        prev.map((tx) => (tx.hash === hash ? { ...tx, status } : tx))
      );
    },
    []
  );

  /**
   * Remove transaction from history
   */
  const removeTransaction = useCallback((hash: string) => {
    setTransactions((prev) => prev.filter((tx) => tx.hash !== hash));
  }, []);

  /**
   * Clear all transactions
   */
  const clearTransactions = useCallback(() => {
    setTransactions([]);
  }, []);

  /**
   * Get pending transactions
   */
  const getPendingTransactions = useCallback(() => {
    return transactions.filter((tx) => tx.status === 'pending');
  }, [transactions]);

  return {
    transactions,
    addTransaction,
    updateTransaction,
    removeTransaction,
    clearTransactions,
    getPendingTransactions,
  };
}
