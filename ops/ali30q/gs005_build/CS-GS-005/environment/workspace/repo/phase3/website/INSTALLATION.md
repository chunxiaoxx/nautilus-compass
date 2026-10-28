# Nautilus API Integration - Installation Guide

## 安装步骤

### 1. 安装依赖

```bash
cd C:/Users/chunx/Projects/nautilus-core/phase3/website
npm install
```

这将安装以下新增依赖：
- `@tanstack/react-query` - React Query 数据获取库
- `@tanstack/react-query-devtools` - React Query 开发工具

### 2. 配置环境变量

复制 `.env.example` 到 `.env`：

```bash
cp .env.example .env
```

或手动创建 `.env` 文件：

```env
# API Configuration
VITE_API_BASE_URL=http://43.160.239.61:8000
VITE_API_TIMEOUT=30000
```

### 3. 集成到应用

在 `src/main.tsx` 或 `src/App.tsx` 中添加 Provider：

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { ApiProvider } from './services/api/provider';
import { AuthProvider } from './services/api/auth-context';
import App from './App';
import './styles/index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ApiProvider>
      <AuthProvider>
        <App />
      </AuthProvider>
    </ApiProvider>
  </React.StrictMode>
);
```

### 4. 使用示例

#### 登录页面

```tsx
import React, { useState } from 'react';
import { useAuth } from './services/api/auth-context';

function LoginPage() {
  const { login, isLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      await login(email, password);
      // 登录成功，自动跳转
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
      />
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Logging in...' : 'Login'}
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}
```

#### 任务列表页面

```tsx
import React from 'react';
import { useTasks } from './services/api';

function TasksPage() {
  const { data, isLoading, error } = useTasks({
    page: 1,
    limit: 10,
    status: 'pending'
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h1>Tasks</h1>
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

#### 受保护的路由

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ProtectedRoute, PublicRoute } from './services/api/auth-context';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          }
        />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
```

### 5. 运行测试（可选）

在浏览器控制台中运行 API 测试：

```tsx
import { runAllTests } from './services/api/test';

// 运行所有测试
runAllTests();
```

### 6. 启动开发服务器

```bash
npm run dev
```

## 文件结构

```
src/services/api/
├── types.ts              # TypeScript 类型定义
├── client.ts             # Axios 客户端配置
├── auth.ts               # 认证 API
├── tasks.ts              # 任务 API
├── agents.ts             # 智能体 API
├── users.ts              # 用户 API
├── cache.ts              # 缓存策略
├── hooks.ts              # React Query Hooks
├── provider.tsx          # React Query Provider
├── auth-context.tsx      # 认证上下文
├── config.ts             # 配置文件
├── utils.ts              # 工具函数
├── test.ts               # API 测试
├── index.ts              # 统一导出
└── README.md             # 文档
```

## 常见问题

### Q: 如何修改 API 基础 URL？

A: 在 `.env` 文件中修改 `VITE_API_BASE_URL`

### Q: 如何处理认证失败？

A: 使用 `useAuth` hook 中的 `isAuthenticated` 状态，或使用 `ProtectedRoute` 组件

### Q: 如何清除缓存？

A: 使用 `apiCache.clear()` 或 `cacheInvalidation.all()`

### Q: 如何自定义请求重试？

A: 在 `config.ts` 中修改 `RETRY_CONFIG`

### Q: 如何启用/禁用 DevTools？

A: DevTools 在开发模式下自动启用，生产环境自动禁用

## 下一步

- 查看 `src/services/api/README.md` 了解详细 API 文档
- 查看 `src/services/api/provider.tsx` 了解更多使用示例
- 运行 `npm run dev` 启动开发服务器
