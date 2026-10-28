import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import axios from 'axios';

export interface Agent {
  id: string;
  name: string;
  type: 'data_collector' | 'labeler' | 'trainer' | 'validator';
  status: 'idle' | 'running' | 'paused' | 'error';
  capabilities: string[];
  performance: {
  tasksCompleted: number;
    successRate: number;
    averageTime: number;
  };
  config: Record<string, any>;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

interface AgentState {
  agents: Agent[];
  currentAgent: Agent | null;
  isLoading: boolean;
  error: string | null;
}

interface AgentActions {
  fetchAgents: () => Promise<void>;
  fetchAgentById: (id: string) => Promise<void>;
  createAgent: (agentData: Partial<Agent>) => Promise<Agent>;
  updateAgent: (id: string, updates: Partial<Agent>) => Promise<void>;
  deleteAgent: (id: string) => Promise<void>;
  startAgent: (id: string) => Promise<void>;
  stopAgent: (id: string) => Promise<void>;
  pauseAgent: (id: string) => Promise<void>;
  setCurrentAgent: (agent: Agent | null) => void;
  clearError: () => void;
}

type AgentStore = AgentState & AgentActions;

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api';

export const useAgentStore = create<AgentStore>()(
  devtools(
    (set) => ({
      // Initial state
      agents: [],
      currentAgent: null,
      isLoading: false,
      error: null,

      // Actions
      fetchAgents: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await axios.get(`${API_BASE_URL}/agents`);
          const agents = response.data.data;

          set({
            agents,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || 'Failed to fetch agents';
          set({
            agents: [],
            isLoading: false,
            error: errorMessage,
          });
          throw new Error(errorMessage);
        }
      },

      fetchAgentById: async (id: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await axios.get(`${API_BASE_URL}/agents/${id}`);
          const agent = response.data.data;

          set({
            currentAgent: agent,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || 'Failed to fetch agent';
          set({
            currentAgent: null,
            isLoading: false,
            error: errorMessage,
          });
          throw new Error(errorMessage);
        }
      },

      createAgent: async (agentData: Partial<Agent>) => {
        set({ isLoading: true, error: null });
        try {
          const response = await axios.post(`${API_BASE_URL}/agents`, agentData);
          const newAgent = response.data.data;

          set((state) => ({
            agents: [newAgent, ...state.agents],
            isLoading: false,
            error: null,
          }));

          return newAgent;
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || 'Failed to create agent';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw new Error(errorMessage);
        }
      },

      updateAgent: async (id: string, updates: Partial<Agent>) => {
        set({ isLoading: true, error: null });
        try {
          const response = await axios.put(`${API_BASE_URL}/agents/${id}`, updates);
          const updatedAgent = response.data.data;

          set((state) => ({
            agents: state.agents.map((agent) =>
              agent.id === id ? updatedAgent : agent
            ),
            currentAgent: state.currentAgent?.id === id ? updatedAgent : state.currentAgent,
            isLoading: false,
            error: null,
          }));
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || 'Failed to update agent';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw new Error(errorMessage);
        }
      },

      deleteAgent: async (id: string) => {
        set({ isLoading: true, error: null });
        try {
          await axios.delete(`${API_BASE_URL}/agents/${id}`);

          set((state) => ({
            agents: state.agents.filter((agent) => agent.id !== id),
            currentAgent: state.currentAgent?.id === id ? null : state.currentAgent,
            isLoading: false,
            error: null,
          }));
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || 'Failed to delete agent';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw new Error(errorMessage);
        }
      },

      startAgent: async (id: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await axios.post(`${API_BASE_URL}/agents/${id}/start`);
          const updatedAgent = response.data.data;

          set((state) => ({
            agents: state.agents.map((agent) =>
              agent.id === id ? updatedAgent : agent
            ),
            currentAgent: state.currentAgent?.id === id ? updatedAgent : state.currentAgent,
            isLoading: false,
            error: null,
          }));
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || 'Failed to start agent';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw new Error(errorMessage);
        }
      },

      stopAgent: async (id: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await axios.post(`${API_BASE_URL}/agents/${id}/stop`);
          const updatedAgent = response.data.data;

          set((state) => ({
            agents: state.agents.map((agent) =>
              agent.id === id ? updatedAgent : agent
            ),
            currentAgent: state.currentAgent?.id === id ? updatedAgent : state.currentAgent,
            isLoading: false,
            error: null,
          }));
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || 'Failed to stop agent';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw new Error(errorMessage);
        }
      },

      pauseAgent: async (id: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await axios.post(`${API_BASE_URL}/agents/${id}/pause`);
          const updatedAgent = response.data.data;

          set((state) => ({
            agents: state.agents.map((agent) =>
              agent.id === id ? updatedAgent : agent
            ),
            currentAgent: state.currentAgent?.id === id ? updatedAgent : state.currentAgent,
            isLoading: false,
            error: null,
          }));
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || 'Failed to pause agent';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw new Error(errorMessage);
        }
      },

      setCurrentAgent: (agent: Agent | null) => {
        set({ currentAgent: agent });
      },

      clearError: () => {
        set({ error: null });
      },
    }),
    { name: 'AgentStore' }
  )
);
