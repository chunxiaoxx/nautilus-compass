---
name: orgfuel-ORGG-ed07abd60797e569-ba075534f3
description: "判读档判例 2026-06-06-compass-substrate-solidification · Phase B "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-ed07abd60797e569
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-06-compass-substrate-solidification · Phase B · MCP 服务固化 + 3-agent dogfood(先 brainstorming · 需跨框)
## Phase B · MCP 服务固化 + 3-agent dogfood(先 brainstorming · 需跨框)

> **不直接 ship。** 先 superpowers:brainstorming 探 3-agent(v5/v7/kairos)各自 scope 与用例,再 writing-plans 细化。下面是设计骨架。

### B1 · MCP 工具契约固化(versioned)
- 把 `mcp_server.py` ~17 工具冻成 versioned 契约(read 组:recall/drift_check/profile/session_search/drift_history;write 组:ingest_obs;poi 组:proof_of_impact)。
- **新增维度召回入口**:让 agent 能按维度 recall 避坑语料(W6 消费面)。

### B2 · 鉴权 + per-agent scope(复用 `middleware/auth.py`)
- 每 agent 一 token + scope:
  - **三者通用**:recall / drift_check / profile(read)。
  - **v5**(nautilus-prime-001 · FDE producer):ingest_obs(写 FDE 知识)+ 维度避坑 recall(W6)。
  - **kairos**(drift/monitor):drift_history / drift_check 重度。
  - **
