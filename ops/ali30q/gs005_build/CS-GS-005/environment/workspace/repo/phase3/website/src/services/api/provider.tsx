import React from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { queryClient } from './hooks';
import {
  useLogin,
  useRegister,
  useLogout,
  useProfile,
  useTasks,
  useTask,
  useMyTasks,
  useAvailableTasks,
  useCreateTask,
  useUpdateTask,
  useDeleteTask,
  useAcceptTask,
  useSubmitTaskResult,
  useAgents,
  useAgent,
  useMyAgents,
  useCreateAgent,
  useUpdateAgent,
  useDeleteAgent,
  useStartAgent,
  useStopAgent,
  useUserProfile,
  useUpdateProfile,
  useUserStats,
  useUserHistory,
  useUploadAvatar,
  useLeaderboard,
} from './hooks';

/**
 * API Provider Component
 *
 * Wrap your app with this component to enable React Query
 *
 * @example
 * ```tsx
 * import { ApiProvider } from './services/api/provider';
 *
 * function App() {
 *   return (
 *     <ApiProvider>
 *       <YourApp />
 *     </ApiProvider>
 *   );
 * }
 * ```
 */
export const ApiProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {process.env.NODE_ENV === 'development' && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  );
};

/**
 * Usage Examples
 *
 * @example Authentication
 * ```tsx
 * function LoginForm() {
 *   const login = useLogin();
 *
 *   const handleSubmit = async (e: React.FormEvent) => {
 *     e.preventDefault();
 *     try {
 *       const result = await login.mutateAsync({
 *         email: 'user@example.com',
 *         password: 'password123'
 *       });
 *       console.log('Logged in:', result);
 *     } catch (error) {
 *       console.error('Login failed:', error);
 *     }
 *   };
 *
 *   return (
 *     <form onSubmit={handleSubmit}>
 *       <button type="submit" disabled={login.isPending}>
 *         {login.isPending ? 'Logging in...' : 'Login'}
 *       </button>
 *       {login.isError && <p>Error: {login.error.message}</p>}
 *     </form>
 *   );
 * }
 * ```
 *
 * @example Fetching Tasks
 * ```tsx
 * function TaskList() {
 *   const { data, isLoading, error } = useTasks({
 *     page: 1,
 *     limit: 10,
 *     status: 'pending'
 *   });
 *
 *   if (isLoading) return <div>Loading...</div>;
 *   if (error) return <div>Error: {error.message}</div>;
 *
 *   return (
 *     <div>
 *       {data?.items.map(task => (
 *         <div key={task.id}>{task.title}</div>
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 *
 * @example Creating a Task
 * ```tsx
 * function CreateTaskForm() {
 *   const createTask = useCreateTask();
 *
 *   const handleSubmit = async (e: React.FormEvent) => {
 *     e.preventDefault();
 *     try {
 *       const task = await createTask.mutateAsync({
 *         title: 'New Task',
 *         description: 'Task description',
 *         type: 'data_collection',
 *         reward: 100
 *       });
 *       console.log('Task created:', task);
 *     } catch (error) {
 *       console.error('Failed to create task:', error);
 *     }
 *   };
 *
 *   return (
 *     <form onSubmit={handleSubmit}>
 *       <button type="submit" disabled={createTask.isPending}>
 *         {createTask.isPending ? 'Creating...' : 'Create Task'}
 *       </button>
 *     </form>
 *   );
 * }
 * ```
 *
 * @example Managing Agents
 * ```tsx
 * function AgentControl({ agentId }: { agentId: string }) {
 *   const { data: agent } = useAgent(agentId);
 *   const startAgent = useStartAgent();
 *   const stopAgent = useStopAgent();
 *
 *   const handleStart = () => {
 *     startAgent.mutate(agentId);
 *   };
 *
 *   const handleStop = () => {
 *     stopAgent.mutate(agentId);
 *   };
 *
 *   return (
 *     <div>
 *       <h3>{agent?.name}</h3>
 *       <p>Status: {agent?.status}</p>
 *       {agent?.status === 'inactive' ? (
 *         <button onClick={handleStart}>Start</button>
 *       ) : (
 *         <button onClick={handleStop}>Stop</button>
 *       )}
 *     </div>
 *   );
 * }
 * ```
 *
 * @example User Profile
 * ```tsx
 * function UserProfile() {
 *   const { data: profile } = useUserProfile();
 *   const { data: stats } = useUserStats();
 *   const updateProfile = useUpdateProfile();
 *
 *   const handleUpdate = async () => {
 *     try {
 *       await updateProfile.mutateAsync({
 *         username: 'newusername'
 *       });
 *     } catch (error) {
 *       console.error('Update failed:', error);
 *     }
 *   };
 *
 *   return (
 *     <div>
 *       <h2>{profile?.username}</h2>
 *       <p>Tasks Completed: {stats?.tasksCompleted}</p>
 *       <p>Success Rate: {stats?.successRate}%</p>
 *       <button onClick={handleUpdate}>Update Profile</button>
 *     </div>
 *   );
 * }
 * ```
 *
 * @example Optimistic Updates
 * ```tsx
 * function TaskItem({ taskId }: { taskId: string }) {
 *   const queryClient = useQueryClient();
 *   const acceptTask = useAcceptTask();
 *
 *   const handleAccept = () => {
 *     acceptTask.mutate(taskId, {
 *       onMutate: async () => {
 *         // Cancel outgoing refetches
 *         await queryClient.cancelQueries({ queryKey: ['tasks', 'detail', taskId] });
 *
 *         // Snapshot previous value
 *         const previousTask = queryClient.getQueryData(['tasks', 'detail', taskId]);
 *
 *         // Optimistically update
 *         queryClient.setQueryData(['tasks', 'detail', taskId], (old: any) => ({
 *           ...old,
 *           status: 'in_progress'
 *         }));
 *
 *         return { previousTask };
 *       },
 *       onError: (err, variables, context) => {
 *         // Rollback on error
 *         if (context?.previousTask) {
 *           queryClient.setQueryData(['tasks', 'detail', taskId], context.previousTask);
 *         }
 *       },
 *     });
 *   };
 *
 *   return <button onClick={handleAccept}>Accept Task</button>;
 * }
 * ```
 */

// Re-export all hooks for convenience
export {
  // Auth hooks
  useLogin,
  useRegister,
  useLogout,
  useProfile,

  // Task hooks
  useTasks,
  useTask,
  useMyTasks,
  useAvailableTasks,
  useCreateTask,
  useUpdateTask,
  useDeleteTask,
  useAcceptTask,
  useSubmitTaskResult,

  // Agent hooks
  useAgents,
  useAgent,
  useMyAgents,
  useCreateAgent,
  useUpdateAgent,
  useDeleteAgent,
  useStartAgent,
  useStopAgent,

  // User hooks
  useUserProfile,
  useUpdateProfile,
  useUserStats,
  useUserHistory,
  useUploadAvatar,
  useLeaderboard,
};
