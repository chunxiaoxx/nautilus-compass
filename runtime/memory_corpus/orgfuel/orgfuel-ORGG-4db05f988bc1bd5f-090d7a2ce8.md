---
name: orgfuel-ORGG-4db05f988bc1bd5f-090d7a2ce8
description: "判读档判例 MACMINI_MIGRATION_PLAN_20261011 · 一、迁移范围盘点 ## 一、迁移范围盘点"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-4db05f988bc1bd5f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 MACMINI_MIGRATION_PLAN_20261011 · 一、迁移范围盘点
## 一、迁移范围盘点

### 必迁(组织核心服务)

| 服务 | 当前宿主 | 迁移复杂度 | 说明 |
|---|---|---|---|
| compass daemon(9876) | Windows 主力机 | 中 | BGE 嵌入+recall+drift,记忆文件随迁 |
| MCP server(stdio) | Windows 主力机 | 低 | mcp_server.py 纯 Python |
| hook.sh(UserPromptSubmit) | Windows 主力机 | 低 | bash 脚本,macOS 兼容 |
| 判读工作台(final_check 等) | Windows 主力机 | 低 | Python 脚本 |
| 跨框投件通道(_INBOUND) | 各框仓 | 低 | git 层面操作 |
| A100 SSH/隧道 | Windows 主力机 | 中 | paramiko/SSH config 迁移 |
| 平台信箱 key | Windows .cache | 低 | key 文件拷贝 |

### 选迁(有价值但非必需)

| 服务 | 说明 |
|---|---|
| dev.to/Discord/知乎 token | 各社媒渠道发布能力 |
| XERJ GitHub 操作 | gh CLI 认证迁移 |
| Gmail REST | 邮件渠道 |
| A100 rerank 隧道 | paramiko 脚本,已在仓 |

### 不迁(留在原位或云端)

| 服务 | 理由 |
|---|---|
| nautilus.social 静态站 | 在 cloud 服务器,独立于本机 |
| A100 训练机 | 独立远
