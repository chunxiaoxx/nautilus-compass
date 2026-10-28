# Zustand Store 系统

完整的状态管理系统，包含5个核心Store和配套工具。

## 📁 文件结构

```
src/stores/
├── authStore.ts              # 用户认证状态
├── taskStore.ts              # 任务管理状态
├── agentStore.ts             # 智能体管理状态
├── walletStore.ts            # Web3钱包状态
├── uiStore.ts                # UI界面状态
├── middleware.ts             # 中间件（日志、错误处理）
├── utils.ts                  # 工具函数
├── index.ts                  # 导出入口
├── StoreProvider.tsx         # Store初始化Provider
├── hooks/                    # 自定义Hooks
│   ├── useAuth.ts
│   ├── useTasks.ts
│   ├── useAgents.ts
│   ├── useWallet.ts
│   ├── useUI.ts
│   └── index.ts
├── components/               # 配套组件
│   ├── ProtectedRoute.tsx
│   ├── NotificationContainer.tsx
│   ├── LoadingOverlay.tsx
│   └── index.ts
├── examples/                 # 使用示例
│   └── AppExample.tsx
└── README.md                 # 使用文档
```

## ✨ 核心功能

### 1. authStore - 用户认证
- 登录/注册/登出
- Token管理
- 自动认证检查
- localStorage持久化

### 2. taskStore - 任务管理
- 任务列表（分页、筛选）
- 任务详情
- 接受任务
- 提交结果
- DevTools支持

### 3. agentStore - 智能体管理
- 智能体列表
- 启动/停止/暂停
- 性能监控
- DevTools支持

### 4. walletStore - Web3钱包
- MetaMask连接
- 余额查询
- 链切换
- 事件监听
- localStorage持久化

### 5. uiStore - UI状态
- 主题切换（light/dark/system）
- 侧边栏控制
- 通知系统
- 全局加载状态
- localStorage持久化

## 🎯 技术特性

- ✅ TypeScript类型安全
- ✅ 持久化支持（localStorage）
- ✅ 中间件系统（日志、错误处理）
- ✅ DevTools集成
- ✅ 完整错误处理
- ✅ 自定义Hooks
- ✅ 配套UI组件
- ✅ 不可变更新模式

## 🚀 快速开始

### 1. 安装依赖
```bash
npm install zustand axios
```

### 2. 在App中使用
```tsx
import { StoreProvider } from '@/stores/StoreProvider';
import { NotificationContainer, LoadingOverlay } from '@/stores/components';

function App() {
  return (
    <StoreProvider>
      <NotificationContainer />
      <LoadingOverlay />
      {/* Your app content */}
    </StoreProvider>
  );
}
```

### 3. 使用Store
```tsx
import { useAuthStore, useTaskStore } from '@/stores';

function MyComponent() {
  const { user, login } = useAuthStore();
  const { tasks, fetchTasks } = useTaskStore();

  // Your component logic
}
```

## 📚 详细文档

查看 `README.md` 获取完整使用指南和API文档。

## 🔧 配置

在 `.env` 文件中配置API地址：
```env
VITE_API_BASE_URL=http://localhost:3000/api
```

## 🎨 配套组件

- **ProtectedRoute** - 路由保护
- **NotificationContainer** - 通知显示
- **LoadingOverlay** - 全局加载遮罩

## 📖 示例代码

查看 `examples/AppExample.tsx` 获取完整使用示例。
