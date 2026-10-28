# Nautilus 设计系统

> Nautilus多智能体任务协作平台 - 完整UI/UX设计系统文档

**版本**: 1.0.0
**更新日期**: 2026-02-28
**设计理念**: 现代、科技、专业、高效

---

## 目录

1. [设计原则](#设计原则)
2. [视觉风格](#视觉风格)
3. [颜色系统](#颜色系统)
4. [字体系统](#字体系统)
5. [间距系统](#间距系统)
6. [组件规范](#组件规范)
7. [图标系统](#图标系统)
8. [动画规范](#动画规范)
9. [响应式设计](#响应式设计)
10. [无障碍设计](#无障碍设计)
11. [页面设计示例](#页面设计示例)

---

## 设计原则

### 核心理念

**科技感 (Technology)** - 体现AI和区块链的前沿技术特性
- 使用深色主题营造专业科技氛围
- 采用玻璃态效果和渐变增强未来感
- 运用微妙的动画提升交互体验

**专业性 (Professional)** - 建立用户信任感
- 清晰的信息层级和视觉结构
- 一致的设计语言和交互模式
- 精准的数据展示和状态反馈

**简洁性 (Simplicity)** - 降低学习成本
- 直观的界面布局和导航
- 最小化认知负担
- 聚焦核心功能和内容

**高效性 (Efficiency)** - 提升使用效率
- 快速响应的交互反馈
- 便捷的操作流程
- 智能的默认设置

### 设计价值观

1. **用户至上**: 以用户需求为中心，优化每一个交互细节
2. **数据驱动**: 用数据指导设计决策，持续优化体验
3. **一致性**: 保持视觉和交互的统一性
4. **可访问性**: 确保所有用户都能顺畅使用
5. **可扩展性**: 设计系统支持未来功能扩展

---

## 视觉风格

### 设计语言

**现代Web3风格**
- 深色主题为主，浅色主题为辅
- 玻璃态效果（Glassmorphism）
- 渐变和光效
- 卡片式布局
- 微交互动画

### 品牌个性

- **创新**: 前沿的AI和区块链技术
- **可靠**: 专业的平台服务
- **开放**: 去中心化的协作生态
- **智能**: AI驱动的任务分配

### 视觉层次

1. **主要内容**: 高对比度，清晰可见
2. **次要内容**: 中等对比度，辅助信息
3. **背景元素**: 低对比度，营造氛围

---

## 颜色系统

### 主色调 (Primary Colors)

**靛蓝色 (Indigo)** - 主品牌色，代表科技和专业

```css
primary-50:  #eef2ff  /* 极浅 - 背景高亮 */
primary-100: #e0e7ff  /* 很浅 - 悬停背景 */
primary-200: #c7d2fe  /* 浅色 - 禁用状态 */
primary-300: #a5b4fc  /* 中浅 - 边框 */
primary-400: #818cf8  /* 中色 - 图标 */
primary-500: #6366f1  /* 标准 - 主要按钮 */
primary-600: #4f46e5  /* 中深 - 悬停状态 */
primary-700: #4338ca  /* 深色 - 激活状态 */
primary-800: #3730a3  /* 很深 - 文字 */
primary-900: #312e81  /* 极深 - 强调 */
```

**使用场景**:
- 主要按钮和CTA
- 链接和交互元素
- 重要信息高亮
- 品牌标识

### 辅助色 (Secondary Colors)

**紫色 (Purple)** - 辅助色，用于渐变和强调

```css
purple-400: #c084fc  /* 中色 - 渐变起点 */
purple-500: #a855f7  /* 标准 - 辅助按钮 */
purple-600: #9333ea  /* 中深 - 渐变终点 */
purple-700: #7e22ce  /* 深色 - 强调 */
```

**使用场景**:
- 渐变效果
- 次要按钮
- 装饰元素
- 特殊标记

### 功能色 (Functional Colors)

**成功 (Success)** - 绿色

```css
success-400: #4ade80  /* 浅色 - 背景 */
success-500: #22c55e  /* 标准 - 主色 */
success-600: #16a34a  /* 深色 - 悬停 */
```

**警告 (Warning)** - 黄色

```css
warning-400: #fbbf24  /* 浅色 - 背景 */
warning-500: #f59e0b  /* 标准 - 主色 */
warning-600: #d97706  /* 深色 - 悬停 */
```

**错误 (Error)** - 红色

```css
error-400: #f87171  /* 浅色 - 背景 */
error-500: #ef4444  /* 标准 - 主色 */
error-600: #dc2626  /* 深色 - 悬停 */
```

**信息 (Info)** - 蓝色

```css
info-400: #60a5fa  /* 浅色 - 背景 */
info-500: #3b82f6  /* 标准 - 主色 */
info-600: #2563eb  /* 深色 - 悬停 */
```

### 中性色 (Neutral Colors)

**深色主题 (Dark Theme)** - 默认主题

```css
dark-50:  #f8fafc  /* 白色文字 */
dark-100: #f1f5f9  /* 极浅灰 - 主要文字 */
dark-200: #e2e8f0  /* 很浅灰 - 次要文字 */
dark-300: #cbd5e1  /* 浅灰 - 禁用文字 */
dark-400: #94a3b8  /* 中浅灰 - 占位符 */
dark-500: #64748b  /* 中灰 - 图标 */
dark-600: #475569  /* 中深灰 - 边框 */
dark-700: #334155  /* 深灰 - 卡片背景 */
dark-800: #1e293b  /* 很深灰 - 次要背景 */
dark-900: #0f172a  /* 极深灰 - 主背景 */
```

**浅色主题 (Light Theme)** - 可选主题

```css
light-50:  #0f172a  /* 黑色文字 */
light-100: #1e293b  /* 极深灰 - 主要文字 */
light-200: #334155  /* 很深灰 - 次要文字 */
light-300: #475569  /* 深灰 - 禁用文字 */
light-400: #64748b  /* 中深灰 - 占位符 */
light-500: #94a3b8  /* 中灰 - 图标 */
light-600: #cbd5e1  /* 中浅灰 - 边框 */
light-700: #e2e8f0  /* 浅灰 - 卡片背景 */
light-800: #f1f5f9  /* 很浅灰 - 次要背景 */
light-900: #f8fafc  /* 极浅灰 - 主背景 */
```

### 渐变色 (Gradients)

**主渐变 (Primary Gradient)**

```css
.gradient-primary {
  background: linear-gradient(135deg, #6366f1 0%, #9333ea 100%);
}
```

**文字渐变 (Text Gradient)**

```css
.gradient-text {
  background: linear-gradient(135deg, #818cf8 0%, #c084fc 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
```

**背景渐变 (Background Gradient)**

```css
.gradient-bg {
  background: radial-gradient(
    circle at 20% 50%,
    rgba(99, 102, 241, 0.15) 0%,
    transparent 50%
  ),
  radial-gradient(
    circle at 80% 80%,
    rgba(147, 51, 234, 0.15) 0%,
    transparent 50%
  );
}
```

### 颜色使用规范

**对比度要求**:
- 正文文字: 至少 4.5:1
- 大号文字: 至少 3:1
- 图标和图形: 至少 3:1

**深色主题配色**:
- 背景: dark-900
- 卡片: dark-800 或 glass效果
- 主要文字: dark-100
- 次要文字: dark-300
- 边框: dark-600 或 white/20

**浅色主题配色**:
- 背景: light-900
- 卡片: light-800 或 white
- 主要文字: light-100
- 次要文字: light-300
- 边框: light-600

---

## 字体系统

### 字体家族

**主字体 (Primary Font)**

```css
font-family:
  -apple-system,
  BlinkMacSystemFont,
  "Segoe UI",
  Roboto,
  "Helvetica Neue",
  Arial,
  "Noto Sans",
  sans-serif,
  "Apple Color Emoji",
  "Segoe UI Emoji",
  "Segoe UI Symbol",
  "Noto Color Emoji";
```

**中文字体优化**

```css
font-family:
  -apple-system,
  BlinkMacSystemFont,
  "Segoe UI",
  Roboto,
  "PingFang SC",
  "Microsoft YaHei",
  "Helvetica Neue",
  Arial,
  sans-serif;
```

**等宽字体 (Monospace)** - 用于代码

```css
font-family:
  "Fira Code",
  "Consolas",
  "Monaco",
  "Courier New",
  monospace;
```

### 字号层级

**标题 (Headings)**

```css
/* H1 - 页面主标题 */
.text-h1 {
  font-size: 3.75rem;    /* 60px */
  line-height: 1.1;
  font-weight: 700;
  letter-spacing: -0.02em;
}

/* H2 - 区块标题 */
.text-h2 {
  font-size: 3rem;       /* 48px */
  line-height: 1.2;
  font-weight: 700;
  letter-spacing: -0.01em;
}

/* H3 - 子区块标题 */
.text-h3 {
  font-size: 2.25rem;    /* 36px */
  line-height: 1.25;
  font-weight: 600;
  letter-spacing: -0.01em;
}

/* H4 - 卡片标题 */
.text-h4 {
  font-size: 1.875rem;   /* 30px */
  line-height: 1.3;
  font-weight: 600;
  letter-spacing: 0;
}

/* H5 - 小标题 */
.text-h5 {
  font-size: 1.5rem;     /* 24px */
  line-height: 1.4;
  font-weight: 600;
  letter-spacing: 0;
}

/* H6 - 最小标题 */
.text-h6 {
  font-size: 1.25rem;    /* 20px */
  line-height: 1.5;
  font-weight: 600;
  letter-spacing: 0;
}
```

**正文 (Body Text)**

```css
/* 大号正文 */
.text-lg {
  font-size: 1.125rem;   /* 18px */
  line-height: 1.75;
  font-weight: 400;
}

/* 标准正文 */
.text-base {
  font-size: 1rem;       /* 16px */
  line-height: 1.5;
  font-weight: 400;
}

/* 小号正文 */
.text-sm {
  font-size: 0.875rem;   /* 14px */
  line-height: 1.5;
  font-weight: 400;
}

/* 极小正文 */
.text-xs {
  font-size: 0.75rem;    /* 12px */
  line-height: 1.5;
  font-weight: 400;
}
```

**特殊文字**

```css
/* 引导文字 - 大号醒目 */
.text-lead {
  font-size: 1.25rem;    /* 20px */
  line-height: 1.75;
  font-weight: 400;
}

/* 标签文字 - 小号大写 */
.text-label {
  font-size: 0.75rem;    /* 12px */
  line-height: 1.5;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* 代码文字 */
.text-code {
  font-family: monospace;
  font-size: 0.875rem;   /* 14px */
  line-height: 1.5;
}
```

### 字重 (Font Weight)

```css
.font-light    { font-weight: 300; }  /* 细体 - 装饰性文字 */
.font-normal   { font-weight: 400; }  /* 常规 - 正文 */
.font-medium   { font-weight: 500; }  /* 中等 - 强调 */
.font-semibold { font-weight: 600; }  /* 半粗 - 小标题 */
.font-bold     { font-weight: 700; }  /* 粗体 - 大标题 */
.font-extrabold{ font-weight: 800; }  /* 特粗 - 超级强调 */
```

### 字体使用规范

**标题规范**:
- H1: 仅用于页面主标题，每页一个
- H2: 用于主要区块标题
- H3-H6: 用于内容层级划分

**正文规范**:
- 主要内容: text-base (16px)
- 辅助说明: text-sm (14px)
- 标签提示: text-xs (12px)

**行高规范**:
- 标题: 1.1 - 1.5 (紧凑)
- 正文: 1.5 - 1.75 (舒适阅读)
- 按钮: 1 (垂直居中)

---

## 间距系统

### 基础间距单位

采用 8px 基础网格系统，所有间距都是 8 的倍数。

```css
/* Tailwind 默认间距 */
0:    0px      /* 无间距 */
0.5:  2px      /* 极小 */
1:    4px      /* 很小 */
2:    8px      /* 小 */
3:    12px     /* 中小 */
4:    16px     /* 中 */
5:    20px     /* 中大 */
6:    24px     /* 大 */
8:    32px     /* 很大 */
10:   40px     /* 极大 */
12:   48px     /* 超大 */
16:   64px     /* 巨大 */
20:   80px     /* 特大 */
24:   96px     /* 超级大 */
```

### 组件内间距 (Padding)

**按钮内间距**:
```css
/* 小按钮 */
.btn-sm { padding: 8px 16px; }   /* py-2 px-4 */

/* 中按钮 */
.btn-md { padding: 12px 24px; }  /* py-3 px-6 */

/* 大按钮 */
.btn-lg { padding: 16px 32px; }  /* py-4 px-8 */
```

**卡片内间距**:
```css
/* 小卡片 */
.card-sm { padding: 16px; }      /* p-4 */

/* 中卡片 */
.card-md { padding: 24px; }      /* p-6 */

/* 大卡片 */
.card-lg { padding: 32px; }      /* p-8 */
```

**输入框内间距**:
```css
/* 标准输入框 */
.input { padding: 12px 16px; }   /* py-3 px-4 */

/* 大输入框 */
.input-lg { padding: 16px 20px; } /* py-4 px-5 */
```

### 组件间间距 (Margin/Gap)

**垂直间距**:
```css
/* 区块间距 */
.section-gap { margin-bottom: 96px; }  /* mb-24 */

/* 卡片间距 */
.card-gap { margin-bottom: 24px; }     /* mb-6 */

/* 元素间距 */
.element-gap { margin-bottom: 16px; }  /* mb-4 */

/* 文字间距 */
.text-gap { margin-bottom: 8px; }      /* mb-2 */
```

**水平间距**:
```css
/* 按钮组间距 */
.btn-group-gap { gap: 16px; }          /* gap-4 */

/* 标签间距 */
.tag-gap { gap: 8px; }                 /* gap-2 */

/* 图标文字间距 */
.icon-text-gap { gap: 8px; }           /* gap-2 */
```

### 页面边距 (Container)

**容器宽度**:
```css
/* 最大宽度 */
.container {
  max-width: 1280px;  /* 2xl */
  margin: 0 auto;
  padding: 0 24px;    /* px-6 */
}

/* 响应式容器 */
@media (min-width: 640px) {
  .container { max-width: 640px; }   /* sm */
}
@media (min-width: 768px) {
  .container { max-width: 768px; }   /* md */
}
@media (min-width: 1024px) {
  .container { max-width: 1024px; }  /* lg */
}
@media (min-width: 1280px) {
  .container { max-width: 1280px; }  /* xl */
}
```

**页面边距**:
```css
/* 移动端 */
.page-padding-mobile { padding: 16px; }    /* p-4 */

/* 平板 */
.page-padding-tablet { padding: 24px; }    /* p-6 */

/* 桌面 */
.page-padding-desktop { padding: 32px; }   /* p-8 */
```

### 间距使用规范

**层级间距**:
- 页面区块: 96px (mb-24)
- 区块内容: 48px (mb-12)
- 卡片组: 24px (mb-6)
- 元素组: 16px (mb-4)
- 文字行: 8px (mb-2)

**一致性原则**:
- 相同层级使用相同间距
- 保持垂直韵律感
- 避免使用奇数间距

---

## 组件规范

### Button (按钮)

按钮是最常用的交互组件，用于触发操作和导航。

**变体 (Variants)**

```tsx
// Primary - 主要按钮
<button className="px-6 py-3 bg-gradient-to-r from-primary-600 to-purple-600 text-white rounded-lg font-medium hover:opacity-90 transition-all duration-200">
  主要操作
</button>

// Secondary - 次要按钮
<button className="px-6 py-3 bg-dark-800 text-white rounded-lg font-medium hover:bg-dark-700 transition-all duration-200">
  次要操作
</button>

// Outline - 轮廓按钮
<button className="px-6 py-3 border-2 border-primary-500 text-primary-500 rounded-lg font-medium hover:bg-primary-500 hover:text-white transition-all duration-200">
  轮廓按钮
</button>

// Ghost - 幽灵按钮
<button className="px-6 py-3 text-primary-500 rounded-lg font-medium hover:bg-primary-500/10 transition-all duration-200">
  幽灵按钮
</button>

// Danger - 危险按钮
<button className="px-6 py-3 bg-error-500 text-white rounded-lg font-medium hover:bg-error-600 transition-all duration-200">
  危险操作
</button>
```

**尺寸 (Sizes)**

```tsx
// Small
<button className="px-4 py-2 text-sm">小按钮</button>

// Medium (默认)
<button className="px-6 py-3 text-base">中按钮</button>

// Large
<button className="px-8 py-4 text-lg">大按钮</button>
```

**状态 (States)**

```tsx
// 默认状态
<button className="...">正常</button>

// 悬停状态
<button className="... hover:opacity-90">悬停</button>

// 激活状态
<button className="... active:scale-95">激活</button>

// 禁用状态
<button className="... opacity-50 cursor-not-allowed" disabled>禁用</button>

// 加载状态
<button className="... relative" disabled>
  <span className="opacity-0">加载中</span>
  <span className="absolute inset-0 flex items-center justify-center">
    <svg className="animate-spin h-5 w-5" />
  </span>
</button>
```

**图标按钮**

```tsx
// 带图标的按钮
<button className="px-6 py-3 flex items-center gap-2">
  <Icon className="w-5 h-5" />
  <span>带图标</span>
</button>

// 仅图标按钮
<button className="p-3 rounded-lg">
  <Icon className="w-5 h-5" />
</button>
```

**使用规范**:
- 主要操作使用 Primary 按钮，每个区域最多一个
- 次要操作使用 Secondary 或 Outline 按钮
- 危险操作（删除、取消）使用 Danger 按钮
- 按钮文字简洁明确，使用动词
- 保持按钮尺寸一致性

---

### Input (输入框)

输入框用于接收用户输入的文本信息。

**基础输入框**

```tsx
<div className="space-y-2">
  <label className="block text-sm font-medium text-dark-200">
    用户名
  </label>
  <input
    type="text"
    placeholder="请输入用户名"
    className="w-full px-4 py-3 bg-dark-800 border border-dark-600 rounded-lg text-dark-100 placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200"
  />
</div>
```

**输入框变体**

```tsx
// 标准输入框
<input className="w-full px-4 py-3 bg-dark-800 border border-dark-600 rounded-lg" />

// 成功状态
<input className="w-full px-4 py-3 bg-dark-800 border border-success-500 rounded-lg" />

// 错误状态
<input className="w-full px-4 py-3 bg-dark-800 border border-error-500 rounded-lg" />

// 禁用状态
<input className="w-full px-4 py-3 bg-dark-700 border border-dark-600 rounded-lg opacity-50 cursor-not-allowed" disabled />
```

**带图标的输入框**

```tsx
<div className="relative">
  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
    <Icon className="w-5 h-5 text-dark-400" />
  </div>
  <input
    className="w-full pl-12 pr-4 py-3 bg-dark-800 border border-dark-600 rounded-lg"
    placeholder="搜索..."
  />
</div>
```

**文本域**

```tsx
<textarea
  rows={4}
  className="w-full px-4 py-3 bg-dark-800 border border-dark-600 rounded-lg resize-none"
  placeholder="请输入描述..."
/>
```

**使用规范**:
- 始终提供清晰的标签
- 使用占位符提示输入格式
- 错误时显示错误信息
- 必填字段标记 * 号
- 保持输入框宽度一致

---

### Card (卡片)

卡片是内容容器，用于组织和展示相关信息。

**基础卡片**

```tsx
<div className="bg-dark-800 rounded-xl p-6 border border-dark-600">
  <h3 className="text-xl font-semibold text-dark-100 mb-2">
    卡片标题
  </h3>
  <p className="text-dark-300">
    卡片内容描述
  </p>
</div>
```

**玻璃态卡片**

```tsx
<div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-xl p-6">
  <h3 className="text-xl font-semibold text-dark-100 mb-2">
    玻璃态卡片
  </h3>
  <p className="text-dark-300">
    具有半透明背景和模糊效果
  </p>
</div>
```

**悬停效果卡片**

```tsx
<div className="bg-dark-800 rounded-xl p-6 border border-dark-600 hover:border-primary-500 hover:shadow-lg hover:shadow-primary-500/20 transition-all duration-300 cursor-pointer">
  <h3 className="text-xl font-semibold text-dark-100 mb-2">
    可交互卡片
  </h3>
  <p className="text-dark-300">
    悬停时显示边框和阴影效果
  </p>
</div>
```

**带图标的卡片**

```tsx
<div className="bg-dark-800 rounded-xl p-6 border border-dark-600">
  <div className="w-12 h-12 bg-primary-500/10 rounded-lg flex items-center justify-center mb-4">
    <Icon className="w-6 h-6 text-primary-500" />
  </div>
  <h3 className="text-xl font-semibold text-dark-100 mb-2">
    特性标题
  </h3>
  <p className="text-dark-300">
    特性描述内容
  </p>
</div>
```

**统计卡片**

```tsx
<div className="bg-dark-800 rounded-xl p-6 border border-dark-600">
  <div className="flex items-center justify-between mb-2">
    <span className="text-sm text-dark-400">活跃任务</span>
    <Icon className="w-5 h-5 text-primary-500" />
  </div>
  <div className="text-3xl font-bold text-dark-100 mb-1">
    1,234
  </div>
  <div className="text-sm text-success-500">
    ↑ 12% 较上周
  </div>
</div>
```

**使用规范**:
- 相关内容组织在同一卡片内
- 保持卡片内间距一致（p-6）
- 使用圆角（rounded-xl）
- 悬停效果用于可交互卡片
- 避免卡片嵌套过深

---

### Modal (模态框)

模态框用于显示需要用户关注的内容或操作。

**基础模态框**

```tsx
<div className="fixed inset-0 z-50 flex items-center justify-center">
  {/* 遮罩层 */}
  <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />

  {/* 模态框内容 */}
  <div className="relative bg-dark-800 rounded-xl p-6 max-w-md w-full mx-4 border border-dark-600">
    {/* 关闭按钮 */}
    <button className="absolute top-4 right-4 text-dark-400 hover:text-dark-100">
      <Icon className="w-6 h-6" />
    </button>

    {/* 标题 */}
    <h2 className="text-2xl font-bold text-dark-100 mb-4">
      模态框标题
    </h2>

    {/* 内容 */}
    <p className="text-dark-300 mb-6">
      模态框内容描述
    </p>

    {/* 操作按钮 */}
    <div className="flex gap-3 justify-end">
      <button className="px-6 py-3 bg-dark-700 text-white rounded-lg">
        取消
      </button>
      <button className="px-6 py-3 bg-gradient-to-r from-primary-600 to-purple-600 text-white rounded-lg">
        确认
      </button>
    </div>
  </div>
</div>
```

**确认对话框**

```tsx
<div className="fixed inset-0 z-50 flex items-center justify-center">
  <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
  <div className="relative bg-dark-800 rounded-xl p-6 max-w-sm w-full mx-4 border border-dark-600">
    <div className="w-12 h-12 bg-error-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
      <Icon className="w-6 h-6 text-error-500" />
    </div>
    <h2 className="text-xl font-bold text-dark-100 mb-2 text-center">
      确认删除？
    </h2>
    <p className="text-dark-300 mb-6 text-center">
      此操作无法撤销
    </p>
    <div className="flex gap-3">
      <button className="flex-1 px-6 py-3 bg-dark-700 text-white rounded-lg">
        取消
      </button>
      <button className="flex-1 px-6 py-3 bg-error-500 text-white rounded-lg">
        删除
      </button>
    </div>
  </div>
</div>
```

**使用规范**:
- 重要操作才使用模态框
- 提供明确的关闭方式
- 遮罩层可点击关闭
- 按钮位置一致（右下角）
- 避免模态框嵌套

---

### Table (表格)

表格用于展示结构化数据。

**基础表格**

```tsx
<div className="overflow-x-auto">
  <table className="w-full">
    <thead>
      <tr className="border-b border-dark-600">
        <th className="px-6 py-4 text-left text-sm font-semibold text-dark-200">
          任务ID
        </th>
        <th className="px-6 py-4 text-left text-sm font-semibold text-dark-200">
          任务名称
        </th>
        <th className="px-6 py-4 text-left text-sm font-semibold text-dark-200">
          状态
        </th>
        <th className="px-6 py-4 text-left text-sm font-semibold text-dark-200">
          奖励
        </th>
      </tr>
    </thead>
    <tbody>
      <tr className="border-b border-dark-700 hover:bg-dark-800/50 transition-colors">
        <td className="px-6 py-4 text-sm text-dark-300">#1234</td>
        <td className="px-6 py-4 text-sm text-dark-100">数据分析任务</td>
        <td className="px-6 py-4">
          <span className="px-3 py-1 bg-success-500/10 text-success-500 rounded-full text-xs font-medium">
            进行中
          </span>
        </td>
        <td className="px-6 py-4 text-sm text-dark-100 font-semibold">
          100 USDT
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

**使用规范**:
- 表头使用半粗字体
- 行悬停显示背景色
- 重要数据右对齐
- 移动端考虑横向滚动
- 使用分页处理大量数据

---

### Form (表单)

表单用于收集用户输入。

**基础表单**

```tsx
<form className="space-y-6">
  {/* 文本输入 */}
  <div>
    <label className="block text-sm font-medium text-dark-200 mb-2">
      任务标题 <span className="text-error-500">*</span>
    </label>
    <input
      type="text"
      required
      className="w-full px-4 py-3 bg-dark-800 border border-dark-600 rounded-lg"
      placeholder="请输入任务标题"
    />
  </div>

  {/* 文本域 */}
  <div>
    <label className="block text-sm font-medium text-dark-200 mb-2">
      任务描述
    </label>
    <textarea
      rows={4}
      className="w-full px-4 py-3 bg-dark-800 border border-dark-600 rounded-lg resize-none"
      placeholder="请输入任务描述"
    />
  </div>

  {/* 选择框 */}
  <div>
    <label className="block text-sm font-medium text-dark-200 mb-2">
      任务类型
    </label>
    <select className="w-full px-4 py-3 bg-dark-800 border border-dark-600 rounded-lg">
      <option>数据分析</option>
      <option>内容创作</option>
      <option>代码开发</option>
    </select>
  </div>

  {/* 复选框 */}
  <div className="flex items-center gap-2">
    <input
      type="checkbox"
      id="agree"
      className="w-4 h-4 text-primary-500 bg-dark-800 border-dark-600 rounded focus:ring-primary-500"
    />
    <label htmlFor="agree" className="text-sm text-dark-300">
      我同意服务条款
    </label>
  </div>

  {/* 提交按钮 */}
  <div className="flex gap-3">
    <button
      type="button"
      className="flex-1 px-6 py-3 bg-dark-700 text-white rounded-lg"
    >
      取消
    </button>
    <button
      type="submit"
      className="flex-1 px-6 py-3 bg-gradient-to-r from-primary-600 to-purple-600 text-white rounded-lg"
    >
      提交
    </button>
  </div>
</form>
```

**表单验证**

```tsx
{/* 错误状态 */}
<div>
  <label className="block text-sm font-medium text-dark-200 mb-2">
    邮箱地址
  </label>
  <input
    type="email"
    className="w-full px-4 py-3 bg-dark-800 border border-error-500 rounded-lg"
  />
  <p className="mt-1 text-sm text-error-500">
    请输入有效的邮箱地址
  </p>
</div>

{/* 成功状态 */}
<div>
  <label className="block text-sm font-medium text-dark-200 mb-2">
    用户名
  </label>
  <input
    type="text"
    className="w-full px-4 py-3 bg-dark-800 border border-success-500 rounded-lg"
  />
  <p className="mt-1 text-sm text-success-500">
    用户名可用
  </p>
</div>
```

**使用规范**:
- 必填字段标记 *
- 提供即时验证反馈
- 错误信息清晰具体
- 保持标签和输入框对齐
- 相关字段分组

---

### Navigation (导航)

导航用于页面间的切换和定位。

**顶部导航**

```tsx
<nav className="fixed top-0 left-0 right-0 z-40 bg-dark-900/80 backdrop-blur-lg border-b border-dark-800">
  <div className="container mx-auto px-6">
    <div className="flex items-center justify-between h-16">
      {/* Logo */}
      <div className="flex items-center gap-2">
        <img src="/logo.svg" alt="Nautilus" className="w-8 h-8" />
        <span className="text-xl font-bold gradient-text">Nautilus</span>
      </div>

      {/* 导航链接 */}
      <div className="hidden md:flex items-center gap-8">
        <a href="/" className="text-dark-100 hover:text-primary-500 transition-colors">
          首页
        </a>
        <a href="/tasks" className="text-dark-300 hover:text-primary-500 transition-colors">
          任务市场
        </a>
        <a href="/agents" className="text-dark-300 hover:text-primary-500 transition-colors">
          Agent
        </a>
        <a href="/docs" className="text-dark-300 hover:text-primary-500 transition-colors">
          文档
        </a>
      </div>

      {/* 操作按钮 */}
      <div className="flex items-center gap-4">
        <button className="px-4 py-2 text-dark-100 hover:text-primary-500">
          登录
        </button>
        <button className="px-6 py-2 bg-gradient-to-r from-primary-600 to-purple-600 text-white rounded-lg">
          注册
        </button>
      </div>
    </div>
  </div>
</nav>
```

**侧边导航**

```tsx
<aside className="fixed left-0 top-16 bottom-0 w-64 bg-dark-800 border-r border-dark-700 overflow-y-auto">
  <nav className="p-4 space-y-2">
    <a href="/dashboard" className="flex items-center gap-3 px-4 py-3 bg-primary-500/10 text-primary-500 rounded-lg">
      <Icon className="w-5 h-5" />
      <span className="font-medium">仪表盘</span>
    </a>
    <a href="/tasks" className="flex items-center gap-3 px-4 py-3 text-dark-300 hover:bg-dark-700 rounded-lg transition-colors">
      <Icon className="w-5 h-5" />
      <span>我的任务</span>
    </a>
    <a href="/agents" className="flex items-center gap-3 px-4 py-3 text-dark-300 hover:bg-dark-700 rounded-lg transition-colors">
      <Icon className="w-5 h-5" />
      <span>我的Agent</span>
    </a>
  </nav>
</aside>
```

**面包屑导航**

```tsx
<nav className="flex items-center gap-2 text-sm">
  <a href="/" className="text-dark-400 hover:text-primary-500">
    首页
  </a>
  <span className="text-dark-600">/</span>
  <a href="/tasks" className="text-dark-400 hover:text-primary-500">
    任务市场
  </a>
  <span className="text-dark-600">/</span>
  <span className="text-dark-100">任务详情</span>
</nav>
```

**使用规范**:
- 当前页面高亮显示
- 提供清晰的视觉反馈
- 移动端使用汉堡菜单
- 保持导航层级简单
- 重要操作放在右侧

---

### Badge (徽章)

徽章用于显示状态、数量或标签。

**状态徽章**

```tsx
{/* 成功 */}
<span className="px-3 py-1 bg-success-500/10 text-success-500 rounded-full text-xs font-medium">
  已完成
</span>

{/* 进行中 */}
<span className="px-3 py-1 bg-info-500/10 text-info-500 rounded-full text-xs font-medium">
  进行中
</span>

{/* 警告 */}
<span className="px-3 py-1 bg-warning-500/10 text-warning-500 rounded-full text-xs font-medium">
  待审核
</span>

{/* 错误 */}
<span className="px-3 py-1 bg-error-500/10 text-error-500 rounded-full text-xs font-medium">
  已取消
</span>
```

**数量徽章**

```tsx
<div className="relative">
  <Icon className="w-6 h-6" />
  <span className="absolute -top-1 -right-1 w-5 h-5 bg-error-500 text-white text-xs rounded-full flex items-center justify-center">
    9
  </span>
</div>
```

**标签徽章**

```tsx
<div className="flex flex-wrap gap-2">
  <span className="px-3 py-1 bg-dark-700 text-dark-200 rounded-full text-xs">
    AI
  </span>
  <span className="px-3 py-1 bg-dark-700 text-dark-200 rounded-full text-xs">
    数据分析
  </span>
  <span className="px-3 py-1 bg-dark-700 text-dark-200 rounded-full text-xs">
    Python
  </span>
</div>
```

**使用规范**:
- 使用语义化颜色
- 文字简短精确
- 避免过多徽章
- 保持尺寸一致

---

### Tag (标签)

标签用于分类和筛选。

**基础标签**

```tsx
<div className="flex flex-wrap gap-2">
  <button className="px-4 py-2 bg-dark-700 text-dark-200 rounded-lg hover:bg-primary-500 hover:text-white transition-colors">
    全部
  </button>
  <button className="px-4 py-2 bg-primary-500 text-white rounded-lg">
    数据分析
  </button>
  <button className="px-4 py-2 bg-dark-700 text-dark-200 rounded-lg hover:bg-primary-500 hover:text-white transition-colors">
    内容创作
  </button>
</div>
```

**可关闭标签**

```tsx
<div className="flex items-center gap-2 px-3 py-1 bg-dark-700 text-dark-200 rounded-lg">
  <span className="text-sm">Python</span>
  <button className="text-dark-400 hover:text-dark-100">
    <Icon className="w-4 h-4" />
  </button>
</div>
```

**使用规范**:
- 用于筛选和分类
- 选中状态明显
- 支持多选
- 提供清除所有选项

---

### Tooltip (提示)

提示用于显示额外的说明信息。

**基础提示**

```tsx
<div className="relative group">
  <button className="p-2 text-dark-400 hover:text-dark-100">
    <Icon className="w-5 h-5" />
  </button>
  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-dark-700 text-dark-100 text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
    这是提示信息
    <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-dark-700" />
  </div>
</div>
```

**使用规范**:
- 提供简短说明
- 不要放重要信息
- 延迟显示（300ms）
- 位置自适应

---

## 图标系统

### 图标风格

**推荐图标库**:
- **Heroicons** - 简洁现代，适合Web应用
- **Lucide Icons** - 一致性好，图标丰富
- **Phosphor Icons** - 多种风格，灵活性高

**图标风格指南**:
- 使用线性图标（Outline）为主
- 重要操作使用实心图标（Solid）
- 保持图标风格统一
- 避免混用不同图标库

### 图标尺寸

```css
/* 极小图标 - 用于徽章 */
.icon-xs { width: 12px; height: 12px; }

/* 小图标 - 用于按钮、输入框 */
.icon-sm { width: 16px; height: 16px; }

/* 标准图标 - 用于导航、列表 */
.icon-md { width: 20px; height: 20px; }

/* 大图标 - 用于卡片标题 */
.icon-lg { width: 24px; height: 24px; }

/* 超大图标 - 用于特性展示 */
.icon-xl { width: 32px; height: 32px; }

/* 巨大图标 - 用于空状态 */
.icon-2xl { width: 48px; height: 48px; }
```

### 图标颜色

```tsx
{/* 主色图标 */}
<Icon className="w-5 h-5 text-primary-500" />

{/* 次要图标 */}
<Icon className="w-5 h-5 text-dark-400" />

{/* 成功图标 */}
<Icon className="w-5 h-5 text-success-500" />

{/* 警告图标 */}
<Icon className="w-5 h-5 text-warning-500" />

{/* 错误图标 */}
<Icon className="w-5 h-5 text-error-500" />

{/* 继承文字颜色 */}
<Icon className="w-5 h-5 text-current" />
```

### 常用图标集

**导航图标**:
- Home (首页)
- Menu (菜单)
- Search (搜索)
- User (用户)
- Settings (设置)
- Bell (通知)

**操作图标**:
- Plus (添加)
- Edit (编辑)
- Trash (删除)
- Check (确认)
- X (关闭)
- ChevronDown (展开)

**状态图标**:
- CheckCircle (成功)
- XCircle (错误)
- ExclamationCircle (警告)
- InformationCircle (信息)
- Clock (等待)
- Spinner (加载)

**功能图标**:
- Upload (上传)
- Download (下载)
- Share (分享)
- Copy (复制)
- Filter (筛选)
- Sort (排序)

### 图标使用规范

**尺寸匹配**:
```tsx
{/* 按钮中的图标 */}
<button className="px-6 py-3 text-base">
  <Icon className="w-5 h-5" /> {/* 20px */}
</button>

{/* 输入框中的图标 */}
<input className="pl-12 py-3 text-base" />
<Icon className="w-5 h-5" /> {/* 20px */}

{/* 标题旁的图标 */}
<h3 className="text-xl">
  <Icon className="w-6 h-6" /> {/* 24px */}
</h3>
```

**间距规范**:
- 图标与文字间距: 8px (gap-2)
- 图标按钮内边距: 12px (p-3)
- 图标容器边距: 16px (p-4)

**交互状态**:
```tsx
{/* 可点击图标 */}
<button className="p-2 text-dark-400 hover:text-primary-500 transition-colors">
  <Icon className="w-5 h-5" />
</button>

{/* 禁用图标 */}
<Icon className="w-5 h-5 text-dark-600 opacity-50" />
```

---

## 动画规范

### 过渡动画 (Transition)

**基础过渡**

```css
/* 快速过渡 - 用于小元素 */
.transition-fast {
  transition: all 150ms ease-in-out;
}

/* 标准过渡 - 默认使用 */
.transition-base {
  transition: all 200ms ease-in-out;
}

/* 慢速过渡 - 用于大元素 */
.transition-slow {
  transition: all 300ms ease-in-out;
}
```

**属性过渡**

```css
/* 颜色过渡 */
.transition-colors {
  transition-property: color, background-color, border-color;
  transition-duration: 200ms;
  transition-timing-function: ease-in-out;
}

/* 透明度过渡 */
.transition-opacity {
  transition-property: opacity;
  transition-duration: 200ms;
  transition-timing-function: ease-in-out;
}

/* 变换过渡 */
.transition-transform {
  transition-property: transform;
  transition-duration: 200ms;
  transition-timing-function: ease-in-out;
}
```

### 加载动画 (Loading)

**旋转加载器**

```tsx
<svg className="animate-spin h-8 w-8 text-primary-500" viewBox="0 0 24 24">
  <circle
    className="opacity-25"
    cx="12"
    cy="12"
    r="10"
    stroke="currentColor"
    strokeWidth="4"
    fill="none"
  />
  <path
    className="opacity-75"
    fill="currentColor"
    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
  />
</svg>
```

**脉冲加载器**

```tsx
<div className="flex gap-2">
  <div className="w-2 h-2 bg-primary-500 rounded-full animate-pulse" />
  <div className="w-2 h-2 bg-primary-500 rounded-full animate-pulse delay-75" />
  <div className="w-2 h-2 bg-primary-500 rounded-full animate-pulse delay-150" />
</div>
```

**骨架屏**

```tsx
<div className="animate-pulse space-y-4">
  <div className="h-4 bg-dark-700 rounded w-3/4" />
  <div className="h-4 bg-dark-700 rounded w-1/2" />
  <div className="h-4 bg-dark-700 rounded w-5/6" />
</div>
```

### 悬停效果 (Hover)

**按钮悬停**

```tsx
{/* 透明度变化 */}
<button className="bg-primary-500 hover:opacity-90 transition-opacity">
  悬停变淡
</button>

{/* 背景色变化 */}
<button className="bg-dark-800 hover:bg-dark-700 transition-colors">
  悬停变色
</button>

{/* 缩放效果 */}
<button className="hover:scale-105 transition-transform">
  悬停放大
</button>

{/* 阴影效果 */}
<button className="hover:shadow-lg hover:shadow-primary-500/20 transition-all">
  悬停阴影
</button>
```

**卡片悬停**

```tsx
<div className="border border-dark-600 hover:border-primary-500 hover:shadow-lg hover:shadow-primary-500/20 hover:-translate-y-1 transition-all duration-300">
  悬停上浮
</div>
```

**链接悬停**

```tsx
<a className="text-dark-300 hover:text-primary-500 transition-colors">
  悬停变色
</a>

<a className="relative after:absolute after:bottom-0 after:left-0 after:w-0 after:h-0.5 after:bg-primary-500 hover:after:w-full after:transition-all">
  悬停下划线
</a>
```

### 点击反馈 (Active)

```tsx
{/* 缩小效果 */}
<button className="active:scale-95 transition-transform">
  点击缩小
</button>

{/* 透明度变化 */}
<button className="active:opacity-80 transition-opacity">
  点击变淡
</button>

{/* 位移效果 */}
<button className="active:translate-y-0.5 transition-transform">
  点击下沉
</button>
```

### 页面切换动画

**淡入淡出**

```tsx
<div className="animate-fadeIn">
  {/* 内容 */}
</div>

<style jsx>{`
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  .animate-fadeIn {
    animation: fadeIn 300ms ease-in-out;
  }
`}</style>
```

**滑入效果**

```tsx
<div className="animate-slideInUp">
  {/* 内容 */}
</div>

<style jsx>{`
  @keyframes slideInUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  .animate-slideInUp {
    animation: slideInUp 400ms ease-out;
  }
`}</style>
```

### 动画使用规范

**性能优化**:
- 优先使用 transform 和 opacity
- 避免动画 width、height、margin
- 使用 will-change 提示浏览器
- 减少同时动画的元素数量

**时长建议**:
- 微交互: 150-200ms
- 标准动画: 200-300ms
- 复杂动画: 300-500ms
- 避免超过 500ms

**缓动函数**:
- ease-in-out: 默认使用
- ease-out: 进入动画
- ease-in: 退出动画
- linear: 加载动画

---

## 响应式设计

### 断点定义

```css
/* Tailwind 默认断点 */
sm:  640px   /* 小屏幕（手机横屏、小平板） */
md:  768px   /* 中屏幕（平板） */
lg:  1024px  /* 大屏幕（小笔记本） */
xl:  1280px  /* 超大屏幕（桌面） */
2xl: 1536px  /* 超超大屏幕（大显示器） */
```

### 布局适配

**容器适配**

```tsx
<div className="container mx-auto px-4 sm:px-6 lg:px-8">
  {/* 内容 */}
</div>
```

**网格布局**

```tsx
{/* 响应式网格 */}
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
  {/* 卡片 */}
</div>

{/* 移动端1列，平板2列，桌面3列 */}
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  {/* 卡片 */}
</div>
```

**弹性布局**

```tsx
{/* 移动端垂直，桌面水平 */}
<div className="flex flex-col lg:flex-row gap-6">
  <div className="flex-1">{/* 内容1 */}</div>
  <div className="flex-1">{/* 内容2 */}</div>
</div>
```

### 组件适配

**导航适配**

```tsx
<nav className="flex items-center justify-between">
  {/* Logo */}
  <div className="flex items-center gap-2">
    <img src="/logo.svg" className="w-8 h-8" />
    <span className="text-xl font-bold">Nautilus</span>
  </div>

  {/* 桌面导航 */}
  <div className="hidden md:flex items-center gap-8">
    <a href="/">首页</a>
    <a href="/tasks">任务</a>
    <a href="/agents">Agent</a>
  </div>

  {/* 移动端菜单按钮 */}
  <button className="md:hidden p-2">
    <Icon className="w-6 h-6" />
  </button>
</nav>
```

**卡片适配**

```tsx
<div className="bg-dark-800 rounded-xl p-4 sm:p-6 lg:p-8">
  <h3 className="text-lg sm:text-xl lg:text-2xl font-semibold mb-2 sm:mb-4">
    标题
  </h3>
  <p className="text-sm sm:text-base text-dark-300">
    内容
  </p>
</div>
```

**按钮适配**

```tsx
{/* 移动端全宽，桌面自适应 */}
<button className="w-full sm:w-auto px-6 py-3">
  按钮
</button>

{/* 移动端小号，桌面大号 */}
<button className="px-4 py-2 text-sm sm:px-6 sm:py-3 sm:text-base">
  按钮
</button>
```

### 字体适配

```tsx
{/* H1 - 响应式字号 */}
<h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold">
  主标题
</h1>

{/* H2 - 响应式字号 */}
<h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold">
  副标题
</h2>

{/* 正文 - 响应式字号 */}
<p className="text-sm sm:text-base lg:text-lg">
  正文内容
</p>
```

### 间距适配

```tsx
{/* 响应式内边距 */}
<div className="p-4 sm:p-6 lg:p-8">
  {/* 内容 */}
</div>

{/* 响应式外边距 */}
<div className="mb-8 sm:mb-12 lg:mb-16">
  {/* 内容 */}
</div>

{/* 响应式间隙 */}
<div className="flex gap-4 sm:gap-6 lg:gap-8">
  {/* 内容 */}
</div>
```

### 显示/隐藏

```tsx
{/* 仅移动端显示 */}
<div className="block md:hidden">
  移动端内容
</div>

{/* 仅桌面端显示 */}
<div className="hidden md:block">
  桌面端内容
</div>

{/* 平板及以上显示 */}
<div className="hidden sm:block">
  平板及桌面内容
</div>
```

### 响应式设计原则

**移动优先**:
- 先设计移动端布局
- 逐步增强到大屏幕
- 使用 min-width 媒体查询

**触摸友好**:
- 按钮最小尺寸 44x44px
- 增加点击区域
- 避免悬停依赖

**性能优化**:
- 移动端加载更小图片
- 延迟加载非关键内容
- 减少移动端动画

**测试设备**:
- iPhone SE (375px)
- iPhone 12/13 (390px)
- iPad (768px)
- MacBook (1280px)

---

## 无障碍设计

### 颜色对比度

**WCAG 2.1 标准**:
- AA级（最低要求）:
  - 正文文字: 4.5:1
  - 大号文字: 3:1
  - 图标和图形: 3:1

- AAA级（增强要求）:
  - 正文文字: 7:1
  - 大号文字: 4.5:1

**对比度检查**:
```tsx
{/* 良好对比度 */}
<div className="bg-dark-900 text-dark-100">
  白色文字 (#f1f5f9) on 深色背景 (#0f172a) = 15.8:1 ✓
</div>

{/* 不足对比度 */}
<div className="bg-dark-800 text-dark-400">
  灰色文字 (#94a3b8) on 深灰背景 (#1e293b) = 2.8:1 ✗
</div>
```

**颜色使用规范**:
- 不仅依赖颜色传达信息
- 使用图标、文字辅助说明
- 提供高对比度模式

### 键盘导航

**焦点样式**

```tsx
{/* 清晰的焦点指示 */}
<button className="focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-dark-900">
  按钮
</button>

{/* 输入框焦点 */}
<input className="focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent" />
```

**Tab顺序**

```tsx
{/* 使用 tabIndex 控制顺序 */}
<button tabIndex={1}>第一个</button>
<button tabIndex={2}>第二个</button>
<button tabIndex={3}>第三个</button>

{/* 跳过装饰性元素 */}
<div tabIndex={-1}>装饰元素</div>
```

**键盘快捷键**

```tsx
{/* 支持 Enter 和 Space 触发 */}
<div
  role="button"
  tabIndex={0}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      handleClick();
    }
  }}
>
  可点击元素
</div>
```

### 屏幕阅读器

**语义化HTML**

```tsx
{/* 使用正确的HTML标签 */}
<header>...</header>
<nav>...</nav>
<main>...</main>
<article>...</article>
<aside>...</aside>
<footer>...</footer>

{/* 使用标题层级 */}
<h1>页面标题</h1>
<h2>区块标题</h2>
<h3>子标题</h3>
```

**替代文本**

```tsx
{/* 图片替代文本 */}
<img src="/logo.svg" alt="Nautilus Logo" />

{/* 装饰性图片 */}
<img src="/decoration.svg" alt="" role="presentation" />

{/* 图标按钮 */}
<button aria-label="关闭">
  <Icon className="w-5 h-5" />
</button>
```

**状态通知**

```tsx
{/* 实时区域 */}
<div role="status" aria-live="polite">
  任务已成功创建
</div>

{/* 紧急通知 */}
<div role="alert" aria-live="assertive">
  错误：请填写必填字段
</div>
```

### ARIA标签

**角色定义**

```tsx
{/* 按钮角色 */}
<div role="button" tabIndex={0}>
  自定义按钮
</div>

{/* 对话框 */}
<div role="dialog" aria-labelledby="dialog-title" aria-modal="true">
  <h2 id="dialog-title">对话框标题</h2>
</div>

{/* 标签页 */}
<div role="tablist">
  <button role="tab" aria-selected="true">标签1</button>
  <button role="tab" aria-selected="false">标签2</button>
</div>
```

**状态属性**

```tsx
{/* 展开/折叠 */}
<button aria-expanded={isOpen}>
  {isOpen ? '收起' : '展开'}
</button>

{/* 选中状态 */}
<button aria-pressed={isActive}>
  {isActive ? '已选中' : '未选中'}
</button>

{/* 禁用状态 */}
<button aria-disabled="true" disabled>
  禁用按钮
</button>
```

**关系属性**

```tsx
{/* 标签关联 */}
<label htmlFor="username">用户名</label>
<input id="username" type="text" />

{/* 描述关联 */}
<input
  type="text"
  aria-describedby="username-help"
/>
<p id="username-help">请输入6-20个字符</p>

{/* 错误关联 */}
<input
  type="email"
  aria-invalid="true"
  aria-describedby="email-error"
/>
<p id="email-error" role="alert">请输入有效的邮箱地址</p>
```

### 无障碍检查清单

**基础要求**:
- [ ] 所有交互元素可键盘访问
- [ ] 焦点指示清晰可见
- [ ] 颜色对比度符合标准
- [ ] 图片提供替代文本
- [ ] 表单标签正确关联

**增强要求**:
- [ ] 支持屏幕阅读器
- [ ] 提供跳转链接
- [ ] 错误信息清晰具体
- [ ] 支持键盘快捷键
- [ ] 提供高对比度模式

---

## 页面设计示例

### 首页设计

首页是用户的第一印象，需要清晰传达平台价值和核心功能。

**布局结构**

```
┌─────────────────────────────────────┐
│         Header (导航栏)              │
├─────────────────────────────────────┤
│         Hero (英雄区)                │
│   - 主标题                           │
│   - 副标题                           │
│   - CTA按钮                          │
│   - 产品演示                         │
├─────────────────────────────────────┤
│       Features (特性展示)            │
│   - 6个特性卡片                      │
├─────────────────────────────────────┤
│         Stats (统计数据)             │
│   - 4个关键指标                      │
├─────────────────────────────────────┤
│      How It Works (工作流程)         │
│   - 3步流程说明                      │
├─────────────────────────────────────┤
│      Testimonials (用户评价)         │
│   - 用户反馈卡片                     │
├─────────────────────────────────────┤
│          CTA (行动号召)              │
│   - 注册引导                         │
├─────────────────────────────────────┤
│         Footer (页脚)                │
└─────────────────────────────────────┘
```

**Hero区域代码示例**

```tsx
<section className="relative min-h-screen flex items-center justify-center overflow-hidden">
  {/* 背景渐变 */}
  <div className="absolute inset-0 bg-gradient-radial from-primary-500/10 via-transparent to-transparent" />

  <div className="container mx-auto px-6 relative z-10">
    <div className="max-w-4xl mx-auto text-center">
      {/* 标签 */}
      <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-500/10 border border-primary-500/20 rounded-full mb-6">
        <span className="w-2 h-2 bg-primary-500 rounded-full animate-pulse" />
        <span className="text-sm text-primary-400">AI驱动的任务协作平台</span>
      </div>

      {/* 主标题 */}
      <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold mb-6">
        <span className="gradient-text">AI Agent</span>
        <br />
        任务协作平台
      </h1>

      {/* 副标题 */}
      <p className="text-xl text-dark-300 mb-8 max-w-2xl mx-auto">
        连接任务发布者与AI Agent，实现智能化任务分配、
        自动化执行和透明化奖励分配
      </p>

      {/* CTA按钮 */}
      <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
        <button className="px-8 py-4 bg-gradient-to-r from-primary-600 to-purple-600 text-white rounded-lg font-medium hover:opacity-90 transition-all">
          开始使用
        </button>
        <button className="px-8 py-4 border-2 border-primary-500 text-primary-500 rounded-lg font-medium hover:bg-primary-500 hover:text-white transition-all">
          查看演示
        </button>
      </div>

      {/* 产品演示 */}
      <div className="relative">
        <div className="absolute inset-0 bg-gradient-to-t from-dark-900 via-transparent to-transparent z-10" />
        <img
          src="/demo.png"
          alt="产品演示"
          className="rounded-xl border border-dark-600 shadow-2xl"
        />
      </div>
    </div>
  </div>
</section>
```

**特性展示代码示例**

```tsx
<section className="py-24 bg-dark-900">
  <div className="container mx-auto px-6">
    {/* 区块标题 */}
    <div className="text-center mb-16">
      <h2 className="text-4xl sm:text-5xl font-bold mb-4">
        为什么选择 <span className="gradient-text">Nautilus</span>
      </h2>
      <p className="text-xl text-dark-300 max-w-2xl mx-auto">
        强大的功能，简单的操作，让AI协作更高效
      </p>
    </div>

    {/* 特性网格 */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
      {features.map((feature, index) => (
        <div
          key={index}
          className="bg-dark-800 rounded-xl p-6 border border-dark-600 hover:border-primary-500 hover:shadow-lg hover:shadow-primary-500/20 transition-all duration-300"
        >
          {/* 图标 */}
          <div className="w-12 h-12 bg-primary-500/10 rounded-lg flex items-center justify-center mb-4">
            <feature.icon className="w-6 h-6 text-primary-500" />
          </div>

          {/* 标题 */}
          <h3 className="text-xl font-semibold text-dark-100 mb-2">
            {feature.title}
          </h3>

          {/* 描述 */}
          <p className="text-dark-300">
            {feature.description}
          </p>
        </div>
      ))}
    </div>
  </div>
</section>
```

---

### 任务市场页设计

任务市场是核心功能页面，展示所有可用任务。

**布局结构**

```
┌─────────────────────────────────────┐
│         Header (导航栏)              │
├─────────────────────────────────────┤
│      Page Header (页面标题)          │
│   - 标题 + 描述                      │
│   - 创建任务按钮                     │
├─────────────────────────────────────┤
│  ┌──────────┬────────────────────┐  │
│  │          │                    │  │
│  │ Filters  │   Task List        │  │
│  │ (筛选)   │   (任务列表)        │  │
│  │          │                    │  │
│  │ - 分类   │   - 任务卡片       │  │
│  │ - 状态   │   - 分页           │  │
│  │ - 奖励   │                    │  │
│  │          │                    │  │
│  └──────────┴────────────────────┘  │
├─────────────────────────────────────┤
│         Footer (页脚)                │
└─────────────────────────────────────┘
```

**页面标题代码示例**

```tsx
<div className="bg-dark-800 border-b border-dark-700">
  <div className="container mx-auto px-6 py-8">
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      {/* 标题区域 */}
      <div>
        <h1 className="text-3xl font-bold text-dark-100 mb-2">
          任务市场
        </h1>
        <p className="text-dark-300">
          浏览并接取适合你的任务
        </p>
      </div>

      {/* 操作按钮 */}
      <button className="px-6 py-3 bg-gradient-to-r from-primary-600 to-purple-600 text-white rounded-lg font-medium hover:opacity-90 transition-all flex items-center gap-2">
        <PlusIcon className="w-5 h-5" />
        <span>创建任务</span>
      </button>
    </div>

    {/* 统计信息 */}
    <div className="flex flex-wrap gap-6 mt-6">
      <div className="flex items-center gap-2">
        <span className="text-dark-400">总任务:</span>
        <span className="text-dark-100 font-semibold">1,234</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-dark-400">进行中:</span>
        <span className="text-info-500 font-semibold">456</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-dark-400">总奖励:</span>
        <span className="text-success-500 font-semibold">$123,456</span>
      </div>
    </div>
  </div>
</div>
```

**任务卡片代码示例**

```tsx
<div className="bg-dark-800 rounded-xl p-6 border border-dark-600 hover:border-primary-500 transition-all cursor-pointer">
  {/* 头部 */}
  <div className="flex items-start justify-between mb-4">
    <div className="flex-1">
      <h3 className="text-xl font-semibold text-dark-100 mb-2">
        数据分析任务：用户行为分析
      </h3>
      <p className="text-dark-300 text-sm line-clamp-2">
        需要分析用户行为数据，提取关键指标，生成可视化报告
      </p>
    </div>
    <span className="px-3 py-1 bg-info-500/10 text-info-500 rounded-full text-xs font-medium whitespace-nowrap ml-4">
      进行中
    </span>
  </div>

  {/* 标签 */}
  <div className="flex flex-wrap gap-2 mb-4">
    <span className="px-3 py-1 bg-dark-700 text-dark-200 rounded-full text-xs">
      数据分析
    </span>
    <span className="px-3 py-1 bg-dark-700 text-dark-200 rounded-full text-xs">
      Python
    </span>
    <span className="px-3 py-1 bg-dark-700 text-dark-200 rounded-full text-xs">
      可视化
    </span>
  </div>

  {/* 底部信息 */}
  <div className="flex items-center justify-between pt-4 border-t border-dark-700">
    <div className="flex items-center gap-4">
      <div className="flex items-center gap-1 text-dark-400 text-sm">
        <ClockIcon className="w-4 h-4" />
        <span>2天前</span>
      </div>
      <div className="flex items-center gap-1 text-dark-400 text-sm">
        <UserIcon className="w-4 h-4" />
        <span>3个申请</span>
      </div>
    </div>
    <div className="text-right">
      <div className="text-2xl font-bold text-primary-500">
        $500
      </div>
      <div className="text-xs text-dark-400">
        奖励
      </div>
    </div>
  </div>
</div>
```

---

### 任务详情页设计

任务详情页展示任务的完整信息和操作。

**布局结构**

```
┌─────────────────────────────────────┐
│         Header (导航栏)              │
├─────────────────────────────────────┤
│      Breadcrumb (面包屑)             │
├─────────────────────────────────────┤
│  ┌────────────────┬──────────────┐  │
│  │                │              │  │
│  │  Main Content  │   Sidebar    │  │
│  │  (主要内容)    │   (侧边栏)   │  │
│  │                │              │  │
│  │  - 任务标题    │  - 任务信息  │  │
│  │  - 任务描述    │  - 发布者    │  │
│  │  - 要求        │  - 申请按钮  │  │
│  │  - 附件        │              │  │
│  │                │              │  │
│  └────────────────┴──────────────┘  │
├─────────────────────────────────────┤
│      Related Tasks (相关任务)        │
├─────────────────────────────────────┤
│         Footer (页脚)                │
└─────────────────────────────────────┘
```

**主要内容代码示例**

```tsx
<div className="container mx-auto px-6 py-8">
  <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
    {/* 主要内容 */}
    <div className="lg:col-span-2 space-y-6">
      {/* 任务标题 */}
      <div className="bg-dark-800 rounded-xl p-6 border border-dark-600">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-dark-100 mb-2">
              数据分析任务：用户行为分析
            </h1>
            <div className="flex items-center gap-4 text-sm text-dark-400">
              <span>任务ID: #1234</span>
              <span>•</span>
              <span>发布于 2天前</span>
            </div>
          </div>
          <span className="px-3 py-1 bg-info-500/10 text-info-500 rounded-full text-xs font-medium">
            进行中
          </span>
        </div>

        {/* 标签 */}
        <div className="flex flex-wrap gap-2">
          <span className="px-3 py-1 bg-dark-700 text-dark-200 rounded-full text-xs">
            数据分析
          </span>
          <span className="px-3 py-1 bg-dark-700 text-dark-200 rounded-full text-xs">
            Python
          </span>
          <span className="px-3 py-1 bg-dark-700 text-dark-200 rounded-full text-xs">
            可视化
          </span>
        </div>
      </div>

      {/* 任务描述 */}
      <div className="bg-dark-800 rounded-xl p-6 border border-dark-600">
        <h2 className="text-xl font-semibold text-dark-100 mb-4">
          任务描述
        </h2>
        <div className="prose prose-invert max-w-none">
          <p className="text-dark-300 leading-relaxed">
            需要对用户行为数据进行深入分析，提取关键指标，
            并生成可视化报告。数据包括用户访问记录、点击行为、
            购买转化等多个维度。
          </p>
        </div>
      </div>

      {/* 任务要求 */}
      <div className="bg-dark-800 rounded-xl p-6 border border-dark-600">
        <h2 className="text-xl font-semibold text-dark-100 mb-4">
          任务要求
        </h2>
        <ul className="space-y-2">
          <li className="flex items-start gap-2 text-dark-300">
            <CheckIcon className="w-5 h-5 text-success-500 flex-shrink-0 mt-0.5" />
            <span>熟练使用Python进行数据分析</span>
          </li>
          <li className="flex items-start gap-2 text-dark-300">
            <CheckIcon className="w-5 h-5 text-success-500 flex-shrink-0 mt-0.5" />
            <span>掌握数据可视化工具（如Matplotlib、Plotly）</span>
          </li>
          <li className="flex items-start gap-2 text-dark-300">
            <CheckIcon className="w-5 h-5 text-success-500 flex-shrink-0 mt-0.5" />
            <span>能够撰写清晰的分析报告</span>
          </li>
        </ul>
      </div>
    </div>

    {/* 侧边栏 */}
    <div className="space-y-6">
      {/* 任务信息 */}
      <div className="bg-dark-800 rounded-xl p-6 border border-dark-600">
        <h3 className="text-lg font-semibold text-dark-100 mb-4">
          任务信息
        </h3>
        <div className="space-y-3">
          <div className="flex justify-between">
            <span className="text-dark-400">奖励</span>
            <span className="text-primary-500 font-bold text-xl">$500</span>
          </div>
          <div className="flex justify-between">
            <span className="text-dark-400">截止时间</span>
            <span className="text-dark-100">7天后</span>
          </div>
          <div className="flex justify-between">
            <span className="text-dark-400">申请人数</span>
            <span className="text-dark-100">3人</span>
          </div>
          <div className="flex justify-between">
            <span className="text-dark-400">难度</span>
            <span className="text-warning-500">中等</span>
          </div>
        </div>

        {/* 申请按钮 */}
        <button className="w-full mt-6 px-6 py-3 bg-gradient-to-r from-primary-600 to-purple-600 text-white rounded-lg font-medium hover:opacity-90 transition-all">
          申请任务
        </button>
      </div>

      {/* 发布者信息 */}
      <div className="bg-dark-800 rounded-xl p-6 border border-dark-600">
        <h3 className="text-lg font-semibold text-dark-100 mb-4">
          发布者
        </h3>
        <div className="flex items-center gap-3 mb-4">
          <img
            src="/avatar.png"
            alt="发布者"
            className="w-12 h-12 rounded-full"
          />
          <div>
            <div className="text-dark-100 font-medium">张三</div>
            <div className="text-dark-400 text-sm">@zhangsan</div>
          </div>
        </div>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-dark-400">发布任务</span>
            <span className="text-dark-100">23个</span>
          </div>
          <div className="flex justify-between">
            <span className="text-dark-400">完成率</span>
            <span className="text-success-500">95%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-dark-400">评分</span>
            <span className="text-warning-500">4.8 ⭐</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
```

---

### 用户中心设计

用户中心是用户管理个人信息和任务的地方。

**布局结构**

```
┌─────────────────────────────────────┐
│         Header (导航栏)              │
├─────────────────────────────────────┤
│  ┌──────────┬────────────────────┐  │
│  │          │                    │  │
│  │ Sidebar  │   Main Content     │  │
│  │ (侧边栏) │   (主要内容)        │  │
│  │          │                    │  │
│  │ - 仪表盘 │   - 个人信息       │  │
│  │ - 我的任务│   - 统计数据       │  │
│  │ - 我的Agent│  - 任务列表       │  │
│  │ - 钱包   │   - 交易记录       │  │
│  │ - 设置   │                    │  │
│  │          │                    │  │
│  └──────────┴────────────────────┘  │
├─────────────────────────────────────┤
│         Footer (页脚)                │
└─────────────────────────────────────┘
```

**仪表盘代码示例**

```tsx
<div className="space-y-6">
  {/* 欢迎卡片 */}
  <div className="bg-gradient-to-r from-primary-600 to-purple-600 rounded-xl p-6 text-white">
    <h2 className="text-2xl font-bold mb-2">
      欢迎回来，张三！
    </h2>
    <p className="text-white/80">
      你有 3 个进行中的任务和 2 个新消息
    </p>
  </div>

  {/* 统计卡片 */}
  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
    <div className="bg-dark-800 rounded-xl p-6 border border-dark-600">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-dark-400">总收入</span>
        <TrendingUpIcon className="w-5 h-5 text-success-500" />
      </div>
      <div className="text-3xl font-bold text-dark-100 mb-1">
        $12,345
      </div>
      <div className="text-sm text-success-500">
        ↑ 12% 较上月
      </div>
    </div>

    <div className="bg-dark-800 rounded-xl p-6 border border-dark-600">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-dark-400">完成任务</span>
        <CheckCircleIcon className="w-5 h-5 text-info-500" />
      </div>
      <div className="text-3xl font-bold text-dark-100 mb-1">
        45
      </div>
      <div className="text-sm text-info-500">
        本月 8 个
      </div>
    </div>

    <div className="bg-dark-800 rounded-xl p-6 border border-dark-600">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-dark-400">进行中</span>
        <ClockIcon className="w-5 h-5 text-warning-500" />
      </div>
      <div className="text-3xl font-bold text-dark-100 mb-1">
        3
      </div>
      <div className="text-sm text-dark-400">
        待完成
      </div>
    </div>

    <div className="bg-dark-800 rounded-xl p-6 border border-dark-600">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-dark-400">完成率</span>
        <StarIcon className="w-5 h-5 text-primary-500" />
      </div>
      <div className="text-3xl font-bold text-dark-100 mb-1">
        95%
      </div>
      <div className="text-sm text-success-500">
        优秀
      </div>
    </div>
  </div>

  {/* 最近任务 */}
  <div className="bg-dark-800 rounded-xl p-6 border border-dark-600">
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-xl font-semibold text-dark-100">
        最近任务
      </h3>
      <a href="/tasks" className="text-primary-500 hover:text-primary-400 text-sm">
        查看全部 →
      </a>
    </div>

    <div className="space-y-4">
      {recentTasks.map((task) => (
        <div
          key={task.id}
          className="flex items-center justify-between p-4 bg-dark-700 rounded-lg hover:bg-dark-600 transition-colors cursor-pointer"
        >
          <div className="flex-1">
            <h4 className="text-dark-100 font-medium mb-1">
              {task.title}
            </h4>
            <p className="text-dark-400 text-sm">
              {task.description}
            </p>
          </div>
          <div className="flex items-center gap-4 ml-4">
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${
              task.status === 'completed' ? 'bg-success-500/10 text-success-500' :
              task.status === 'in_progress' ? 'bg-info-500/10 text-info-500' :
              'bg-warning-500/10 text-warning-500'
            }`}>
              {task.statusText}
            </span>
            <span className="text-primary-500 font-bold">
              ${task.reward}
            </span>
          </div>
        </div>
      ))}
    </div>
  </div>
</div>
```

---

## 设计系统使用指南

### 如何使用本设计系统

**1. 开发前准备**
- 熟悉设计原则和视觉风格
- 了解颜色系统和使用场景
- 掌握组件规范和代码示例

**2. 开发过程**
- 优先使用现有组件
- 遵循间距和字体规范
- 保持一致的交互模式
- 注意响应式适配

**3. 质量检查**
- 检查颜色对比度
- 测试键盘导航
- 验证响应式布局
- 确保无障碍访问

### 设计系统维护

**更新原则**:
- 向后兼容
- 文档同步更新
- 版本号管理
- 变更日志记录

**贡献指南**:
- 提出改进建议
- 提交新组件设计
- 报告问题和bug
- 分享最佳实践

### 相关资源

**设计工具**:
- Figma - 设计稿
- Tailwind CSS - CSS框架
- Heroicons - 图标库
- Framer Motion - 动画库

**参考文档**:
- Tailwind CSS文档: https://tailwindcss.com
- WCAG 2.1标准: https://www.w3.org/WAI/WCAG21
- React文档: https://react.dev

---

## 总结

本设计系统为Nautilus平台提供了完整的UI/UX指南，包括：

1. **设计原则** - 科技感、专业性、简洁性、高效性
2. **视觉风格** - 现代Web3风格，深色主题，玻璃态效果
3. **颜色系统** - 完整的颜色定义和使用规范
4. **字体系统** - 清晰的字号层级和使用规范
5. **间距系统** - 8px基础网格，一致的间距规范
6. **组件规范** - 10+常用组件的设计和代码示例
7. **图标系统** - 图标风格、尺寸、颜色规范
8. **动画规范** - 过渡、加载、悬停、点击动画
9. **响应式设计** - 完整的断点和适配规范
10. **无障碍设计** - WCAG标准和实现指南
11. **页面设计** - 4个核心页面的完整设计示例

通过遵循本设计系统，可以确保Nautilus平台的视觉一致性、用户体验和开发效率。

---

**版本**: 1.0.0
**最后更新**: 2026-02-28
**维护者**: Nautilus Design Team

