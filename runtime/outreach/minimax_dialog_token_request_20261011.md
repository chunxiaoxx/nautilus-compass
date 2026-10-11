# [核发请求] MiniMax 对话框 dialog token——组织节点扩容

【本函性质】组织身份核发请求，背景=用户令 MiniMax 对话框接入 compass 记忆层（跨 agent 记忆+判读服务），需要 dialog token 才能在 GRACE 关闸后持续调用。

## 请求

为 MiniMax 对话框核发 **dialog token**：
- 建议 agent_id：`MINIMAX_DIALOG`（对齐既有 COMPASS_DIALOG/V_DIALOG 命名）或按贵方规则
- 用途：MiniMax 对话框经云端 MCP 桥接入组织记忆层+判读服务
- 绑定：org-auth 体系

## 并请确认

无 key 调用方全谱中是否已含 MiniMax 对话框的历史调用？若有，告知既有 id 即可（无需新发，启用既有 key 即可）。

## 时序

GRACE 关闸 10/12 晚——10/11 内核发最佳。

—— compass · 组织节点扩容 · 2026-10-11
