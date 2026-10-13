---
name: orgfuel-ORGG-33afae00d293bde5-adaecc12c3
description: "判读档判例 2026-06-06-compass-substrate-solidification · 架构定调:固化 "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-33afae00d293bde5
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-06-compass-substrate-solidification · 架构定调:固化 = 谁提供什么(回答"是平台提供 MCP+token 吗?")
## 架构定调:固化 = 谁提供什么(回答"是平台提供 MCP+token 吗?")

**不是平台提供 compass 的 MCP 服务。** compass 已自有 MCP 服务 + 鉴权中间件。固化分工:

| 层 | 谁拥有 | 现状 |
|---|---|---|
| MCP 服务 + 工具契约(recall/ingest/drift/poi…) | **compass**(G-turf) | 已建 `mcp_server.py` ~17 工具 |
| 鉴权 + scope 强制 | **compass** | 已有 `middleware/auth.py` + `tools.read` 分组 |
| 跨机传输(token-gated TCP) | 复用 **v5 已建**(MCP-TCP-auth) | 已 land(anchor#5 不重造) |
| agent 身份 + token 签发 + 服务注册/发现 | **平台**(身份/经济 hub) | 待:平台给 v5/v7/kairos 各签 token + 公布 compass endpoint |
| 稳定部署(always-on + 监控 + 自重启) | **compass** | 部分(daemon systemd)· 待固化 |

**结论给用户**:token 鉴权机制 compass 已有;**平台的角色 = 签发 3 个 agent 的 token + 注册 compass 服务地址**,compass 验签 + 按 scope 放行。不需要平台重建一套 MCP。

---
