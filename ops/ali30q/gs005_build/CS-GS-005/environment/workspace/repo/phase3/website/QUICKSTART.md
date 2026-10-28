# Nautilus 首页快速启动指南

## 🚀 快速开始

### 1. 安装依赖
```bash
npm install
```

### 2. 启动开发服务器
```bash
npm run dev
```

访问: http://localhost:5173

### 3. 查看首页
首页路径: `/` 或 `/home`

## 📁 首页相关文件

### 主要组件
- `src/pages/Home.tsx` - 首页入口
- `src/components/sections/Hero.tsx` - 主视觉区
- `src/components/sections/Features.tsx` - 功能特性
- `src/components/sections/HowItWorks.tsx` - 工作流程
- `src/components/sections/Stats.tsx` - 统计数据
- `src/components/sections/CTA.tsx` - 行动号召

### 样式文件
- `src/styles/index.css` - 全局样式
- `tailwind.config.js` - Tailwind配置

## 🎨 自定义修改

### 修改颜色
编辑 `tailwind.config.js`:
```js
colors: {
  primary: { ... },  // 主色调
  dark: { ... }      // 深色主题
}
```

### 修改内容
编辑对应的组件文件，例如修改特性列表:
```tsx
// src/components/sections/Features.tsx
const features = [
  { icon: '🤖', title: '...', description: '...' }
]
```

### 修改动画
调整 Framer Motion 参数:
```tsx
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.6 }}  // 修改动画时长
>
```

## 📱 响应式预览

### 移动端
- Chrome DevTools: F12 → Toggle device toolbar
- 推荐测试: iPhone SE (375px), iPhone 12 (390px)

### 平板
- 推荐测试: iPad (768px), iPad Pro (1024px)

### 桌面
- 推荐测试: 1280px, 1920px

## 🔧 常见问题

### Q: 动画不流畅？
A: 检查是否安装了 framer-motion: `npm install framer-motion`

### Q: 样式不生效？
A: 确保 Tailwind CSS 正确配置，运行 `npm run dev` 重启服务器

### Q: 构建失败？
A: 当前项目有一些其他文件的TypeScript错误，但不影响首页功能。可以使用 `npm run dev` 开发模式查看效果。

## 📚 更多信息

- 详细文档: `HOME_PAGE_SUMMARY.md`
- 设计系统: `DESIGN_SYSTEM.md`
- Framer Motion: https://www.framer.com/motion/
- Tailwind CSS: https://tailwindcss.com/
