# Nautilus 网站UI/UX设计指南

**版本**: v1.0
**创建时间**: 2026-02-26
**项目**: Nautilus多智能体任务协作平台
**设计风格**: 现代、科技感、专业

---

## 1. 设计理念

### 1.1 核心设计原则
- **简洁明了**: 清晰的信息层级，避免视觉混乱
- **科技感**: 体现区块链和AI技术的前沿性
- **专业性**: 建立企业级产品的信任感
- **易用性**: 直观的交互，降低学习成本
- **一致性**: 统一的设计语言和交互模式

### 1.2 设计目标
- 3秒内传达核心价值
- 引导用户完成关键操作
- 建立品牌认知和信任
- 提供愉悦的浏览体验
- 支持多设备和多场景

---

## 2. 色彩系统

### 2.1 主色调

#### 品牌主色 - 科技蓝
```
Primary Blue
- 50:  #f0f9ff  (背景、悬停)
- 100: #e0f2fe
- 200: #bae6fd
- 300: #7dd3fc
- 400: #38bdf8
- 500: #0ea5e9  ← 主色
- 600: #0284c7
- 700: #0369a1
- 800: #075985
- 900: #0c4a6e  (深色文字)
```

**使用场景**:
- 主要按钮和CTA
- 链接和交互元素
- 重要信息高亮
- 品牌标识

#### 辅助色 - 深空蓝
```
Secondary Navy
- 50:  #f8fafc
- 500: #1e293b
- 900: #0f172a  ← 辅助色
```

**使用场景**:
- 导航栏背景
- 页脚背景
- 深色模式主色
- 文字颜色

### 2.2 功能色

#### 成功 - 绿色
```
Success Green
- 500: #10b981
- 600: #059669
```

#### 警告 - 橙色
```
Warning Orange
- 500: #f59e0b
- 600: #d97706
```

#### 错误 - 红色
```
Error Red
- 500: #ef4444
- 600: #dc2626
```

#### 信息 - 蓝色
```
Info Blue
- 500: #3b82f6
- 600: #2563eb
```

### 2.3 中性色

#### 灰度系统
```
Gray Scale
- 50:  #f9fafb  (浅背景)
- 100: #f3f4f6
- 200: #e5e7eb  (边框)
- 300: #d1d5db
- 400: #9ca3af  (禁用)
- 500: #6b7280  (次要文字)
- 600: #4b5563
- 700: #374151  (正文)
- 800: #1f2937
- 900: #111827  (标题)
```

### 2.4 渐变色

#### 主渐变
```css
/* 科技蓝渐变 */
background: linear-gradient(135deg, #0ea5e9 0%, #0369a1 100%);

/* 深空渐变 */
background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);

/* 光晕效果 */
background: radial-gradient(circle at 50% 50%,
  rgba(14, 165, 233, 0.15) 0%,
  transparent 50%);
```

### 2.5 暗黑模式

#### 暗黑模式色彩映射
```
Light Mode          →  Dark Mode
--------------------------------------------------
#ffffff (背景)      →  #0f172a
#f9fafb (次背景)    →  #1e293b
#111827 (文字)      →  #f9fafb
#6b7280 (次文字)    →  #94a3b8
#e5e7eb (边框)      →  #334155
```

---

## 3. 字体系统

### 3.1 字体选择

#### 西文字体
```css
/* 主字体 - Inter */
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

/* 等宽字体 - JetBrains Mono */
font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
```

**Inter特点**:
- 现代、清晰、易读
- 优秀的屏幕显示效果
- 支持可变字体
- 广泛的字符集

#### 中文字体
```css
/* 中文主字体 */
font-family: 'PingFang SC', 'Microsoft YaHei', 'Noto Sans SC', sans-serif;

/* 完整字体栈 */
font-family: 'Inter', 'PingFang SC', -apple-system, BlinkMacSystemFont,
  'Segoe UI', 'Microsoft YaHei', sans-serif;
```

### 3.2 字体大小

#### 类型比例 (Type Scale)
```
xs:   12px / 0.75rem   (小标签、辅助文字)
sm:   14px / 0.875rem  (正文小、表单)
base: 16px / 1rem      (正文)
lg:   18px / 1.125rem  (正文大、引言)
xl:   20px / 1.25rem   (小标题)
2xl:  24px / 1.5rem    (标题)
3xl:  30px / 1.875rem  (大标题)
4xl:  36px / 2.25rem   (页面标题)
5xl:  48px / 3rem      (Hero标题)
6xl:  60px / 3.75rem   (超大标题)
7xl:  72px / 4.5rem    (特大标题)
```

### 3.3 字重 (Font Weight)
```
Light:    300  (装饰性文字)
Regular:  400  (正文)
Medium:   500  (强调、按钮)
Semibold: 600  (小标题)
Bold:     700  (标题)
Extrabold: 800 (超大标题)
```

### 3.4 行高 (Line Height)
```
Tight:   1.25  (大标题)
Snug:    1.375 (标题)
Normal:  1.5   (正文)
Relaxed: 1.625 (长文本)
Loose:   2.0   (特殊场景)
```

### 3.5 字间距 (Letter Spacing)
```
Tighter: -0.05em  (大标题)
Tight:   -0.025em (标题)
Normal:   0       (正文)
Wide:     0.025em (小字)
Wider:    0.05em  (全大写)
```

---

## 4. 间距系统

### 4.1 间距比例
```
0:   0px
1:   4px    (0.25rem)
2:   8px    (0.5rem)
3:   12px   (0.75rem)
4:   16px   (1rem)     ← 基础单位
5:   20px   (1.25rem)
6:   24px   (1.5rem)
8:   32px   (2rem)
10:  40px   (2.5rem)
12:  48px   (3rem)
16:  64px   (4rem)
20:  80px   (5rem)
24:  96px   (6rem)
32:  128px  (8rem)
```

### 4.2 组件间距规则
```
- 相关元素: 8-16px
- 组件内部: 16-24px
- 组件之间: 32-48px
- 区块之间: 64-96px
- 页面区域: 96-128px
```

---

## 5. 布局系统

### 5.1 网格系统

#### 桌面端 (Desktop)
```
Container: 1280px max-width
Columns: 12列
Gutter: 24px
Margin: 48px
```

#### 平板端 (Tablet)
```
Container: 100%
Columns: 8列
Gutter: 20px
Margin: 32px
```

#### 移动端 (Mobile)
```
Container: 100%
Columns: 4列
Gutter: 16px
Margin: 16px
```

### 5.2 断点 (Breakpoints)
```css
/* Mobile First */
sm:  640px   /* 手机横屏 */
md:  768px   /* 平板竖屏 */
lg:  1024px  /* 平板横屏/小笔记本 */
xl:  1280px  /* 桌面 */
2xl: 1536px  /* 大屏幕 */
```

### 5.3 容器宽度
```css
.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 24px;
}

.container-narrow {
  max-width: 768px;  /* 文章、表单 */
}

.container-wide {
  max-width: 1536px;  /* 宽屏展示 */
}

.container-full {
  max-width: 100%;    /* 全宽 */
}
```

---

## 6. 组件设计

### 6.1 按钮 (Buttons)

#### 主要按钮 (Primary)
```css
.btn-primary {
  background: #0ea5e9;
  color: #ffffff;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: #0284c7;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);
}
```

#### 次要按钮 (Secondary)
```css
.btn-secondary {
  background: transparent;
  color: #0ea5e9;
  border: 2px solid #0ea5e9;
  padding: 12px 24px;
  border-radius: 8px;
}
```

#### 按钮尺寸
```
Small:  py-2 px-4  text-sm   (32px height)
Medium: py-3 px-6  text-base (44px height)
Large:  py-4 px-8  text-lg   (56px height)
```

### 6.2 卡片 (Cards)

#### 基础卡片
```css
.card {
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
}

.card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  transform: translateY(-4px);
}
```

#### 特色卡片
```css
.card-featured {
  background: linear-gradient(135deg, #0ea5e9 0%, #0369a1 100%);
  color: #ffffff;
  border: 2px solid rgba(255, 255, 255, 0.2);
}
```

### 6.3 输入框 (Input Fields)

```css
.input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 16px;
  transition: all 0.2s;
}

.input:focus {
  border-color: #0ea5e9;
  outline: none;
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1);
}
```

### 6.4 导航栏 (Navigation)

#### 桌面导航
```
Height: 72px
Background: rgba(255, 255, 255, 0.8)
Backdrop-filter: blur(12px)
Border-bottom: 1px solid rgba(0, 0, 0, 0.1)
Position: sticky
```

#### 移动导航
```
Full-screen overlay
Slide-in animation
Close button
Backdrop blur
```

### 6.5 页脚 (Footer)

```
Background: #0f172a
Color: #94a3b8
Padding: 64px 0 32px
4-column layout (desktop)
1-column layout (mobile)
```

---

## 7. 图标系统

### 7.1 图标风格
- **风格**: 线性图标 (Outline)
- **粗细**: 2px stroke
- **圆角**: 2px radius
- **尺寸**: 16px, 20px, 24px, 32px, 48px

### 7.2 图标使用规则
```
- 导航图标: 24px
- 按钮图标: 20px
- 列表图标: 16px
- 特性图标: 48px
- Hero图标: 64px
```

### 7.3 图标颜色
```
- 默认: currentColor (继承文字颜色)
- 主色: #0ea5e9
- 成功: #10b981
- 警告: #f59e0b
- 错误: #ef4444
```

---

## 8. 动画和过渡

### 8.1 动画原则
- **有目的**: 每个动画都应该有明确的目的
- **快速**: 保持动画简短（200-400ms）
- **自然**: 使用缓动函数模拟物理运动
- **一致**: 相似元素使用相似动画

### 8.2 缓动函数 (Easing)
```css
/* 标准缓动 */
ease-out: cubic-bezier(0, 0, 0.2, 1)     /* 进入 */
ease-in:  cubic-bezier(0.4, 0, 1, 1)     /* 退出 */
ease-in-out: cubic-bezier(0.4, 0, 0.2, 1) /* 双向 */

/* 弹性缓动 */
spring: cubic-bezier(0.34, 1.56, 0.64, 1)
```

### 8.3 动画时长
```
Fast:   150ms  (小元素、简单过渡)
Normal: 250ms  (标准过渡)
Slow:   400ms  (复杂动画、页面过渡)
```

### 8.4 常用动画

#### 淡入淡出
```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.fade-in {
  animation: fadeIn 0.3s ease-out;
}
```

#### 滑入
```css
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

#### 缩放
```css
@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
```

#### 悬停效果
```css
.hover-lift {
  transition: transform 0.2s ease-out;
}

.hover-lift:hover {
  transform: translateY(-4px);
}
```

---

## 9. 阴影系统

### 9.1 阴影层级
```css
/* 无阴影 */
shadow-none: none

/* 微阴影 */
shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05)

/* 小阴影 */
shadow: 0 1px 3px rgba(0, 0, 0, 0.1)

/* 中阴影 */
shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1)

/* 大阴影 */
shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1)

/* 超大阴影 */
shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.1)

/* 巨大阴影 */
shadow-2xl: 0 25px 50px rgba(0, 0, 0, 0.15)
```

### 9.2 彩色阴影
```css
/* 品牌色阴影 */
.shadow-primary {
  box-shadow: 0 8px 24px rgba(14, 165, 233, 0.2);
}

/* 成功色阴影 */
.shadow-success {
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.2);
}
```

---

## 10. 圆角系统

### 10.1 圆角尺寸
```css
rounded-none: 0px
rounded-sm:   4px   (小元素)
rounded:      6px   (默认)
rounded-md:   8px   (卡片、按钮)
rounded-lg:   12px  (大卡片)
rounded-xl:   16px  (特大卡片)
rounded-2xl:  24px  (Hero区域)
rounded-full: 9999px (圆形)
```

### 10.2 使用规则
```
- 按钮: 8px
- 输入框: 8px
- 卡片: 12px
- 模态框: 16px
- 图片: 12px
- 头像: 9999px (圆形)
```

---

## 11. 响应式设计

### 11.1 移动优先策略
```css
/* 默认样式 (Mobile) */
.hero {
  padding: 32px 16px;
  font-size: 32px;
}

/* 平板 */
@media (min-width: 768px) {
  .hero {
    padding: 64px 32px;
    font-size: 48px;
  }
}

/* 桌面 */
@media (min-width: 1024px) {
  .hero {
    padding: 96px 48px;
    font-size: 60px;
  }
}
```

### 11.2 响应式图片
```html
<picture>
  <source media="(min-width: 1024px)" srcset="hero-desktop.jpg">
  <source media="(min-width: 768px)" srcset="hero-tablet.jpg">
  <img src="hero-mobile.jpg" alt="Hero">
</picture>
```

### 11.3 响应式排版
```
Mobile:  16px base, 1.5 line-height
Tablet:  16px base, 1.6 line-height
Desktop: 18px base, 1.7 line-height
```

---

## 12. 特殊效果

### 12.1 玻璃态 (Glassmorphism)
```css
.glass {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}
```

### 12.2 渐变边框
```css
.gradient-border {
  position: relative;
  background: #ffffff;
  border-radius: 12px;
}

.gradient-border::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 12px;
  padding: 2px;
  background: linear-gradient(135deg, #0ea5e9, #0369a1);
  -webkit-mask: linear-gradient(#fff 0 0) content-box,
                linear-gradient(#fff 0 0);
  mask-composite: exclude;
}
```

### 12.3 发光效果
```css
.glow {
  box-shadow: 0 0 20px rgba(14, 165, 233, 0.5),
              0 0 40px rgba(14, 165, 233, 0.3),
              0 0 60px rgba(14, 165, 233, 0.1);
}
```

### 12.4 网格背景
```css
.grid-background {
  background-image:
    linear-gradient(rgba(14, 165, 233, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(14, 165, 233, 0.1) 1px, transparent 1px);
  background-size: 50px 50px;
}
```

---

## 13. 可访问性设计

### 13.1 颜色对比度
```
- 正文文字: 至少 4.5:1
- 大文字(18px+): 至少 3:1
- 图标和UI元素: 至少 3:1
```

### 13.2 焦点状态
```css
.focusable:focus {
  outline: 2px solid #0ea5e9;
  outline-offset: 2px;
}

.focusable:focus:not(:focus-visible) {
  outline: none;
}
```

### 13.3 触摸目标
```
- 最小尺寸: 44x44px
- 间距: 至少 8px
- 移动端按钮: 48x48px
```

---

## 14. 设计资源

### 14.1 设计工具
- **Figma**: 主要设计工具
- **Adobe XD**: 备选工具
- **Sketch**: macOS用户

### 14.2 设计系统
- **Tailwind UI**: 组件参考
- **shadcn/ui**: 组件库
- **Radix UI**: 无样式组件

### 14.3 图标资源
- **Lucide Icons**: 主要图标库
- **Heroicons**: 备选图标
- **Phosphor Icons**: 补充图标

### 14.4 插图和图片
- **unDraw**: 免费插图
- **Unsplash**: 高质量图片
- **Pexels**: 免费视频和图片

---

## 15. 品牌元素

### 15.1 Logo使用规范
```
- 最小尺寸: 32px height
- 安全区域: Logo周围至少留出Logo高度的1/2空间
- 颜色变体: 全彩、单色、白色、黑色
- 禁止: 拉伸、旋转、添加效果、改变颜色
```

### 15.2 品牌图形
- 网络节点图案
- 六边形网格
- 连接线动画
- 粒子效果

---

## 16. 页面模板

### 16.1 Hero Section模板
```
┌─────────────────────────────────────────┐
│  [导航栏]                                │
├─────────────────────────────────────────┤
│                                          │
│         [超大标题]                       │
│         [副标题]                         │
│         [CTA按钮组]                      │
│                                          │
│         [Hero图片/动画]                  │
│                                          │
└─────────────────────────────────────────┘
```

### 16.2 特性展示模板
```
┌──────────┬──────────┬──────────┐
│  [图标]  │  [图标]  │  [图标]  │
│  标题    │  标题    │  标题    │
│  描述    │  描述    │  描述    │
└──────────┴──────────┴──────────┘
```

### 16.3 CTA区域模板
```
┌─────────────────────────────────────────┐
│              [标题]                      │
│              [描述]                      │
│         [主按钮] [次按钮]                │
└─────────────────────────────────────────┘
```

---

## 17. 设计检查清单

### 17.1 视觉设计
- [ ] 色彩对比度符合WCAG AA标准
- [ ] 字体大小适中，易于阅读
- [ ] 间距一致，视觉层级清晰
- [ ] 图标风格统一
- [ ] 图片质量高，加载优化

### 17.2 交互设计
- [ ] 所有交互元素有明确的悬停状态
- [ ] 按钮和链接易于识别
- [ ] 表单有清晰的错误提示
- [ ] 加载状态有明确反馈
- [ ] 动画流畅，不影响性能

### 17.3 响应式设计
- [ ] 在所有断点下布局正常
- [ ] 移动端触摸目标足够大
- [ ] 图片在不同设备上正常显示
- [ ] 文字在小屏幕上可读

### 17.4 可访问性
- [ ] 键盘可以访问所有功能
- [ ] 图片有替代文本
- [ ] 表单有正确的标签
- [ ] 焦点状态清晰可见
- [ ] 支持屏幕阅读器

---

## 18. 下一步行动

1. ✅ 完成设计指南
2. ⏳ 创建Figma设计文件
3. ⏳ 设计关键页面原型
4. ⏳ 用户测试和反馈
5. ⏳ 迭代优化设计

---

**文档状态**: 已完成
**审核状态**: 待审核
**最后更新**: 2026-02-26
