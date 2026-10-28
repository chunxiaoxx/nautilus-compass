# Nautilus 网站建设快速启动指南

**版本**: v1.0
**创建时间**: 2026-02-26
**适用对象**: 项目启动团队

---

## 🚀 5分钟快速了解

### 项目概况

**项目名称**: Nautilus官方网站
**项目类型**: 产品官网 + 技术文档 + 开发者平台
**开发周期**: 8-10周
**团队规模**: 5人
**预算**: $90,000（开发）+ $1,916/年（运营）

### 核心目标

✅ 展示Nautilus产品价值和技术优势
✅ 吸引开发者和企业用户
✅ 提供完整的技术文档和API参考
✅ 建立品牌认知和技术社区
✅ 实现月访问量10,000+（12个月）

---

## 📋 第一周行动清单

### Day 1: 团队组建和环境准备

#### 上午：团队确认
- [ ] 确认前端开发 × 2人
- [ ] 确认UI/UX设计师 × 1人
- [ ] 确认内容编辑 × 1人
- [ ] 确认项目经理 × 1人
- [ ] 签订合同和保密协议
- [ ] 设置团队沟通渠道（Slack/飞书）

#### 下午：账号和服务
- [ ] 注册域名 nautilus.io
- [ ] 开通Vercel Pro账号
- [ ] 开通Cloudflare Pro账号
- [ ] 创建GitHub组织和仓库
- [ ] 申请Google Analytics账号
- [ ] 申请Algolia账号（搜索）

**预算**: 域名 $20 + Vercel $20 + Cloudflare $20 = $60

---

### Day 2: 项目初始化

#### 上午：创建项目
```bash
# 1. 创建Next.js项目
npx create-next-app@latest nautilus-website \
  --typescript \
  --tailwind \
  --app \
  --src-dir \
  --import-alias "@/*"

cd nautilus-website

# 2. 安装核心依赖
pnpm add framer-motion zustand @tanstack/react-query
pnpm add next-intl next-seo
pnpm add lucide-react

# 3. 安装开发依赖
pnpm add -D @types/node prettier eslint-config-prettier
pnpm add -D vitest @testing-library/react @playwright/test

# 4. 初始化shadcn/ui
npx shadcn-ui@latest init
```

#### 下午：配置项目
- [ ] 配置TypeScript (tsconfig.json)
- [ ] 配置Tailwind CSS (tailwind.config.js)
- [ ] 配置ESLint和Prettier
- [ ] 设置Git hooks (Husky)
- [ ] 创建环境变量文件 (.env.local)
- [ ] 推送到GitHub

**交付物**: 可运行的项目脚手架

---

### Day 3: 设计系统搭建

#### 上午：设计资源
- [ ] 创建Figma项目
- [ ] 导入色彩系统
- [ ] 设置字体（Inter, PingFang SC）
- [ ] 创建基础组件库
- [ ] 设计首页原型

#### 下午：代码实现
```bash
# 安装shadcn/ui组件
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add input
npx shadcn-ui@latest add navigation-menu
```

- [ ] 创建色彩变量 (globals.css)
- [ ] 配置字体文件
- [ ] 实现基础组件
- [ ] 创建Storybook（可选）

**交付物**: 设计系统和基础组件

---

### Day 4: 布局和导航

#### 全天任务
- [ ] 创建根布局 (app/layout.tsx)
- [ ] 实现Header组件
- [ ] 实现Footer组件
- [ ] 实现移动端导航
- [ ] 配置路由结构
- [ ] 测试响应式布局

**代码示例**:
```typescript
// app/layout.tsx
import { Inter } from 'next/font/google'
import Header from '@/components/layout/header'
import Footer from '@/components/layout/footer'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh">
      <body className={inter.className}>
        <Header />
        <main>{children}</main>
        <Footer />
      </body>
    </html>
  )
}
```

**交付物**: 完整的布局系统

---

### Day 5: 首页Hero Section

#### 全天任务
- [ ] 设计Hero Section
- [ ] 实现主标题和副标题
- [ ] 添加CTA按钮
- [ ] 实现背景动画
- [ ] 添加滚动提示
- [ ] 优化移动端显示

**代码示例**:
```typescript
// components/marketing/hero.tsx
'use client'

import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { ArrowRight, FileText, Play } from 'lucide-react'

export function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* 背景动画 */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-slate-50" />

      {/* 内容 */}
      <div className="relative z-10 container mx-auto px-4 text-center">
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-5xl md:text-7xl font-bold text-slate-900 mb-6"
        >
          Nautilus
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="text-xl md:text-2xl text-slate-600 mb-8 max-w-3xl mx-auto"
        >
          区块链驱动的多智能体协作平台
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="flex flex-col sm:flex-row gap-4 justify-center"
        >
          <Button size="lg" className="gap-2">
            开始使用 <ArrowRight className="w-4 h-4" />
          </Button>
          <Button size="lg" variant="outline" className="gap-2">
            查看文档 <FileText className="w-4 h-4" />
          </Button>
          <Button size="lg" variant="ghost" className="gap-2">
            观看演示 <Play className="w-4 h-4" />
          </Button>
        </motion.div>
      </div>
    </section>
  )
}
```

**交付物**: 完整的Hero Section

---

## 📅 第一个月计划

### Week 1: 基础搭建 ✅
- Day 1: 团队和环境
- Day 2: 项目初始化
- Day 3: 设计系统
- Day 4: 布局导航
- Day 5: Hero Section

### Week 2: 首页核心内容
- Day 6: 特性展示区域（4个特性卡片）
- Day 7: 技术优势区域（6个优势点）
- Day 8: 使用案例展示（3个案例）
- Day 9: 统计数据和CTA区域
- Day 10: 首页优化和测试

### Week 3: 产品页面
- Day 11-12: 产品概述和功能详解
- Day 13: 技术架构展示
- Day 14: 使用场景详解
- Day 15: 产品页优化

### Week 4: 开发者页面
- Day 16-17: 快速开始指南
- Day 18: API文档结构
- Day 19: SDK文档和代码示例
- Day 20: 开发者页优化

---

## 🛠️ 开发环境设置

### 必需软件

```bash
# 1. Node.js 18+
node --version  # 应该 >= 18.0.0

# 2. pnpm
npm install -g pnpm
pnpm --version

# 3. Git
git --version

# 4. VS Code（推荐）
# 安装扩展：
# - ESLint
# - Prettier
# - Tailwind CSS IntelliSense
# - TypeScript Vue Plugin (Volar)
```

### 环境变量配置

创建 `.env.local`:
```env
# API配置
NEXT_PUBLIC_API_URL=http://localhost:8000

# 网站配置
NEXT_PUBLIC_SITE_URL=http://localhost:3000
NEXT_PUBLIC_SITE_NAME=Nautilus

# 分析（可选）
NEXT_PUBLIC_GA_ID=
NEXT_PUBLIC_ALGOLIA_APP_ID=
NEXT_PUBLIC_ALGOLIA_API_KEY=

# Sentry（可选）
SENTRY_DSN=
```

### 启动开发服务器

```bash
# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev

# 访问 http://localhost:3000
```

---

## 📚 必读文档

### 新成员入职必读（按顺序）

1. **WEBSITE_INDEX.md** (10分钟)
   - 了解文档体系
   - 快速导航

2. **WEBSITE_PREPARATION_REPORT.md** (30分钟)
   - 项目全局概览
   - 目标和预期

3. **根据角色阅读专业文档** (1-2小时)
   - 开发者 → WEBSITE_TECH_STACK.md
   - 设计师 → WEBSITE_DESIGN_GUIDE.md
   - 内容 → WEBSITE_CONTENT_PLAN.md
   - PM → WEBSITE_DEVELOPMENT_PLAN.md

### 每日参考文档

- **开发规范**: WEBSITE_DEVELOPMENT_PLAN.md 第8章
- **设计规范**: WEBSITE_DESIGN_GUIDE.md
- **组件库**: shadcn/ui文档
- **API参考**: Next.js文档

---

## 🎯 第一周目标

### 技术目标
- [x] 项目脚手架搭建完成
- [x] 开发环境配置完成
- [x] 基础组件库实现
- [x] 布局系统完成
- [x] Hero Section完成

### 团队目标
- [x] 团队成员到位
- [x] 沟通渠道建立
- [x] 开发流程确定
- [x] 代码规范统一

### 交付物
- [x] 可运行的项目
- [x] 设计系统文档
- [x] 基础组件库
- [x] 首页Hero Section

---

## 💡 最佳实践

### 开发流程

1. **每日站会** (15分钟)
   - 昨天完成了什么
   - 今天计划做什么
   - 遇到什么问题

2. **代码审查**
   - 所有PR必须审查
   - 至少1人批准
   - 自动化检查通过

3. **测试驱动**
   - 编写测试用例
   - 保持测试覆盖率
   - 定期运行测试

4. **文档同步**
   - 代码即文档
   - 及时更新README
   - 记录重要决策

### Git工作流

```bash
# 1. 创建功能分支
git checkout -b feature/hero-section

# 2. 开发和提交
git add .
git commit -m "feat: add hero section"

# 3. 推送到远程
git push origin feature/hero-section

# 4. 创建Pull Request
# 在GitHub上创建PR，等待审查

# 5. 合并到develop
# 审查通过后合并
```

### 提交规范

```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试
chore: 构建/工具

示例:
feat: add hero section to homepage
fix: resolve mobile navigation issue
docs: update API documentation
```

---

## 🔍 常见问题

### Q1: 如何快速了解项目？
**A**: 阅读WEBSITE_INDEX.md和WEBSITE_PREPARATION_REPORT.md

### Q2: 遇到技术问题怎么办？
**A**:
1. 查看WEBSITE_TECH_STACK.md
2. 查阅官方文档
3. 在团队群提问
4. 记录到问题文档

### Q3: 设计规范在哪里？
**A**: WEBSITE_DESIGN_GUIDE.md包含完整的设计系统

### Q4: 如何提交代码？
**A**: 遵循Git工作流和提交规范（见上文）

### Q5: 测试怎么写？
**A**: 参考WEBSITE_DEVELOPMENT_PLAN.md第10章

---

## 📞 联系方式

### 团队沟通
- **日常沟通**: Slack/飞书群
- **代码讨论**: GitHub Issues/PR
- **紧急事项**: 电话/微信

### 技术支持
- **Next.js**: https://nextjs.org/docs
- **Tailwind CSS**: https://tailwindcss.com/docs
- **shadcn/ui**: https://ui.shadcn.com

### 项目管理
- **项目看板**: [待设置]
- **文档中心**: [待设置]
- **设计文件**: [Figma链接]

---

## ✅ 启动检查清单

### 准备工作
- [ ] 阅读完本指南
- [ ] 阅读WEBSITE_INDEX.md
- [ ] 阅读角色相关文档
- [ ] 加入团队沟通群
- [ ] 获取必要的账号权限

### 环境配置
- [ ] 安装Node.js 18+
- [ ] 安装pnpm
- [ ] 安装Git
- [ ] 安装VS Code和扩展
- [ ] 克隆项目仓库
- [ ] 配置环境变量
- [ ] 启动开发服务器成功

### 开发准备
- [ ] 了解项目结构
- [ ] 熟悉开发规范
- [ ] 了解Git工作流
- [ ] 知道如何提问
- [ ] 准备好开始开发

---

## 🎉 开始开发！

一切准备就绪，现在可以开始开发了！

### 第一个任务建议

**前端开发者**:
- 实现Hero Section
- 创建基础组件
- 配置路由系统

**UI/UX设计师**:
- 完成首页设计
- 创建组件库
- 准备设计资源

**内容编辑**:
- 撰写首页文案
- 准备产品描述
- 规划博客内容

**项目经理**:
- 设置项目看板
- 组织每日站会
- 跟踪项目进度

---

## 📈 进度追踪

### 每日更新
在团队群分享：
- 今日完成的任务
- 遇到的问题
- 明日计划

### 每周回顾
- 本周完成情况
- 下周计划
- 风险和问题

### 里程碑庆祝
- M1: 项目启动 🎉
- M2: 基础完成 🎊
- M3: 首页完成 🚀
- ...

---

**准备好了吗？让我们开始构建Nautilus网站！** 🚀

---

**文档版本**: v1.0
**创建时间**: 2026-02-26
**适用阶段**: 项目启动
**下次更新**: Week 2开始时
