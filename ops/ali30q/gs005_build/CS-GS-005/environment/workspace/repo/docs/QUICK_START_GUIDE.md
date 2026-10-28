# Nautilus 快速开始指南

**版本**: 1.0
**目标**: 5分钟上手 Nautilus

---

## 安装

### 方式 1: Docker (推荐)

```bash
# 拉取镜像
docker pull openclaw/nautilus

# 运行
docker run -d -p 18789:18789 openclaw/nautilus

# 访问
# 浏览器打开 http://localhost:18789
```

### 方式 2: npm

```bash
# 安装
npm install -g openclaw

# 启动
openclaw

# 访问
# 浏览器打开 http://localhost:18789
```

---

## 选择 Agent

1. 打开 Web 界面
2. 在 Agent 市场浏览
3. 选择需要的 Agent
4. 添加到你的团队

### 常用 Agent

| 类别 | Agent |
|------|-------|
| 开发 | Python Developer, Frontend Engineer |
| 设计 | UI Designer, Logo Creator |
| 营销 | Social Media Manager, SEO Expert |
| 内容 | Content Writer, Blog Post |
| 分析 | Data Analyst, Market Research |

---

## 发布任务

### 方式 1: Web 界面

1. 在输入框输入任务
2. 描述你想要的结果
3. 点击发送

### 方式 2: API

```bash
curl -X POST http://localhost:18789/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task": "帮我写一个天气App",
    "agents": ["python-developer", "ui-designer"]
  }'
```

---

## 示例任务

### 任务 1: 写一个天气App

```
任务：帮我写一个天气预报的Python程序
要求：
- 使用天气API
- 显示7天预报
- 有简单UI
```

### 任务 2: 做市场分析

```
任务：分析智能家居市场
要求：
- 市场规模
- 主要玩家
- 发展趋势
- 投资机会
```

### 任务 3: 写推广文案

```
任务：帮我写一个新产品的推广文案
产品：AI助手
目标用户：开发者
风格：专业但有趣
```

---

## 进阶功能

### 多 Agent 协作

```json
{
  "task": "发布新产品",
  "agents": [
    "market-researcher",
    "content-writer",
    "designer",
    "social-media-manager"
  ]
}
```

### 自定义 Agent

在 `agents/` 目录创建新的 Agent 定义：

```yaml
name: My Agent
description: 我的自定义Agent
capabilities:
  - code
  - analyze
system_prompt: 你是一个专业的...
```

---

## 常见问题

### Q: 需要多少资源？

A: 推荐 4核+8GB RAM

### Q: 支持哪些模型？

A: OpenAI, Anthropic, Google, MiniMax 等

### Q: 如何扩展？

A: 通过插件系统添加新功能

---

## 下一步

- [ ] 阅读完整文档
- [ ] 加入 Discord 社区
- [ ] 贡献代码

**Discord**: 即将上线
**GitHub**: github.com/chunxiaoxx/nautilus-core
