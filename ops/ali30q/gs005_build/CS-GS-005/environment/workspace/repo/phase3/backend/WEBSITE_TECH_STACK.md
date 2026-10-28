# Nautilus 网站技术栈选择

**版本**: v1.0
**创建时间**: 2026-02-26
**项目**: Nautilus多智能体任务协作平台

---

## 1. 技术栈概述

### 1.1 选择原则
- **现代化**: 使用最新稳定的技术
- **性能优先**: 快速加载和流畅交互
- **开发效率**: 提高开发速度和维护性
- **SEO友好**: 支持服务端渲染
- **可扩展性**: 易于扩展和维护
- **社区支持**: 活跃的社区和丰富的生态

### 1.2 技术选型对比

| 维度 | Next.js | Nuxt.js | Gatsby |
|------|---------|---------|--------|
| 框架 | React | Vue | React |
| SSR | ✅ 优秀 | ✅ 优秀 | ❌ SSG only |
| 性能 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| SEO | ✅ 优秀 | ✅ 优秀 | ✅ 优秀 |
| 学习曲线 | 中等 | 较低 | 中等 |
| 生态系统 | 非常丰富 | 丰富 | 丰富 |
| 企业采用 | 广泛 | 中等 | 中等 |

**推荐**: Next.js 14+ (App Router)

---

## 2. 前端技术栈

### 2.1 核心框架

#### Next.js 14+ (App Router)
**选择理由**:
- ✅ React 18+ 支持，最新特性
- ✅ 服务端渲染 (SSR) 和静态生成 (SSG)
- ✅ 优秀的性能优化（自动代码分割、图片优化）
- ✅ 内置路由系统
- ✅ API Routes支持
- ✅ 强大的开发体验
- ✅ Vercel部署优化
- ✅ 大型企业广泛采用

**版本**: Next.js 14.1+

**配置示例**:
```javascript
// next.config.js
module.exports = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: ['nautilus.io'],
    formats: ['image/avif', 'image/webp'],
  },
  i18n: {
    locales: ['zh', 'en'],
    defaultLocale: 'zh',
  },
  experimental: {
    optimizeCss: true,
  },
}
```

---

### 2.2 UI框架和组件库

#### 主选方案: Tailwind CSS + shadcn/ui

**Tailwind CSS 3.4+**
- ✅ 实用优先的CSS框架
- ✅ 高度可定制
- ✅ 优秀的性能（PurgeCSS）
- ✅ 响应式设计简单
- ✅ 暗黑模式支持

**shadcn/ui**
- ✅ 基于Radix UI的高质量组件
- ✅ 完全可定制
- ✅ 无需安装包，复制代码即用
- ✅ TypeScript支持
- ✅ 可访问性优秀

**备选方案**:
- Material-UI (MUI): 适合需要Material Design风格
- Ant Design: 适合企业级应用
- Chakra UI: 适合快速开发

**推荐配置**:
```javascript
// tailwind.config.js
module.exports = {
  darkMode: 'class',
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          500: '#0ea5e9',
          900: '#0c4a6e',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms'),
  ],
}
```

---

### 2.3 动画库

#### Framer Motion
**选择理由**:
- ✅ 强大的动画能力
- ✅ 声明式API
- ✅ 手势支持
- ✅ 布局动画
- ✅ SVG动画
- ✅ 优秀的性能

**版本**: framer-motion 11+

**使用示例**:
```typescript
import { motion } from 'framer-motion'

export function Hero() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <h1>Nautilus</h1>
    </motion.div>
  )
}
```

**备选方案**:
- GSAP: 更强大但学习曲线陡峭
- React Spring: 基于物理的动画
- Anime.js: 轻量级动画库

---

### 2.4 状态管理

#### Zustand
**选择理由**:
- ✅ 简单易用
- ✅ 无需Provider
- ✅ TypeScript支持优秀
- ✅ 性能优秀
- ✅ 体积小（~1KB）

**版本**: zustand 4+

**使用示例**:
```typescript
import { create } from 'zustand'

interface AppState {
  theme: 'light' | 'dark'
  setTheme: (theme: 'light' | 'dark') => void
}

export const useAppStore = create<AppState>((set) => ({
  theme: 'light',
  setTheme: (theme) => set({ theme }),
}))
```

**备选方案**:
- Redux Toolkit: 适合大型复杂应用
- Jotai: 原子化状态管理
- React Context: 简单场景

---

### 2.5 数据获取

#### TanStack Query (React Query)
**选择理由**:
- ✅ 强大的缓存机制
- ✅ 自动重新获取
- ✅ 乐观更新
- ✅ 分页和无限滚动
- ✅ TypeScript支持

**版本**: @tanstack/react-query 5+

**使用示例**:
```typescript
import { useQuery } from '@tanstack/react-query'

export function useAgents() {
  return useQuery({
    queryKey: ['agents'],
    queryFn: async () => {
      const res = await fetch('/api/agents')
      return res.json()
    },
  })
}
```

---

### 2.6 表单处理

#### React Hook Form
**选择理由**:
- ✅ 性能优秀（最小重渲染）
- ✅ 易于集成验证库
- ✅ TypeScript支持
- ✅ 体积小

**版本**: react-hook-form 7+

**配合 Zod 进行验证**:
```typescript
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
})

export function LoginForm() {
  const { register, handleSubmit } = useForm({
    resolver: zodResolver(schema),
  })

  return <form onSubmit={handleSubmit(onSubmit)}>...</form>
}
```

---

### 2.7 图表和可视化

#### Recharts + D3.js
**Recharts**: 用于常规图表
- ✅ React组件化
- ✅ 响应式
- ✅ 易于使用

**D3.js**: 用于复杂可视化
- ✅ 强大灵活
- ✅ 自定义能力强
- ✅ 社区资源丰富

**使用示例**:
```typescript
import { LineChart, Line, XAxis, YAxis } from 'recharts'

export function TaskChart({ data }) {
  return (
    <LineChart width={600} height={300} data={data}>
      <XAxis dataKey="date" />
      <YAxis />
      <Line type="monotone" dataKey="tasks" stroke="#0ea5e9" />
    </LineChart>
  )
}
```

---

### 2.8 代码高亮

#### Shiki
**选择理由**:
- ✅ VS Code同款高亮
- ✅ 支持多种主题
- ✅ 性能优秀
- ✅ 服务端渲染友好

**版本**: shiki 1+

**备选**: Prism.js, Highlight.js

---

### 2.9 Markdown渲染

#### MDX
**选择理由**:
- ✅ Markdown + JSX
- ✅ 可嵌入React组件
- ✅ Next.js原生支持
- ✅ 适合技术文档

**配置**:
```javascript
// next.config.js
const withMDX = require('@next/mdx')()

module.exports = withMDX({
  pageExtensions: ['js', 'jsx', 'ts', 'tsx', 'md', 'mdx'],
})
```

---

### 2.10 图标库

#### Lucide React
**选择理由**:
- ✅ 现代简洁
- ✅ 一致的设计
- ✅ Tree-shakable
- ✅ TypeScript支持

**使用示例**:
```typescript
import { Rocket, Code, Zap } from 'lucide-react'

export function Features() {
  return (
    <div>
      <Rocket className="w-6 h-6" />
      <Code className="w-6 h-6" />
      <Zap className="w-6 h-6" />
    </div>
  )
}
```

---

## 3. 后端技术栈

### 3.1 API层

#### Next.js API Routes
**用途**: 轻量级API端点
- 联系表单提交
- Newsletter订阅
- 简单数据查询

**示例**:
```typescript
// app/api/subscribe/route.ts
export async function POST(request: Request) {
  const { email } = await request.json()
  // 处理订阅逻辑
  return Response.json({ success: true })
}
```

#### 主后端API
**使用现有的FastAPI后端**:
- 用户认证
- 任务管理
- 智能体管理
- 区块链交互

---

### 3.2 内容管理

#### 方案A: 基于文件的CMS (推荐)
**Contentlayer**
- ✅ 类型安全的内容
- ✅ 基于文件系统
- ✅ Git版本控制
- ✅ 开发者友好

**目录结构**:
```
content/
├── blog/
│   ├── post-1.mdx
│   └── post-2.mdx
├── docs/
│   ├── getting-started.mdx
│   └── api-reference.mdx
└── pages/
    └── about.mdx
```

#### 方案B: Headless CMS
**Strapi / Sanity / Contentful**
- 适合非技术团队管理内容
- 提供可视化编辑器
- 需要额外服务器

**推荐**: 初期使用Contentlayer，后期根据需要迁移到Headless CMS

---

### 3.3 搜索功能

#### Algolia
**选择理由**:
- ✅ 快速搜索
- ✅ 即时结果
- ✅ 拼写纠正
- ✅ 高亮显示
- ✅ 易于集成

**配置示例**:
```typescript
import algoliasearch from 'algoliasearch/lite'
import { InstantSearch, SearchBox, Hits } from 'react-instantsearch'

const searchClient = algoliasearch('APP_ID', 'API_KEY')

export function Search() {
  return (
    <InstantSearch searchClient={searchClient} indexName="docs">
      <SearchBox />
      <Hits />
    </InstantSearch>
  )
}
```

**备选方案**:
- Meilisearch: 开源自托管
- Typesense: 开源替代方案
- 自建搜索: 使用Fuse.js

---

## 4. 部署和基础设施

### 4.1 托管平台

#### Vercel (推荐)
**选择理由**:
- ✅ Next.js原生支持
- ✅ 全球CDN
- ✅ 自动HTTPS
- ✅ 预览部署
- ✅ 边缘函数
- ✅ 分析和监控
- ✅ 免费额度慷慨

**配置**:
```json
// vercel.json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "regions": ["hkg1", "sfo1"],
  "env": {
    "NEXT_PUBLIC_API_URL": "@api-url"
  }
}
```

**备选方案**:
- Netlify: 类似Vercel
- Cloudflare Pages: 性能优秀
- AWS Amplify: AWS生态
- 自托管: Docker + Nginx

---

### 4.2 CDN和静态资源

#### Cloudflare CDN
**用途**:
- 图片加速
- 静态资源缓存
- DDoS防护
- 全球加速

**配置**:
- 启用Brotli压缩
- 设置缓存规则
- 配置Page Rules
- 启用HTTP/3

---

### 4.3 图片优化

#### Cloudinary / Vercel Image Optimization
**功能**:
- 自动格式转换（WebP, AVIF）
- 响应式图片
- 懒加载
- 压缩优化

**使用Next.js Image组件**:
```typescript
import Image from 'next/image'

export function Hero() {
  return (
    <Image
      src="/hero.jpg"
      alt="Nautilus"
      width={1200}
      height={600}
      priority
      placeholder="blur"
    />
  )
}
```

---

### 4.4 域名和DNS

#### Cloudflare DNS
**配置**:
```
nautilus.io          A      76.76.21.21
www.nautilus.io      CNAME  nautilus.io
api.nautilus.io      CNAME  api-server.com
docs.nautilus.io     CNAME  nautilus.io
```

---

## 5. 开发工具

### 5.1 包管理器

#### pnpm (推荐)
**选择理由**:
- ✅ 快速安装
- ✅ 节省磁盘空间
- ✅ 严格的依赖管理
- ✅ Monorepo支持

**备选**: npm, yarn

---

### 5.2 代码质量

#### ESLint + Prettier
**配置**:
```json
// .eslintrc.json
{
  "extends": [
    "next/core-web-vitals",
    "plugin:@typescript-eslint/recommended",
    "prettier"
  ],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/no-explicit-any": "warn"
  }
}
```

#### Husky + lint-staged
**Git Hooks**:
```json
// package.json
{
  "lint-staged": {
    "*.{js,jsx,ts,tsx}": ["eslint --fix", "prettier --write"],
    "*.{json,md,mdx}": ["prettier --write"]
  }
}
```

---

### 5.3 类型检查

#### TypeScript 5+
**配置**:
```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "moduleResolution": "bundler",
    "jsx": "preserve",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

---

### 5.4 测试

#### Vitest + Testing Library
**单元测试**:
```typescript
import { render, screen } from '@testing-library/react'
import { expect, test } from 'vitest'
import { Hero } from './Hero'

test('renders hero section', () => {
  render(<Hero />)
  expect(screen.getByText('Nautilus')).toBeInTheDocument()
})
```

#### Playwright
**E2E测试**:
```typescript
import { test, expect } from '@playwright/test'

test('homepage loads', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('h1')).toContainText('Nautilus')
})
```

---

### 5.5 性能监控

#### Vercel Analytics
- Web Vitals监控
- 实时性能数据
- 用户体验指标

#### Sentry
- 错误追踪
- 性能监控
- 用户反馈

**配置**:
```typescript
// sentry.client.config.ts
import * as Sentry from '@sentry/nextjs'

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  tracesSampleRate: 0.1,
  environment: process.env.NODE_ENV,
})
```

---

## 6. 分析和营销

### 6.1 网站分析

#### Google Analytics 4
**配置**:
```typescript
// app/layout.tsx
import { GoogleAnalytics } from '@next/third-parties/google'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>{children}</body>
      <GoogleAnalytics gaId="G-XXXXXXXXXX" />
    </html>
  )
}
```

#### Plausible Analytics (备选)
- 隐私友好
- 轻量级
- 简单易用

---

### 6.2 SEO工具

#### next-seo
**配置**:
```typescript
import { NextSeo } from 'next-seo'

export default function Page() {
  return (
    <>
      <NextSeo
        title="Nautilus - 多智能体协作平台"
        description="区块链驱动的去中心化任务市场"
        openGraph={{
          title: 'Nautilus',
          description: '多智能体协作平台',
          images: [{ url: '/og-image.jpg' }],
        }}
      />
      {/* 页面内容 */}
    </>
  )
}
```

---

## 7. 国际化

### 7.1 i18n方案

#### next-intl
**配置**:
```typescript
// middleware.ts
import createMiddleware from 'next-intl/middleware'

export default createMiddleware({
  locales: ['zh', 'en'],
  defaultLocale: 'zh',
})
```

**使用**:
```typescript
import { useTranslations } from 'next-intl'

export function Hero() {
  const t = useTranslations('home')
  return <h1>{t('title')}</h1>
}
```

---

## 8. 完整技术栈总结

### 8.1 前端核心
```
- Framework: Next.js 14+ (App Router)
- Language: TypeScript 5+
- UI: Tailwind CSS + shadcn/ui
- Animation: Framer Motion
- State: Zustand
- Data Fetching: TanStack Query
- Forms: React Hook Form + Zod
```

### 8.2 开发工具
```
- Package Manager: pnpm
- Linting: ESLint + Prettier
- Testing: Vitest + Playwright
- Git Hooks: Husky + lint-staged
```

### 8.3 内容和数据
```
- Content: Contentlayer (MDX)
- Search: Algolia
- Analytics: Google Analytics 4
- Monitoring: Sentry + Vercel Analytics
```

### 8.4 部署和基础设施
```
- Hosting: Vercel
- CDN: Cloudflare
- DNS: Cloudflare DNS
- Images: Vercel Image Optimization
```

---

## 9. 项目结构

```
nautilus-website/
├── app/                      # Next.js App Router
│   ├── (marketing)/         # 营销页面组
│   │   ├── page.tsx         # 首页
│   │   ├── product/         # 产品页
│   │   ├── about/           # 关于页
│   │   └── layout.tsx
│   ├── developers/          # 开发者页面
│   ├── docs/                # 文档页面
│   ├── blog/                # 博客
│   ├── api/                 # API Routes
│   └── layout.tsx           # 根布局
├── components/              # React组件
│   ├── ui/                  # shadcn/ui组件
│   ├── layout/              # 布局组件
│   ├── marketing/           # 营销组件
│   └── docs/                # 文档组件
├── content/                 # MDX内容
│   ├── blog/
│   ├── docs/
│   └── pages/
├── lib/                     # 工具函数
│   ├── api.ts
│   ├── utils.ts
│   └── constants.ts
├── public/                  # 静态资源
│   ├── images/
│   ├── fonts/
│   └── icons/
├── styles/                  # 全局样式
│   └── globals.css
├── types/                   # TypeScript类型
├── messages/                # i18n翻译文件
│   ├── zh.json
│   └── en.json
├── .env.local              # 环境变量
├── next.config.js          # Next.js配置
├── tailwind.config.js      # Tailwind配置
├── tsconfig.json           # TypeScript配置
└── package.json
```

---

## 10. 开发流程

### 10.1 本地开发
```bash
# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev

# 类型检查
pnpm type-check

# 代码检查
pnpm lint

# 运行测试
pnpm test

# 构建生产版本
pnpm build

# 预览生产版本
pnpm start
```

### 10.2 部署流程
```
1. 推送代码到GitHub
2. Vercel自动检测并构建
3. 生成预览URL
4. 审核通过后合并到main
5. 自动部署到生产环境
```

---

## 11. 预算估算

### 11.1 开发成本
- Next.js: 免费开源
- UI组件: 免费开源
- 开发工具: 免费开源

### 11.2 运营成本（月度）
- Vercel Pro: $20/月
- Cloudflare Pro: $20/月
- Algolia: $0-$99/月（根据使用量）
- Sentry: $0-$26/月
- 域名: $10-20/年

**总计**: 约 $60-165/月

---

## 12. 时间估算

### 12.1 开发阶段
- 项目搭建和配置: 1周
- 首页开发: 1-2周
- 产品页面: 1周
- 开发者页面: 1周
- 文档系统: 2周
- 博客系统: 1周
- 测试和优化: 1周

**总计**: 8-10周

---

## 13. 风险和挑战

### 13.1 技术风险
- Next.js版本更新可能带来breaking changes
- 第三方服务依赖（Algolia, Vercel）

### 13.2 缓解措施
- 锁定主要依赖版本
- 准备备选方案
- 定期备份数据
- 监控服务状态

---

## 14. 下一步行动

1. ✅ 完成技术栈选择
2. ⏳ 创建项目脚手架
3. ⏳ 设计UI/UX
4. ⏳ 开发核心组件
5. ⏳ 集成内容管理
6. ⏳ 部署测试环境

---

**文档状态**: 已完成
**审核状态**: 待审核
**最后更新**: 2026-02-26
