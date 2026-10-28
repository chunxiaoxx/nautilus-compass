# 首页组件使用示例

## 组件导入和使用

### Home 页面
```tsx
import Hero from '../components/sections/Hero'
import Features from '../components/sections/Features'
import HowItWorks from '../components/sections/HowItWorks'
import Stats from '../components/sections/Stats'
import CTA from '../components/sections/CTA'

export default function Home() {
  return (
    <div className="min-h-screen">
      <Hero />
      <Features />
      <HowItWorks />
      <Stats />
      <CTA />
    </div>
  )
}
```

## 各组件详细说明

### 1. Hero 组件

**特点**:
- 全屏主视觉区
- 动态背景渐变光球
- 响应式标题和副标题
- 双CTA按钮
- 产品演示区域

**自定义示例**:
```tsx
// 修改标题
<h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
  <span className="gradient-text">你的标题</span>
  <br />
  副标题文字
</h1>

// 修改按钮文字
<Button size="lg">你的按钮文字</Button>
```

### 2. Features 组件

**特点**:
- 6个特性卡片网格
- 图标 + 标题 + 描述
- 悬停动画效果
- 响应式布局

**自定义示例**:
```tsx
const features = [
  {
    icon: '🎯',  // 修改图标
    title: '你的特性标题',
    description: '你的特性描述'
  },
  // 添加更多特性...
]
```

### 3. HowItWorks 组件

**特点**:
- 4步工作流程
- 步骤编号和图标
- 连接线和箭头
- 滚动触发动画

**自定义示例**:
```tsx
const steps = [
  {
    number: '01',
    title: '第一步',
    description: '步骤描述',
    icon: '📝'
  },
  // 添加更多步骤...
]
```

### 4. Stats 组件

**特点**:
- 4个统计指标
- 数字滚动动画
- 玻璃态背景
- 悬停放大效果

**自定义示例**:
```tsx
const stats = [
  {
    value: 1234,      // 数字值
    label: '标签文字',
    prefix: '',       // 前缀（如 $）
    suffix: ''        // 后缀（如 %）
  },
  // 添加更多统计...
]
```

### 5. CTA 组件

**特点**:
- 行动号召区域
- 双CTA按钮
- 信任指标
- 动态背景效果

**自定义示例**:
```tsx
<h2 className="text-4xl md:text-5xl font-bold mb-4">
  你的号召标题
</h2>
<p className="text-xl text-dark-300 mb-8">
  你的号召描述
</p>
```

## 动画配置

### 淡入动画
```tsx
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.6 }}
>
  内容
</motion.div>
```

### 滚动触发动画
```tsx
<motion.div
  initial={{ opacity: 0, y: 20 }}
  whileInView={{ opacity: 1, y: 0 }}
  viewport={{ once: true }}  // 只触发一次
  transition={{ duration: 0.6 }}
>
  内容
</motion.div>
```

### 悬停动画
```tsx
<motion.div
  whileHover={{ y: -8, scale: 1.02 }}
  transition={{ duration: 0.3 }}
>
  内容
</motion.div>
```

### 依次出现动画（Stagger）
```tsx
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1  // 每个子元素延迟0.1s
    }
  }
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
}

<motion.div variants={containerVariants} initial="hidden" animate="visible">
  {items.map((item, i) => (
    <motion.div key={i} variants={itemVariants}>
      {item}
    </motion.div>
  ))}
</motion.div>
```

## 样式类使用

### 渐变文字
```tsx
<span className="gradient-text">渐变文字</span>
```

### 玻璃态效果
```tsx
<div className="glass rounded-2xl p-8">
  内容
</div>
```

### 渐变背景
```tsx
<div className="bg-gradient-to-r from-primary-600 to-purple-600">
  内容
</div>
```

### 响应式字号
```tsx
<h1 className="text-4xl md:text-5xl lg:text-6xl">
  响应式标题
</h1>
```

### 响应式间距
```tsx
<div className="p-4 md:p-6 lg:p-8">
  响应式内边距
</div>
```

## 颜色系统

### 主色调
```tsx
className="text-primary-500"      // 文字
className="bg-primary-500"        // 背景
className="border-primary-500"    // 边框
```

### 深色主题
```tsx
className="text-dark-100"         // 主要文字
className="text-dark-300"         // 次要文字
className="text-dark-400"         // 辅助文字
className="bg-dark-800"           // 卡片背景
className="bg-dark-900"           // 页面背景
```

### 功能色
```tsx
className="text-success-500"      // 成功（绿色）
className="text-warning-500"      // 警告（黄色）
className="text-error-500"        // 错误（红色）
className="text-info-500"         // 信息（蓝色）
```

## 最佳实践

### 1. 性能优化
- 使用 `viewport={{ once: true }}` 避免重复触发动画
- 动画时长控制在 200-500ms
- 优先使用 transform 和 opacity（GPU加速）

### 2. 响应式设计
- 移动优先（先写移动端样式）
- 使用 Tailwind 断点: sm, md, lg, xl
- 测试多种设备尺寸

### 3. 可访问性
- 保持足够的颜色对比度
- 使用语义化HTML标签
- 提供清晰的视觉层次

### 4. 代码组织
- 将数据和UI分离
- 使用常量定义配置
- 保持组件简洁（单一职责）

## 扩展建议

### 添加新的特性卡片
1. 编辑 `Features.tsx`
2. 在 `features` 数组中添加新对象
3. 保持图标、标题、描述的一致性

### 添加新的统计指标
1. 编辑 `Stats.tsx`
2. 在 `stats` 数组中添加新对象
3. 设置 value, label, prefix, suffix

### 修改工作流程步骤
1. 编辑 `HowItWorks.tsx`
2. 修改 `steps` 数组
3. 可以增加或减少步骤数量

### 自定义动画效果
1. 调整 `initial` 和 `animate` 属性
2. 修改 `transition` 的 duration 和 ease
3. 添加 `whileHover` 或 `whileTap` 交互

## 故障排除

### 动画不显示
- 检查 framer-motion 是否安装
- 确认组件正确导入 motion
- 查看浏览器控制台错误

### 样式不生效
- 确认 Tailwind CSS 正确配置
- 检查类名拼写
- 清除缓存重启开发服务器

### 响应式布局问题
- 使用浏览器开发工具测试
- 检查断点类名（sm:, md:, lg:）
- 确认容器宽度设置正确
