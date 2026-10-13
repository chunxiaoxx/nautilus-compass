---
name: orgfuel-ORGG-33f3ad3e2d1c7211-153b1ae48c
description: "判读档判例 2026-06-03-poi-central-ledger-implementation · Task 5:"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-33f3ad3e2d1c7211
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-03-poi-central-ledger-implementation · Task 5: 云端 inline helper 加 `project` 参数(patch)
## Task 5: 云端 inline helper 加 `project` 参数(patch)

横切 P0-1 契约另一端。云端 `_v14_emit_poi_candidate` 从 v14 recall 的 `project` query 参数取(V5 已传)。沿用现有 exec 契约测试模式。

**Files:**
- Modify: `ops/patch_v14_recall_poi_candidate.py`（`EMIT_HELPER` 常量 + 注入点传 project）
- Test: `tests/test_v14_poi_emission_patch.py`（已存在 · 加断言)

**Step 1: 加失败断言** — 在现有 exec 测试里断言输出行含 `"project"`,且 helper 签名为 `_v14_emit_poi_candidate(hits, query, agent_id, project)`。

**Step 2: 确认失败**

**Step 3: 实现** — `EMIT_HELPER` 签名加 `project`,写入 dict 加 `"project": project`(helper 内对 project 做同样规范化:`if ":" in project or "\\\\" in project` 则 replace);注入到 v14_recall 的调用点把 `project` 实参传进去(recall 路由已有 project 变量)。

**Step 4: 确认通过** — `python -m pyte
