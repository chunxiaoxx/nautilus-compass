import { useState, useCallback } from 'react';
import { contractService } from '../contracts';
import type { Task, RewardHistory } from '../contracts';

/**
 * Hook for interacting with smart contracts
 */
export function useContract() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Create a new task
   */
  const createTask = useCallback(
    async (title: string, description: string, reward: string) => {
      setIsLoading(true);
      setError(null);

      try {
        const tx = await contractService.createTask(title, description, reward);
        setIsLoading(false);
      return tx;
      } catch (err) {
        const errorMessage = (err as Error).message;
     setError(errorMessage);
        setIsLoading(false);
        throw new Error(errorMessage);
      }
    },
    []
  );

  /**
   * Submit task completion
   */
  const submitTask = useCallback(async (taskId: number, submissionUrl: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const tx = await contractService.submitTask(taskId, submissionUrl);
      setIsLoading(false);
      return tx;
    } catch (err) {
      const errorMessage = (err as Error).message;
      setError(errorMessage);
      setIsLoading(false);
      throw new Error(errorMessage);
    }
  }, []);

  /**
   * Approve task submission
   */
  const approveTask = useCallback(async (taskId: number, worker: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const tx = await contractService.approveTask(taskId, worker);
      setIsLoading(false);
      return tx;
    } catch (err) {
      const errorMessage = (err as Error).message;
      setError(errorMessage);
      setIsLoading(false);
      throw new Error(errorMessage);
    }
  }, []);

  /**
   * Reject task submission
   */
  const rejectTask = useCallback(async (taskId: number, worker: string, reason: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const tx = await contractService.rejectTask(taskId, worker, reason);
      setIsLoading(false);
      return tx;
    } catch (err) {
      const errorMessage = (err as Error).message;
      setError(errorMessage);
      setIsLoading(false);
      throw new Error(errorMessage);
    }
  }, []);

  /**
   * Cancel task
   */
  const cancelTask = useCallback(async (taskId: number) => {
    setIsLoading(true);
    setError(null);

    try {
      const tx = await contractService.cancelTask(taskId);
      setIsLoading(false);
      return tx;
    } catch (err) {
      const errorMessage = (err as Error).message;
      setError(errorMessage);
    setIsLoading(false);
      throw new Error(errorMessage);
    }
  }, []);

  /**
   * Get task details
   */
  const getTask = useCallback(async (taskId: number): Promise<Task | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const task = await contractService.getTask(taskId);
      setIsLoading(false);
      return task;
    } catch (err) {
      const errorMessage = (err as Error).message;
      setError(errorMessage);
      setIsLoading(false);
      return null;
    }
  }, []);

  /**
   * Get tasks by creator
   */
  const getTasksByCreator = useCallback(async (creator: string): Promise<bigint[]> => {
    setIsLoading(true);
    setError(null);

    try {
      const taskIds = await contractService.getTasksByCreator(creator);
      setIsLoading(false);
      return taskIds;
    } catch (err) {
      const errorMessage = (err as Error).message;
      setError(errorMessage);
      setIsLoading(false);
      return [];
    }
  }, []);

  /**
   * Get tasks by worker
   */
  const getTasksByWorker = useCallback(async (worker: string): Promise<bigint[]> => {
    setIsLoading(true);
    setError(null);

    try {
      const taskIds = await contractService.getTasksByWorker(worker);
      setIsLoading(false);
      return taskIds;
    } catch (err) {
      const errorMessage = (err as Error).message;
      setError(errorMessage);
      setIsLoading(false);
      return [];
    }
  }, []);

  /**
   * Get active tasks
   */
  const getActiveTasks = useCallback(async (): Promise<bigint[]> => {
    setIsLoading(true);
    setError(null);

    try {
      const taskIds = await contractService.getActiveTasks();
    setIsLoading(false);
      return taskIds;
    } catch (err) {
      const errorMessage = (err as Error).message;
      setError(errorMessage);
      setIsLoading(false);
      return [];
    }
  }, []);

  /**
   * Get total tasks count
   */
  const getTotalTasks = useCallback(async (): Promise<bigint> => {
    setIsLoading(true);
    setError(null);

    try {
      const total = await contractService.getTotalTasks();
      setIsLoading(false);
      return total;
    } catch (err) {
      const errorMessage = (err as Error).message;
      setError(errorMessage);
      setIsLoading(false);
      return 0n;
    }
  }, []);

  /**
   * Claim reward
   */
  const claimReward = useCallback(async (taskId: number) => {
    setIsLoading(true);
    setError(null);

    try {
      const tx = await contractService.claimReward(taskId);
      setIsLoading(false);
      return tx;
    } catch (err) {
      const errorMessage = (err as Error).message;
      setError(errorMessage);
      setIsLoading(false);
      throw new Error(errorMessage);
    }
  }, []);

  /**
   * Get reward balance
   */
  const getRewardBalance = useCallback(async (user: string): Promise<string> => {
    setIsLoading(true);
    setError(null);

    try {
      const balance = await contractService.getRewardBalance(user);
      setIsLoading(false);
      return balance;
    } catch (err) {
      const errorMessage = (err as Error).message;
      setError(errorMessage);
      setIsLoading(false);
      return '0';
    }
  }, []);

  /**
   * Withdraw rewards
   */
  const withdrawRewards = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const tx = await contractService.withdrawRewards();
      setIsLoading(false);
      return tx;
    } catch (err) {
      const errorMessage = (err as Error).message;
      setError(errorMessage);
      setIsLoading(false);
   throw new Error(errorMessage);
    }
  }, []);

  /**
   * Deposit rewards
   */
  const depositRewards = useCallback(async (amount: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const tx = await contractService.depositRewards(amount);
      setIsLoading(false);
      return tx;
    } catch (err) {
      const errorMessage = (err as Error).message;
    setError(errorMessage);
      setIsLoading(false);
      throw new Error(errorMessage);
    }
  }, []);

  /**
   * Get total rewards paid
   */
  const getTotalRewardsPaid = useCallback(async (): Promise<string> => {
    setIsLoading(true);
    setError(null);

    try {
      const total = await contractService.getTotalRewardsPaid();
      setIsLoading(false);
      return total;
    } catch (err) {
      const errorMessage = (err as Error).message;
      setError(errorMessage);
      setIsLoading(false);
      return '0';
    }
  }, []);

  /**
   * Get user reward history
   */
  const getUserRewardHistory = useCallback(
    async (user: string): Promise<RewardHistory[]> => {
      setIsLoading(true);
      setError(null);

      try {
        const history = await contractService.getUserRewardHistory(user);
        setIsLoading(false);
        return history;
      } catch (err) {
        const errorMessage = (err as Error).message;
        setError(errorMessage);
        setIsLoading(false);
        return [];
      }
    },
    []
  );

  /**
   * Get pending rewards
   */
  const getPendingRewards = useCallback(async (user: string): Promise<string> => {
    setIsLoading(true);
    setError(null);

    try {
      const pending = await contractService.getPendingRewards(user);
      setIsLoading(false);
      return pending;
    } catch (err) {
      const errorMessage = (err as Error).message;
      setError(errorMessage);
      setIsLoading(false);
      return '0';
    }
  }, []);

  /**
   * Estimate gas for creating task
   */
  const estimateCreateTaskGas = useCallback(
    async (title: string, description: string, reward: string): Promise<bigint> => {
      setError(null);

      try {
        return await contractService.estimateCreateTaskGas(title, description, reward);
      } catch (err) {
        const errorMessage = (err as Error).message;
        setError(errorMessage);
        return 0n;
      }
    },
    []
  );

  /**
   * Estimate gas for submitting task
   */
  const estimateSubmitTaskGas = useCallback(
    async (taskId: number, submissionUrl: string): Promise<bigint> => {
      setError(null);

      try {
        return await contractService.estimateSubmitTaskGas(taskId, submissionUrl);
      } catch (err) {
        const errorMessage = (err as Error).message;
        setError(errorMessage);
        return 0n;
      }
    },
    []
  );

  /**
   * Clear error
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    isLoading,
    error,
    clearError,
    // Task methods
    createTask,
    submitTask,
    approveTask,
    rejectTask,
    cancelTask,
    getTask,
    getTasksByCreator,
    getTasksByWorker,
    getActiveTasks,
    getTotalTasks,
    // Reward methods
    claimReward,
    getRewardBalance,
    withdrawRewards,
    depositRewards,
    getTotalRewardsPaid,
    getUserRewardHistory,
    getPendingRewards,
    // Gas estimation
    estimateCreateTaskGas,
    estimateSubmitTaskGas,
  };
}
