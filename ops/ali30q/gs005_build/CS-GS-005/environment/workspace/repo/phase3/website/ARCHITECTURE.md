# Nautilus 多智能体任务协作平台 - 网站架构文档

## 文档版本
- **版本**: 1.0.0
- **日期**: 2026-02-28
- **作者**: Architecture Team
- **状态**: Draft

---

## 目录

1. [项目概述](#1-项目概述)
2. [网站地图](#2-网站地图)
3. [用户流程设计](#3-用户流程设计)
4. [技术架构](#4-技术架构)
5. [组件设计系统](#5-组件设计系统)
6. [状态管理方案](#6-状态管理方案)
7. [API集成方案](#7-api集成方案)
8. [设计系统](#8-设计系统)
9. [用户体验设计](#9-用户体验设计)
10. [部署策略](#10-部署策略)

---

## 1. 项目概述

### 1.1 项目定位

**Nautilus** 是一个基于区块链的多智能体任务协作平台，旨在连接任务发布者和AI智能体，通过去中心化的方式实现任务分配、协作执行和奖励分配。

### 1.2 核心价值主张

- **去中心化协作**: 基于区块链的透明任务分配机制
- **智能体生态**: 多样化的AI智能体能力市场
- **公平激励**: 基于贡献的代币奖励系统
- **高效执行**: 自动化的任务分解和协作流程

### 1.3 目标用户

1. **任务发布者**
   - 企业用户：需要AI能力完成业务任务
   - 个人用户：寻求AI协助解决问题
   - 开发者：测试和验证AI能力

2. **智能体提供者**
   - AI开发者：部署和运营智能体
   - 算法研究者：验证AI模型效果
   - 服务商：提供专业AI服务

### 1.4 技术栈

**前端**
- React 18.3+ (UI框架)
- TypeScript 5.0+ (类型安全)
- Vite 5.0+ (构建工具)
- Tailwind CSS 3.4+ (样式框架)
- React Router 6.0+ (路由管理)
- Zustand 4.0+ (状态管理)
- React Query 5.0+ (数据获取)
- Ethers.js 6.0+ (区块链集成)
- Framer Motion 11.0+ (动画)

**后端API**
- FastAPI (已部署)
- 地址: http://43.160.239.61:8000

**区块链**
- Ethereum Sepolia (测试网)
- Web3.js/Ethers.js (钱包集成)

---

## 2. 网站地图

### 2.1 页面层级结构

```
Nautilus Platform
│
├── 公开页面 (Public)
│   ├── 首页 (/)
│   ├── 任务市场 (/marketplace)
│   ├── 任务详情 (/tasks/:id)
│   ├── 关于我们 (/about)
│   └── 文档中心 (/docs)
│
├── 认证页面 (Auth)
│   ├── 登录 (/login)
│   ├── 注册 (/register)
│   └── 钱包连接 (/connect-wallet)
│
└── 用户中心 (Dashboard) - 需要认证
    ├── 概览 (/dashboard)
    ├── 我的任务 (/dashboard/tasks)
    ├── 创建任务 (/dashboard/tasks/create)
    ├── 我的智能体 (/dashboard/agents)
    ├── 钱包 (/dashboard/wallet)
    ├── 个人设置 (/dashboard/settings)
    └── 消息中心 (/dashboard/messages)
```

### 2.2 导航结构

**主导航 (Header)**
```
Logo | 任务市场 | 智能体 | 文档 | 关于 | [登录] [注册] / [用户头像]
```

**用户中心导航 (Sidebar)**
```
- 概览
- 我的任务
- 创建任务
- 我的智能体
- 钱包
- 消息中心
- 设置
```

---

## 3. 用户流程设计

### 3.1 任务发布者流程

1. 访问首页 → 注册/登录
2. 点击"创建任务"
3. 填写任务信息（标题、描述、要求）
4. 设置奖励金额
5. 预览任务
6. 连接钱包并支付押金
7. 发布任务
8. 等待智能体接受
9. 查看任务进度
10. 审核结果
11. 确认完成并释放奖励

### 3.2 智能体提供者流程

1. 访问平台 → 注册/登录
2. 浏览任务市场
3. 使用筛选器查找合适任务
4. 查看任务详情
5. 评估能力匹配
6. 接受任务
7. 执行任务
8. 提交结果
9. 等待审核
10. 获得奖励

---

## 4. 技术架构

### 4.1 整体架构

```
┌─────────────────────────────────────────┐
│           用户界面层 (UI Layer)          │
│  首页 | 任务市场 | 用户中心 | 管理后台   │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│          组件层 (Component Layer)        │
│  布局组件 | 业务组件 | 通用组件 | UI组件 │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│        状态管理层 (State Layer)          │
│  用户状态 | 任务状态 | 钱包状态 | UI状态 │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│          服务层 (Service Layer)          │
│  API服务 | Web3服务 | 存储服务 | 工具   │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│           数据层 (Data Layer)            │
│     后端API | 区块链 | IPFS              │
└─────────────────────────────────────────┘
```

### 4.2 目录结构

```
nautilus-website/
├── public/
│   ├── favicon.ico
│   └── assets/
│
├── src/
│   ├── main.tsx                 # 应用入口
│   ├── App.tsx                  # 根组件
│   │
│   ├── components/              # 组件
│   │   ├── layout/             # 布局组件
│   │   │   ├── Header.tsx
│   │   │   ├── Footer.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── DashboardLayout.tsx
│   │   │
│   │   ├── common/             # 通用组件
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Card.tsx
│   │   │   └── Loading.tsx
│   │   │
│   │   ├── task/               # 任务组件
│   │   │   ├── TaskCard.tsx
│   │   │   ├── TaskList.tsx
│   │   │   ├── TaskFilter.tsx
│   │   │   └── TaskForm.tsx
│   │   │
│   │   └── wallet/             # 钱包组件
│   │       ├── WalletConnect.tsx
│   │       └── WalletBalance.tsx
│   │
│   ├── pages/                   # 页面组件
│   │   ├── Home.tsx
│   │   ├── Marketplace.tsx
│   │   ├── TaskDetail.tsx
│   │   ├── Login.tsx
│   │   ├── Register.tsx
│   │   │
│   │   └── dashboard/
│   │       ├── Overview.tsx
│   │       ├── MyTasks.tsx
│   │       ├── CreateTask.tsx
│   │       ├── MyAgents.tsx
│   │       ├── Wallet.tsx
│   │       └── Settings.tsx
│   │
│   ├── hooks/                   # 自定义Hooks
│   │   ├── useAuth.ts
│   │   ├── useTasks.ts
│   │   ├── useWallet.ts
│   │   └── useWeb3.ts
│   │
│   ├── stores/                  # Zustand状态
│   │   ├── authStore.ts
│   │   ├── taskStore.ts
│   │   ├── walletStore.ts
│   │   └── uiStore.ts
│   │
│   ├── services/                # 服务层
│   │   ├── api/
│   │   │   ├── client.ts
│   │   │   ├── auth.ts
│   │   │   ├── tasks.ts
│   │   │   └── agents.ts
│   │   │
│   │   └── web3/
│   │       ├── provider.ts
│   │       ├── contracts.ts
│   │       └── wallet.ts
│   │
│   ├── types/                   # 类型定义
│   │   ├── task.ts
│   │   ├── agent.ts
│   │   ├── user.ts
│   │   └── wallet.ts
│   │
│   ├── utils/                   # 工具函数
│   │   ├── format.ts
│   │   ├── validation.ts
│   │   └── constants.ts
│   │
│   ├── config/                  # 配置
│   │   ├── env.ts
│   │   ├── routes.ts
│   │   └── web3.ts
│   │
│   └── router/                  # 路由
│       └── index.tsx
│
├── .env.example
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── README.md
```

---

## 5. 组件设计系统

### 5.1 组件层级

```
App
├── RootLayout
│   ├── Header
│   │   ├── Logo
│   │   ├── Navigation
│   │   └── UserMenu
│   ├── Main (Outlet)
│   └── Footer
│
├── DashboardLayout
│   ├── DashboardHeader
│   ├── Sidebar
│   ├── Main (Outlet)
│   └── Notifications
│
└── Pages
    ├── Home
    │   ├── HeroSection
    │   ├── FeaturesSection
    │   ├── HowItWorksSection
    │   └── CTASection
    │
    ├── Marketplace
    │   ├── SearchBar
    │   ├── FilterPanel
    │   └── TaskList
    │
    └── Dashboard
        ├── Overview
        ├── MyTasks
        └── CreateTask
```

### 5.2 核心组件规范

#### Button组件

```typescript
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'outline' | 'ghost';
  size: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
}
```

#### Card组件

```typescript
interface CardProps {
  title?: string;
  subtitle?: string;
  footer?: React.ReactNode;
  hoverable?: boolean;
  children: React.ReactNode;
}
```

#### TaskCard组件

```typescript
interface TaskCardProps {
  task: Task;
  onView: (id: string) => void;
  onAccept?: (id: string) => void;
}
```

---

## 6. 状态管理方案

### 6.1 Zustand Store设计

#### 认证状态 (authStore)

```typescript
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}
```

#### 任务状态 (taskStore)

```typescript
interface TaskState {
  tasks: Task[];
  currentTask: Task | null;
  filters: TaskFilters;
  isLoading: boolean;

  fetchTasks: (filters?: TaskFilters) => Promise<void>;
  fetchTaskById: (id: string) => Promise<void>;
  createTask: (data: CreateTaskData) => Promise<void>;
  acceptTask: (id: string) => Promise<void>;
  submitResult: (id: string, result: TaskResult) => Promise<void>;
}
```

#### 钱包状态 (walletStore)

```typescript
interface WalletState {
  address: string | null;
  balance: string;
  chainId: number | null;
  isConnected: boolean;

  connect: () => Promise<void>;
  disconnect: () => void;
  switchChain: (chainId: number) => Promise<void>;
}
```

---

## 7. API集成方案

### 7.1 API客户端配置

```typescript
// src/services/api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 处理未授权
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### 7.2 React Query集成

```typescript
// src/hooks/useTasks.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { taskAPI } from '@/services/api/tasks';

export const useTasks = (filters?: TaskFilters) => {
  return useQuery({
    queryKey: ['tasks', filters],
    queryFn: () => taskAPI.getTasks(filters),
  });
};

export const useCreateTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: taskAPI.createTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
};
```

---

## 8. 设计系统

### 8.1 颜色系统

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
        },
        secondary: {
          50: '#faf5ff',
          500: '#a855f7',
          600: '#9333ea',
        },
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444',
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          500: '#6b7280',
          900: '#111827',
        },
      },
    },
  },
};
```

### 8.2 字体系统

```css
/* src/assets/styles/global.css */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'Fira Code', monospace;
}

body {
  font-family: var(--font-sans);
}
```

### 8.3 间距系统

```javascript
// Tailwind默认间距系统
spacing: {
  0: '0px',
  1: '0.25rem',  // 4px
  2: '0.5rem',   // 8px
  3: '0.75rem',  // 12px
  4: '1rem',     // 16px
  6: '1.5rem',   // 24px
  8: '2rem',     // 32px
  12: '3rem',    // 48px
  16: '4rem',    // 64px
}
```

---

## 9. 用户体验设计

### 9.1 响应式设计

```javascript
// Tailwind断点
screens: {
  'sm': '640px',
  'md': '768px',
  'lg': '1024px',
  'xl': '1280px',
  '2xl': '1536px',
}
```

### 9.2 加载状态

- 骨架屏（Skeleton）
- 加载动画（Spinner）
- 进度条（Progress Bar）
- 占位符（Placeholder）

### 9.3 错误处理

- Toast通知
- 错误边界（Error Boundary）
- 404页面
- 500页面
- 表单验证错误

### 9.4 无障碍设计

- 语义化HTML
- ARIA标签
- 键盘导航
- 屏幕阅读器支持
- 颜色对比度

---

## 10. 部署策略

### 10.1 构建优化

```javascript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['framer-motion'],
          'web3-vendor': ['ethers'],
        },
      },
    },
  },
});
```

### 10.2 环境配置

```bash
# .env.development
VITE_API_URL=http://localhost:8000
VITE_CHAIN_ID=11155111
VITE_RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY

# .env.production
VITE_API_URL=http://43.160.239.61:8000
VITE_CHAIN_ID=11155111
VITE_RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY
```

### 10.3 部署流程

1. 构建生产版本
```bash
npm run build
```

2. 部署到服务器
```bash
scp -r dist/* user@server:/var/www/nautilus
```

3. 配置Nginx
```nginx
server {
    listen 80;
    server_name nautilus.example.com;

    root /var/www/nautilus;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

---

## 附录

### A. 技术决策记录

| 决策 | 选择 | 原因 |
|------|------|------|
| 状态管理 | Zustand | 轻量、简单、TypeScript友好 |
| 数据获取 | React Query | 缓存、重试、自动刷新 |
| 样式方案 | Tailwind CSS | 快速开发、一致性 |
| 区块链库 | Ethers.js | 文档完善、社区活跃 |
| 动画库 | Framer Motion | 强大、易用 |

### B. 性能指标

- 首屏加载时间: < 2s
- 交互响应时间: < 100ms
- Lighthouse评分: > 90
- Bundle大小: < 500KB (gzip)

### C. 浏览器支持

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

---

**文档状态**: Draft
**最后更新**: 2026-02-28
**下一步**: 开始UI/UX设计和组件开发
