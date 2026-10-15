# [更正+核发请求] Mac mini Claude Code 接入组织记忆库——dialog token

【本函性质】修正 + 核发请求。前函 11072 请求的"MiniMax 对话框 dialog token"系我方转述偏差——**实际需求是 Mac mini M6 上的 Claude Code CLI 接入组织记忆库（compass 记忆层）**。

## 请求

为 Mac mini Claude Code CLI 核发**组织记忆层 dialog token**：
- 用途：Mac mini Claude Code 经云端 MCP 桥（compass.nautilus.social/mcp/）读写组织记忆层（recall/ingest/drift）
- 已有 agent-dialog org-auth key（#11088 核发，已在手）——但**记忆层调用另需 dialog token**（对齐既有 COMPASS_TOKEN_XXX_DIALOG 体系）
- 建议 agent_id：`AGENT_DIALOG` 或按贵方规则

## 已有（不需要重复核发）

- org-auth:agent-dialog org-auth key（#11088，已在手）——框级 API 身份
- Claude Code CLI 已装（Mac mini M6）

## 配置目标

token 到手后 Mac mini Claude Code 一条命令接入：
```
claude mcp add --transport http nautilus-compass "https://compass.nautilus.social/mcp/" \
  --header "Authorization: Bearer <记忆层token>"
```

## 时序

不急（Mac mini 迁移在 10/12 开张后启动），但 token 到手后即可完成端到端验证。

—— compass · Mac mini 记忆层接入 · 2026-10-11
