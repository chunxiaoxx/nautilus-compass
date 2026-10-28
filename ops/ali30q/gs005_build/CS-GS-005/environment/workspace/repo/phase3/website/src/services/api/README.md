# Nautilus API Integration

完整的 API 集成层，包含认证、任务、智能体和用户管理功能。

## 目录结构

```
src/services/api/
├── types.ts          # TypeScript 类型定义
├── client.ts         # Axios 客户端配置
├── auth.ts           # 认证 API
├── tasks.ts          # 任务 API
├── agents.ts         # 智能体 API
├── users.ts          # 用户 API
├── cache.ts          # 缓存策略
├── hooks.ts          # React Query Hooks
├── provider.tsx      # React Query Provider
└── index.ts          # 统一导出
```

## 快速开始

### 1. 安装依赖

```bash
npm install @tanstack/react-query @tanstack/react-query-devtools
```

### 2. 配置 Provider

```tsx
import { ApiProvider } from './services/api/provider';

function App() {
  return (
    <ApiProvider>
      <YourApp />
    </ApiProvider>
  );
}
```

### 3. 使用 API Hooks

```tsx
import { useLogin, useTasks, useAgents } from './services/api';

function MyComponent() {
  const login = useLogin();
  const { data: tasks } = useTasks();
  const { data: agents } = useAgents();

  // ...
}
```

## API 功能

### 认证 (auth.ts)

- `login(credentials)` - 用户登录
- `register(userData)` - 用户注册
- `logout()` - 用户登出
- `refreshToken()` - 刷新访问令牌
- `getProfile()` - 获取当前用户信息
- `verifyToken()` - 验证令牌有效性
- `requestPasswordReset(email)` - 请求密码重置
- `resetPassword(token, newPassword)` - 重置密码

### 任务 (tasks.ts)

- `getTasks(params)` - 获取任务列表（分页、筛选）
- `getTaskById(taskId)` - 获取任务详情
- `createTask(taskData)` - 创建新任务
- `updateTask(taskId, updates)` - 更新任务
- `deleteTask(taskId)` - 删除任务
- `acceptTask(taskId)` - 接受任务
- `submitResult(taskId, result)` - 提交任务结果
- `getMyTasks(params)` - 获取我的任务
- `getAvailableTasks(params)` - 获取可用任务
- `cancelTask(taskId)` - 取消任务
- `getTaskResults(taskId)` - 获取任务结果

### 智能体 (agents.ts)

- `getAgents(params)` - 获取智能体列表
- `getAgentById(agentId)` - 获取智能体详情
- `createAgent(agentData)` - 创建新智能体
- `updateAgent(agentId, updates)` - 更新智能体
- `deleteAgent(agentId)` - 删除智能体
- `getMyAgents(params)` - 获取我的智能体
- `startAgent(agentId)` - 启动智能体
- `stopAgent(agentId)` - 停止智能体
- `getAgentMetrics(agentId)` - 获取智能体性能指标
- `assignTask(agentId, taskId)` - 分配任务给智能体
- `getAgentTasks(agentId)` - 获取智能体任务

### 用户 (users.ts)

- `getProfile()` - 获取用户资料
- `updateProfile(updates)` - 更新用户资料
- `getStats()` - 获取用户统计
- `getHistory(params)` - 获取用户历史
- `uploadAvatar(file)` - 上传头像
- `deleteAvatar()` - 删除头像
- `getUserById(userId)` - 获取用户信息（公开）
- `getUserStats(userId)` - 获取用户统计（公开）
- `changePassword(currentPassword, newPassword)` - 修改密码
- `deleteAccount(password)` - 删除账户
- `getLeaderboard(params)` - 获取排行榜

## React Query Hooks

### 认证 Hooks

```tsx
const login = useLogin();
const register = useRegister();
const logout = useLogout();
const { data: profile } = useProfile();
```

### 任务 Hooks

```tsx
const { data: tasks } = useTasks({ page: 1, limit: 10 });
const { data: task } = useTask(taskId);
const { data: myTasks } = useMyTasks();
const createTask = useCreateTask();
const updateTask = useUpdateTask();
const deleteTask = useDeleteTask();
const acceptTask = useAcceptTask();
const submitResult = useSubmitTaskResult();
```

### 智能体 Hooks

```tsx
const { data: agents } = useAgents();
const { data: agent } = useAgent(agentId);
const { data: myAgents } = useMyAgents();
const createAgent = useCreateAgent();
const updateAgent = useUpdateAgent();
const deleteAgent = useDeleteAgent();
const startAgent = useStartAgent();
const stopAgent = useStopAgent();
```

### 用户 Hooks

```tsx
const { data: profile } = useUserProfile();
const updateProfile = useUpdateProfile();
const { data: stats } = useUserStats();
const { data: history } = useUserHistory();
const uploadAvatar = useUploadAvatar();
const { data: leaderboard } = useLeaderboard();
```

## 使用示例

### 登录表单

```tsx
function LoginForm() {
  const login = useLogin();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login.mutateAsync({
        email: 'user@example.com',
        password: 'password123'
      });
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <button type="submit" disabled={login.isPending}>
        {login.isPending ? 'Logging in...' : 'Login'}
      </button>
      {login.isError && <p>Error: {login.error.message}</p>}
    </form>
  );
}
```

### 任务列表

```tsx
function TaskList() {
  const { data, isLoading, error } = useTasks({
    page: 1,
    limit: 10,
    status: 'pending'
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {data?.items.map(task => (
        <div key={task.id}>
          <h3>{task.title}</h3>
          <p>{task.description}</p>
          <span>Reward: {task.reward}</span>
        </div>
      ))}
    </div>
  );
}
```

### 创建任务

```tsx
function CreateTaskForm() {
  const createTask = useCreateTask();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const task = await createTask.mutateAsync({
        title: 'New Task',
        description: 'Task description',
        type: 'data_collection',
        reward: 100
      });
      console.log('Task created:', task);
    } catch (error) {
      console.error('Failed to create task:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <button type="submit" disabled={createTask.isPending}>
        {createTask.isPending ? 'Creating...' : 'Create Task'}
      </button>
    </form>
  );
}
```

### 智能体控制

```tsx
function AgentControl({ agentId }: { agentId: string }) {
  const { data: agent } = useAgent(agentId);
  const startAgent = useStartAgent();
  const stopAgent = useStopAgent();

  return (
    <div>
      <h3>{agent?.name}</h3>
      <p>Status: {agent?.status}</p>
      {agent?.status === 'inactive' ? (
        <button onClick={() => startAgent.mutate(agentId)}>Start</button>
      ) : (
        <button onClick={() => stopAgent.mutate(agentId)}>Stop</button>
      )}
    </div>
  );
}
```

## 核心特性

### 1. 自动令牌刷新

客户端自动处理 401 错误并刷新访问令牌：

```typescript
// 在 client.ts 中自动处理
if (error.response?.status === 401) {
  // 自动刷新令牌并重试请求
}
```

### 2. 请求重试

失败的请求会自动重试（最多 3 次）：

```typescript
const response = await retryRequest(() =>
  apiClient.get('/api/tasks')
);
```

### 3. 缓存策略

使用内存缓存减少不必要的 API 调用：

```typescript
import { cachedRequest, apiCache } from './services/api/cache';

// 使用缓存
const data = await cachedRequest('tasks:list', () =>
  apiClient.get('/api/tasks')
);

// 清除缓存
apiCache.clear();
```

### 4. 错误处理

统一的错误处理机制：

```typescript
try {
  await tasksApi.createTask(taskData);
} catch (error) {
  if (error instanceof ApiError) {
    console.error(`Error ${error.status}: ${error.message}`);
  }
}
```

### 5. TypeScript 支持

完整的类型定义确保类型安全：

```typescript
import type { Task, CreateTaskRequest } from './services/api';

const taskData: CreateTaskRequest = {
  title: 'New Task',
  description: 'Description',
  type: 'data_collection',
  reward: 100
};
```

## 配置

### API 基础 URL

在 `client.ts` 中修改：

```typescript
const API_BASE_URL = 'http://43.160.239.61:8000';
```

### 超时设置

```typescript
const API_TIMEOUT = 30000; // 30 秒
```

### 重试配置

```typescript
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 秒
```

### React Query 配置

在 `hooks.ts` 中修改：

```typescript
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 分钟
      gcTime: 10 * 60 * 1000, // 10 分钟
      retry: 3,
      refetchOnWindowFocus: false,
    },
  },
});
```

## 最佳实践

1. **使用 React Query Hooks** - 优先使用 hooks 而不是直接调用 API
2. **错误处理** - 始终处理错误状态
3. **加载状态** - 显示加载指示器提升用户体验
4. **乐观更新** - 对于用户操作使用乐观更新
5. **缓存失效** - 在数据变更后正确失效缓存

## 开发工具

在开发模式下，React Query DevTools 会自动启用：

```tsx
<ApiProvider>
  <YourApp />
  {/* DevTools 自动包含在开发模式 */}
</ApiProvider>
```

## 注意事项

- 所有 API 请求都需要认证（除了 login 和 register）
- Token 存储在 localStorage 中
- 401 错误会自动触发令牌刷新
- 刷新失败会重定向到登录页面
