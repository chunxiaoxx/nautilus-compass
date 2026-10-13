---
name: orgfuel-ORGG-9b9c1f4d325f06d6-10d710acfe
description: "判读档判例 2026-06-06-compass-mcp-3agent-dogfood-design · 4. 设计骨架"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-9b9c1f4d325f06d6
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-06-compass-mcp-3agent-dogfood-design · 4. 设计骨架(方案 A)
## 4. 设计骨架(方案 A)

### B1 · MCP 工具契约固化(versioned)
把 `mcp_server.py` ~17 工具冻成 versioned 契约(`/v1/`),分组:
- **read 组**:recall · drift_check · profile · session_search · drift_history · thread_recall
- **write 组**:ingest_obs
- **poi 组**:proof_of_impact(读)· PoI 写限制(poi_writer 最小权限先例 · 只 reconcile/verdict 路写)
- **governance 组**:governance_dispatch/audit/plan/lock_check(kairos/治理用)
- **platform 组**:submit_platform_task · ingest_platform_task_result · long_task · add_worker
- **🆕 维度召回入口**:让 agent 按维度 recall 避坑语料(W6 消费面 · Phase A substrate 的消费 API)

### B2 · 鉴权 + per-agent scope(扩 `middleware/auth.py`)
现 auth.py 返回 `Tenant`(authn + quota)。**加 scope 强制**:
- 每 agent 一 token + scope 集(scope 存 compass 本地表 `compass.agent_scopes` 或 JWT clai
