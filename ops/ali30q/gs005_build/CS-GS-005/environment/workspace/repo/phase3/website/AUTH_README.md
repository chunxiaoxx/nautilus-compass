# Nautilus Authentication System

完整的用户认证系统，支持邮箱登录和 Web3 钱包登录。

## 功能特性

- 邮箱/密码登录和注册
- Web3 钱包（MetaMask）登录和注册
- JWT Token 管理
- 自动登录（记住我）
- 路由保护
- 表单验证（Zod）
- 错误处理

## 文件结构

```
src/
├── types/
│   └── auth.ts                 # 认证相关类型定义
├── utils/
│   ├── api.ts                  # API 客户端和错误处理
│   ├── token.ts                # JWT Token 工具函数
│   └── validation.ts           # 表单验证 Schema
├── context/
│   └── AuthContext.tsx         # 认证上下文和 Provider
├── hooks/
│   └── useAuth.ts              # 认证相关 Hooks
├── components/
│   └── auth/
│       └── ProtectedRoute.tsx  # 路由保护组件
└── pages/
    ├── Login.tsx               # 登录页面
    ├── Register.tsx            # 注册页面
    └── Dashboard.tsx           # 用户控制台（示例）
```

## 使用方法

### 1. 环境变量配置

创建 `.env` 文件：

```env
VITE_API_BASE_URL=http://localhost:3000/api
```

### 2. 在应用中使用

已在 `App.tsx` 中集成 `AuthProvider`：

```tsx
import { AuthProvider } from './context/AuthContext'

function App() {
  return (
    <AuthProvider>
      {/* 路由和其他组件 */}
    </AuthProvider>
  )
}
```

### 3. 保护路由

```tsx
import ProtectedRoute from './components/auth/ProtectedRoute'

<Route
  path="/dashboard"
  element={
    <ProtectedRoute>
      <Dashboard />
    </ProtectedRoute>
  }
/>
```

### 4. 使用认证 Hooks

```tsx
import { useAuthCheck, useLogin, useLogout } from './hooks/useAuth'

function MyComponent() {
  const { user, isAuthenticated } = useAuthCheck()
  const { login, isLoading, error } = useLogin()
  const { logout } = useLogout()

  // 使用认证功能
}
```

## API 接口要求

后端需要提供以下接口：

### 1. 邮箱登录
```
POST /api/auth/login
Body: { email: string, password: string }
Response: { success: boolean, data: { user: User, token: string }, error?: string }
```

### 2. 邮箱注册
```
POST /api/auth/register
Body: { email: string, password: string }
Response: { success: boolean, data: { user: User, token: string }, error?: string }
```

### 3. 钱包登录
```
POST /api/auth/wallet-login
Body: { walletAddress: string, signature: string }
Response: { success: boolean, data: { user: User, token: string }, error?: string }
```

### 4. 获取当前用户
```
GET /api/auth/me
Headers: { Authorization: Bearer <token> }
Response: { success: boolean, data: { user: User }, error?: string }
```

## Token 管理

- 使用 `rememberMe` 时，Token 存储在 `localStorage`
- 不使用时，Token 存储在 `sessionStorage`
- Token 自动添加到所有 API 请求的 Authorization Header
- Token 过期或无效时自动重定向到登录页

## 表单验证规则

### 登录表单
- 邮箱：必填，有效邮箱格式
- 密码：必填，至少 8 个字符

### 注册表单
- 邮箱：必填，有效邮箱格式
- 密码：必填，至少 8 个字符，包含大小写字母和数字
- 确认密码：必填，必须与密码一致
- 用户协议：必须同意

### 钱包登录
- 钱包地址：必填，有效的以太坊地址格式（0x + 40 位十六进制）
- 签名：必填

## 安全特性

1. **JWT Token 验证**：自动检查 Token 有效期
2. **请求拦截**：自动添加认证 Token
3. **响应拦截**：401 错误自动重定向到登录页
4. **密码强度**：要求大小写字母和数字组合
5. **XSS 防护**：使用 React 的自动转义
6. **CSRF 防护**：需要后端配合实现

## 依赖包

```json
{
  "react-hook-form": "^7.x",
  "zod": "^3.x",
  "@hookform/resolvers": "^3.x",
  "jwt-decode": "^4.x",
  "axios": "^1.x"
}
```

## 下一步

1. 实现后端 API 接口
2. 添加忘记密码功能
3. 添加邮箱验证
4. 添加双因素认证（2FA）
5. 添加社交登录（Google, GitHub 等）
6. 添加用户资料编辑页面
