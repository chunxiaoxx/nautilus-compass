# Nautilus Website 开发指南

## 🛠️ 开发环境设置

### 前置要求

- Node.js 18+
- npm 或 yarn
- Git

### 初始化项目

```bash
# 克隆项目
cd /c/Users/chunx/Projects/nautilus-core/phase3/website

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

---

## 📁 项目结构详解

```
website/
├── public/                 # 静态资源
│   └── vite.svg           # 默认图标
├── src/
│   ├── components/        # 组件目录
│   │   ├── common/        # 通用组件
│   │   │   ├── Button.tsx
│   │   │   └── Card.tsx
│   │   ├── layout/        # 布局组件
│   │   │   ├── Layout.tsx
│   │   │   ├── Header.tsx
│   │   │   └── Footer.tsx
│   │   └── sections/      # 页面区块
│   │       ├── Hero.tsx
│   │       ├── Features.tsx
│   │       ├── Stats.tsx
│   │       └── CTA.tsx
│   ├── pages/             # 页面组件
│   │   └── Home.tsx
│   ├── styles/            # 样式文件
│   │   └── index.css
│   ├── App.tsx            # 主应用组件
│   └── main.tsx           # 应用入口
├── index.html             # HTML模板
├── package.json           # 项目配置
├── vite.config.ts         # Vite配置
├── tailwind.config.js     # Tailwind配置
├── tsconfig.json          # TypeScript配置
└── README.md              # 项目说明
```

---

## 🎨 设计系统

### 颜色方案

```typescript
// Primary Colors (靛蓝)
primary-50: '#eef2ff'
primary-500: '#6366f1'
primary-600: '#4f46e5'

// Dark Theme (深色主题)
dark-50: '#f8fafc'
dark-400: '#94a3b8'
dark-700: '#334155'
dark-800: '#1e293b'
dark-900: '#0f172a'
```

### 自定义样式类

```css
.glass              /* 玻璃态效果 */
.gradient-primary   /* 主色渐变 */
.gradient-text      /* 渐变文字 */
```

---

## 🧩 组件开发

### Button组件

```tsx
import Button from '@/components/common/Button'

// 使用示例
<Button variant="primary" size="lg">
  点击我
</Button>

// Props
variant: 'primary' | 'secondary' | 'outline'
size: 'sm' | 'md' | 'lg'
```

### Card组件

```tsx
import Card from '@/components/common/Card'

// 使用示例
<Card hover>
  <h3>标题</h3>
  <p>内容</p>
</Card>

// Props
hover: boolean  // 悬停效果
```

---

## 📄 添加新页面

### 1. 创建页面组件

```tsx
// src/pages/NewPage.tsx
export default function NewPage() {
  return (
    <div>
      <h1>新页面</h1>
    </div>
  )
}
```

### 2. 添加路由

```tsx
// src/App.tsx
import NewPage from './pages/NewPage'

<Routes>
  <Route path="/new" element={<NewPage />} />
</Routes>
```

---

## 🎭 动画效果

使用Framer Motion添加动画：

```tsx
import { motion } from 'framer-motion'

<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.5 }}
>
  内容
</motion.div>
```

---

## 🔧 常用命令

```bash
# 开发
npm run dev          # 启动开发服务器
npm run build        # 构建生产版本
npm run preview      # 预览生产版本

# 代码质量
npm run lint         # 运行ESLint
npm run format       # 格式化代码
```

---

## 📱 响应式设计

使用Tailwind的响应式前缀：

```tsx
<div className="text-base md:text-lg lg:text-xl">
  响应式文字
</div>

// 断点
sm: 640px   // 手机横屏
md: 768px   // 平板
lg: 1024px  // 桌面
xl: 1280px  // 大屏
```

---

## 🚀 部署

### Vercel部署

```bash
# 安装Vercel CLI
npm i -g vercel

# 部署
vercel --prod
```

### Netlify部署

```bash
# 安装Netlify CLI
npm i -g netlify-cli

# 部署
netlify deploy --prod --dir=dist
```

---

## 🐛 调试技巧

### React DevTools

安装Chrome扩展：React Developer Tools

### Vite调试

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    sourcemap: true  // 启用source map
  }
})
```

---

## 📝 代码规范

### TypeScript

- 使用类型注解
- 避免使用`any`
- 使用接口定义Props

### React

- 使用函数组件
- 使用Hooks管理状态
- 组件名使用PascalCase

### 样式

- 优先使用Tailwind类
- 自定义样式放在index.css
- 使用语义化类名

---

## 🔗 API集成

### 配置环境变量

```bash
# .env.local
VITE_API_URL=http://localhost:8000
```

### 使用Axios

```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL
})

// 使用
const response = await api.get('/api/tasks')
```

---

## 📚 学习资源

- [React文档](https://react.dev)
- [Vite文档](https://vitejs.dev)
- [Tailwind CSS文档](https://tailwindcss.com)
- [TypeScript文档](https://www.typescriptlang.org)
- [Framer Motion文档](https://www.framer.com/motion)

---

## 🤝 贡献指南

1. Fork项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

---

## ❓ 常见问题

### Q: 如何修改主题颜色？

A: 编辑`tailwind.config.js`中的colors配置

### Q: 如何添加新字体？

A: 在`index.html`中添加字体链接，然后在`tailwind.config.js`配置

### Q: 如何优化构建大小？

A: 使用动态导入、Tree Shaking、代码分割

---

**开发愉快！** 🚀
