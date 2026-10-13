---
name: orgfuel-ORGD-aa587636a068e349-cd9b6365d0
description: "[## 0c. anchor#5 复用盘点(别从零造 · 2026-06-21)] - 🔴 **平台已有(烂尾)A2A+"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-aa587636a068e349
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 0c. anchor#5 复用盘点(别从零造 · 2026-06-21)] - 🔴 **平台已有(烂尾)A2A+MCP 服务端**(用户提示·实测定位):git worktree `agent-a2152bb850d8d40bc`(**未合主干 = 烂尾**·最后活动 2026-05-03 ~7 周前)。
- 代码 ~1021 行:`phase3/backend/api/a2a.py`(227)+ `a2a_relay.py`(145)+ `services/a2a_protocol.py`(309)+ `nautilus_agent/connectors/mcp_connector.py`(340)。
- 文档:`docs/a2a-mcp-architecture-analysis.md`(A2A=协调层:能力广告/任务分解/状态同步/结果聚合;MCP=上下文层:工具定义/发现/注入;production 架构图 Control Plane + A2A Relay;基于 Nautilus↔Kairos 真实交互的运营洞察)+ A2A_PROTOCOL/A2A_VS_MCP 等多份。
- → **对外 A2A+MCP 不从零造**。下个 session 设计先评估:① 这资产能否接续/复用(代码 7 周新鲜度)② 烂尾根因(优先级转 FDE/RSI?技术债?未接通?)是否可解 ③ 与 compass serving 现有 A2A(`/a2a/messages`+agent.json·**LIVE**)的关系 —— 很可能**互补**:平台的是 agent 协调层(任务分发),compass 的是记忆胶囊层。两层叠加正好是目标"A2A+MCP 融合"。
- **soul auto-mint 飞轮**(2026-06-21 入站):soul 正建 auto-mint t
