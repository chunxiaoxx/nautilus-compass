# Nautilus 设计系统 - 快速参考

> 开发者快速查阅指南

## 颜色速查

### 主色调
```css
primary-500: #6366f1  /* 主要按钮、链接 */
primary-600: #4f46e5  /* 悬停状态 */
purple-600: #9333ea   /* 渐变终点 */
```

### 功能色
```css
success-500: #22c55e  /* 成功状态 */
warning-500: #f59e0b  /* 警告状态 */
error-500: #ef4444    /* 错误状态 */
info-500: #3b82f6     /* 信息状态 */
```

### 中性色（深色主题）
```css
dark-900: #0f172a    /* 主背景 */
dark-800: #1e293b    /* 卡片背景 */
dark-700: #334155    /* 次要背景 */
dark-600: #475569    /* 边框 */
dark-100: #f1f5f9    /* 主要文字 */
dark-300: #cbd5e1    /* 次要文字 */
```

## 字体速查

### 标题
```tsx
<h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold">
<h2 className="text-4xl sm:text-5xl font-bold">
<h3 className="text-3xl sm:text-4xl font-semibold">
<h4 className="text-2xl font-semibold">
```

### 正文
```tsx
<p className="text-base">      /* 16px - 标准 */
<p className="text-lg">       /* 18px - 大号 */
<p className="text-sm">       /* 14px - 小号 */
<p className="text-xs">       /* 12px - 极小 */
```

## 间距速查

### 常用间距
```tsx
p-4   /* 16px - 小卡片内边距 */
p-6   /* 24px - 标准卡片内边距 */
p-8   /* 32px - 大卡片内边距 */

mb-4  /* 16px - 元素间距 */
mb-6  /* 24px - 卡片间距 */
mb-12 /* 48px - 区块内容间距 */
mb-24 /* 96px - 页面区块间距 */

gap-2 /* 8px - 标签、图标间距 */
gap-4 /* 16px - 按钮组间距 */
gap-6 /* 24px - 卡片网格间距 */
```

## 组件速查

### 按钮
```tsx
/* 主要按钮 */
<button className="px-6 py-3 bg-gradient-to-r from-primary-600 to-purple-600 text-white rounded-lg font-medium hover:opacity-90 transition-all">
  主要操作
</button>

/* 次要按钮 */
<button className="px-6 py-3 bg-dark-800 text-white rounded-lg font-medium hover:bg-dark-700 transition-all">
  次要操作
</button>

/* 轮廓按钮 */
<button className="px-6 py-3 border-2 border-primary-500 text-primary-500 rounded-lg font-medium hover:bg-primary-500 hover:text-white transition-all">
  轮廓按钮
</button>
```

### 输入框
```tsx
<input
  type="text"
  placeholder="请输入..."
  className="w-full px-4 py-3 bg-dark-800 border border-dark-600 rounded-lg text-dark-100 placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
/>
```

### 卡片
```tsx
/* 基础卡片 */
<div className="bg-dark-800 rounded-xl p-6 border border-dark-600">
  内容
</div>

/* 玻璃态卡片 */
<div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-xl p-6">
  内容
</div>

/* 可交互卡片 */
<div className="bg-dark-800 rounded-xl p-6 border border-dark-600 hover:border-primary-500 hover:shadow-lg hover:shadow-primary-500/20 transition-all cursor-pointer">
  内容
</div>
```

### 徽章
```tsx
/* 成功 */
<span className="px-3 py-1 bg-success-500/10 text-success-500 rounded-full text-xs font-medium">
  已完成
</span>

/* 进行中 */
<span className="px-3 py-1 bg-info-500/10 text-info-500 rounded-full text-xs font-medium">
  进行中
</span>

/* 警告 */
<span className="px-3 py-1 bg-warning-500/10 text-warning-500 rounded-full text-xs font-medium">
  待审核
</span>

/* 错误 */
<span className="px-3 py-1 bg-error-500/10 text-error-500 rounded-full text-xs font-medium">
  已取消
</span>
```

## 渐变速查

### 主渐变
```tsx
className="bg-gradient-to-r from-primary-600 to-purple-600"
```

### 文字渐变
```tsx
className="bg-gradient-to-r from-primary-400 to-purple-400 bg-clip-text text-transparent"
```

### 背景渐变
```tsx
className="bg-gradient-radial from-primary-500/10 via-transparent to-transparent"
```

## 动画速查

### 过渡
```tsx
className="transition-all duration-200"      /* 标准过渡 */
className="transition-colors duration-200"   /* 颜色过渡 */
className="transition-opacity duration-200"  /* 透明度过渡 */
className="transition-transform duration-200" /* 变换过渡 */
```

### 悬停效果
```tsx
className="hover:opacity-90"           /* 透明度变化 */
className="hover:bg-dark-700"          /* 背景色变化 */
className="hover:scale-105"            /* 缩放 */
className="hover:-translate-y-1"       /* 上浮 */
className="hover:shadow-lg"            /* 阴影 */
```

### 点击反馈
```tsx
className="active:scale-95"            /* 缩小 */
className="active:opacity-80"          /* 变淡 */
className="active:translate-y-0.5"     /* 下沉 */
```

## 响应式速查

### 断点
```tsx
sm:   /* 640px+ */
md:   /* 768px+ */
lg:   /* 1024px+ */
xl:   /* 1280px+ */
2xl:  /* 1536px+ */
```

### 常用模式
```tsx
/* 响应式网格 */
className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"

/* 响应式弹性布局 */
className="flex flex-col lg:flex-row gap-6"

/* 响应式字号 */
className="text-4xl sm:text-5xl lg:text-6xl"

/* 响应式间距 */
className="p-4 sm:p-6 lg:p-8"

/* 响应式显示/隐藏 */
className="block md:hidden"        /* 仅移动端 */
className="hidden md:block"        /* 仅桌面端 */
```

## 无障碍速查

### 焦点样式
```tsx
className="focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-dark-900"
```

### ARIA标签
```tsx
<button aria-label="关闭">
  <Icon />
</button>

<img src="..." alt="描述" />

<div role="button" tabIndex={0}>
  自定义按钮
</div>
```

## 图标尺寸速查

```tsx
className="w-4 h-4"   /* 16px - 小图标 */
className="w-5 h-5"   /* 20px - 标准图标 */
className="w-6 h-6"   /* 24px - 大图标 */
className="w-8 h-8"   /* 32px - 超大图标 */
```

## 常用布局模式

### 容器
```tsx
<div className="container mx-auto px-6">
  内容
</div>
```

### 居中布局
```tsx
<div className="flex items-center justify-center min-h-screen">
  内容
</div>
```

### 两栏布局
```tsx
<div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
  <div className="lg:col-span-2">主内容</div>
  <div>侧边栏</div>
</div>
```

### 卡片网格
```tsx
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
  {items.map(item => <Card key={item.id} />)}
</div>
```

---

**提示**: 完整文档请查看 `DESIGN_SYSTEM.md`
