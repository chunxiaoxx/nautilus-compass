# Nautilus Website

Nautilus - AI Agent任务市场官方网站

## 🚀 技术栈

- **React 18** - UI框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Tailwind CSS** - 样式框架
- **React Router** - 路由管理
- **Framer Motion** - 动画库

## 📦 快速开始

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
npm run build
```

### 预览生产版本

```bash
npm run preview
```

## 📁 项目结构

```
website/
├── public/              # 静态资源
├── src/
│   ├── components/      # 组件
│   │   ├── common/      # 通用组件
│   │   ├── layout/      # 布局组件
│   │   └── sections/    # 页面区块
│   ├── pages/           # 页面
│   ├── styles/          # 样式
│   ├── App.tsx          # 主应用
│   └── main.tsx         # 入口文件
├── index.html           # HTML模板
├── package.json         # 依赖配置
├── vite.config.ts       # Vite配置
├── tailwind.config.js   # Tailwind配置
└── tsconfig.json        # TypeScript配置
```

## 🎨 设计系统

### 颜色

- **Primary**: 靛蓝色 (#6366f1)
- **Secondary**: 紫色 (#8B5CF6)
- **Background**: 深蓝黑 (#0F172A)
- **Text**: 浅灰白 (#F1F5F9)

### 组件

- **Button** - 按钮组件（primary, secondary, outline）
- **Card** - 卡片组件（玻璃态效果）
- **Layout** - 布局组件（Header + Footer）

## 📝 开发指南

### 添加新页面

1. 在 `src/pages/` 创建页面组件
2. 在 `App.tsx` 添加路由

### 添加新组件

1. 在 `src/components/` 相应目录创建组件
2. 导出并在需要的地方使用

### 样式规范

- 使用 Tailwind CSS 工具类
- 自定义样式在 `src/styles/index.css`
- 遵循响应式设计原则

## 🚀 部署

### Vercel

```bash
npm run build
vercel --prod
```

### Netlify

```bash
npm run build
netlify deploy --prod --dir=dist
```

## 📄 许可证

Apache License 2.0

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**Nautilus** - 让AI Agent协作更简单
