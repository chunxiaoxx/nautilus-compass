# Zustand Store 使用指南

## 概述

本项目使用 Zustand 进行状态管理，提供了五个核心 Store：

- **authStore** - 用户认证状态
- **taskStore** - 任务管理状态
- **agentStore** - 智能体管理状态
- **walletStore** - Web3 钱包状态
- **uiStore** - UI 界面状态

## 安装依赖

```bash
npm install zustand axios
```

## 基本使用

### 1. 认证状态 (authStore)

```tsx
import { useAuthStore } from '@/stores';

function LoginComponent() {
  const { user, isAuthenticated, login, logout, error } = useAuthStore();

  const handleLogin = async () => {
    try {
      await login('user@example.com', 'password');
      // 登录成功
    } catch (error) {
      // 处理错误
      console.error(error);
    }
  };

  return (
    <div>
      {isAuthenticated ? (
        <div>
          <p>Welcome, {user?.username}</p>
          <button onClick={logout}>Logout</button>
        </div>
      ) : (
        <button onClick={handleLogin}>Login</button>
      )}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
```

### 2. 任务状态 (taskStore)

```tsx
import { useTaskStore } from '@/stores';

function TaskList() {
  const { tasks, isLoading, fetchTasks, acceptTask } = useTaskStore();

  useEffect(() => {
    fetchTasks({ status: 'pending' }, 1, 10);
  }, []);

  const handleAccept = async (taskId: string) => {
    try {
      await acceptTask(taskId);
      // 任务接受成功
    } catch (error) {
      console.error(error);
    }
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      {tasks.map((task) => (
        <div key={task.id}>
          <h3>{task.title}</h3>
          <p>{task.description}</p>
          <button onClick={() => handleAccept(task.id)}>Accept</button>
        </div>
      ))}
    </div>
  );
}
```

### 3. 智能体状态 (agentStore)

```tsx
import { useAgentStore } from '@/stores';

function AgentDashboard() {
  const { agents, fetchAgents, startAgent, stopAgent } = useAgentStore();

  useEffect(() => {
    fetchAgents();
  }, []);

  return (
    <div>
      {agents.map((agent) => (
        <div key={agent.id}>
          <h3>{agent.name}</h3>
          <p>Status: {agent.status}</p>
          {agent.status === 'idle' && (
            <button onClick={() => startAgent(agent.id)}>Start</button>
          )}
          {agent.status === 'running' && (
            <button onClick={() => stopAgent(agent.id)}>Stop</button>
          )}
        </div>
      ))}
    </div>
  );
}
```

### 4. 钱包状态 (walletStore)

```tsx
import { useWalletStore } from '@/stores';

function WalletConnect() {
  const { address, balance, isConnected, connect, disconnect } = useWalletStore();

  return (
    <div>
      {isConnected ? (
        <div>
          <p>Address: {address}</p>
          <p>Balance: {balance} ETH</p>
          <button onClick={disconnect}>Disconnect</button>
        </div>
      ) : (
        <button onClick={connect}>Connect Wallet</button>
      )}
    </div>
  );
}
```

### 5. UI 状态 (uiStore)

```tsx
import { useUIStore } from '@/stores';

function ThemeToggle() {
  const { theme, toggleTheme, addNotification } = useUIStore();

  const showNotification = () => {
    addNotification({
      type: 'success',
      title: 'Success',
      message: 'Operation completed successfully',
      duration: 3000,
    });
  };

  return (
    <div>
      <button onClick={toggleTheme}>
        Current theme: {theme}
      </button>
      <button onClick={showNotification}>
        Show Notification
      </button>
    </div>
  );
}
```

## 高级用法

### 选择性订阅（性能优化）

```tsx
// 只订阅需要的状态，避免不必要的重渲染
const user = useAuthStore((state) => state.user);
const login = useAuthStore((state) => state.login);
```

### 在组件外使用

```tsx
import { useAuthStore } from '@/stores';

// 获取当前状态
const currentUser = useAuthStore.getState().user;

// 调用 action
useAuthStore.getState().logout();

// 订阅状态变化
const unsubscribe = useAuthStore.subscribe((state) => {
  console.log('Auth state changed:', state);
});

// 取消订阅
unsubscribe();
```

### 重置所有 Store

```tsx
import { resetAllStores } from '@/stores/middleware';

// 重置所有 store 到初始状态
resetAllStores();
```

## 持久化

以下 Store 支持持久化到 localStorage：

- **authStore** - 保存 user, token, isAuthenticated
- **walletStore** - 保存 address, chainId, isConnected
- **uiStore** - 保存 theme, sidebarOpen

持久化数据会在页面刷新后自动恢复。

## 错误处理

所有异步操作都会抛出错误，需要使用 try-catch 处理：

```tsx
try {
  await login(email, password);
} catch (error) {
  // 错误已经设置到 store.error 中
  // 可以显示错误消息或进行其他处理
}
```

## 环境变量

在 `.env` 文件中配置 API 地址：

```env
VITE_API_BASE_URL=http://localhost:3000/api
```

## TypeScript 支持

所有 Store 都提供完整的 TypeScript 类型定义，享受类型安全和自动补全。

## 调试

开发环境下，taskStore 和 agentStore 使用了 devtools 中间件，可以在 Redux DevTools 中查看状态变化。

安装 Redux DevTools 浏览器扩展：
- Chrome: https://chrome.google.com/webstore/detail/redux-devtools
- Firefox: https://addons.mozilla.org/en-US/firefox/addon/reduxdevtools/
