---
name: orgfuel-ORGG-55c0e49cdf86d83f-ede012622d
description: "判读档判例 2026-06-05-fde-rsi-dual-flywheel-closure · Phase 3 · 缺"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-55c0e49cdf86d83f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-05-fde-rsi-dual-flywheel-closure · Phase 3 · 缺口3:FDE verdict→PoI adapter(双轮咬合·接 soul verdict 流)
## Phase 3 · 缺口3:FDE verdict→PoI adapter(双轮咬合·接 soul verdict 流)

> 大纲(待 soul checklist_scorer 真实 verdict 流稳定后细化)。
- Task 3.1: 定义 FDE outcome schema(checklist 通过率 + 专家复核结论 → poi outcome),映射 `proof/poi_reconciler.py:37-44` 的 success/failure/pending。
- Task 3.2: adapter 把 FDE verdict 写 `agent_tool_calls` 兼容形态(或直接 upsert `compass.poi_credit`),复用 `proof/poi_credit_store.py:18`。TDD:mock verdict→credit。
- Task 3.3: 云端开 `COMPASS_CLOUD_POI_BOOST=1`,验 credited memory 召回被 boost。
- 边界:FDE 外部信号,不碰平台内部 RSI。
