import { useEffect, useCallback } from 'react';
import { useAgentStore } from '@/stores';

/**
 * Hook to fetch and manage agents
 */
export const useAgents = () => {
  const { agents, isLoading, error, fetchAgents } = useAgentStore();

  useEffect(() => {
    fetchAgents();
  }, []);

  const refetch = useCallback(() => {
    fetchAgents();
  }, [fetchAgents]);

  return {
    agents,
    isLoading,
    error,
    refetch,
  };
};

/**
 * Hook to manage a single agent
 */
export const useAgent = (agentId?: string) => {
  const {
    currentAgent,
    isLoading,
    error,
    fetchAgentById,
    startAgent,
    stopAgent,
    pauseAgent,
    updateAgent,
  } = useAgentStore();

  useEffect(() => {
    if (agentId) {
      fetchAgentById(agentId);
    }
  }, [agentId]);

  const start = useCallback(async () => {
    if (agentId) {
      await startAgent(agentId);
    }
  }, [agentId, startAgent]);

  const stop = useCallback(async () => {
    if (agentId) {
      await stopAgent(agentId);
    }
  }, [agentId, stopAgent]);

  const pause = useCallback(async () => {
    if (agentId) {
      await pauseAgent(agentId);
    }
  }, [agentId, pauseAgent]);

  const update = useCallback(async (updates: any) => {
    if (agentId) {
      await updateAgent(agentId, updates);
    }
  }, [agentId, updateAgent]);

  return {
    agent: currentAgent,
    isLoading,
    error,
    start,
    stop,
    pause,
    update,
  };
};

/**
 * Hook to filter agents by status
 */
export const useAgentsByStatus = (status: 'idle' | 'running' | 'paused' | 'error') => {
  const agents = useAgentStore((state) =>
    state.agents.filter((agent) => agent.status === status)
  );

  return agents;
};

/**
 * Hook to filter agents by type
 */
export const useAgentsByType = (type: 'data_collector' | 'labeler' | 'trainer' | 'validator') => {
  const agents = useAgentStore((state) =>
    state.agents.filter((agent) => agent.type === type)
  );

  return agents;
};
