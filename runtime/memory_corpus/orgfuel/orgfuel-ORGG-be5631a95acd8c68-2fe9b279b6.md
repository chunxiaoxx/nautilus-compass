---
name: orgfuel-ORGG-be5631a95acd8c68-2fe9b279b6
description: "判读档判例 2026-06-05-fde-rsi-dual-flywheel-closure · Phase 2 · 缺"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-be5631a95acd8c68
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-05-fde-rsi-dual-flywheel-closure · Phase 2 · 缺口1:跨设备 ingest 修(小·解跨设备原文召回)
## Phase 2 · 缺口1:跨设备 ingest 修(小·解跨设备原文召回)

### Task 2.1: 云端实测确认 bug(先证实再修)
**Files:** Read `ops/v0.9_to_v14_adapter_patch.py:187-216`、`daemon.py:1092,982`。
**Step 1:** 对云端 `/v1/v14/ingest_obs` POST 一条测试 obs(带 `content` 字段),再 recall 它,确认是否召回得到。
**Step 2:** 记录结果:若召回不到=证实静默失败(`ingest_obs+content` vs daemon `ingest+text` 不匹配)。写进 notes。
**Gate:** 若云端能召回 → daemon 是别的构建,bug 不存在,跳过 Phase 2,只记差异。

### Task 2.2: 对齐 action/字段(TDD)
**Files:** Modify `ops/v0.9_to_v14_adapter_patch.py` 或 `daemon.py:1092` · Test: `tests/test_ingest_obs_route.py`(create)。
**Step 1:** 失败测试:`action="ingest_obs"`+`content` 经分发能命中 `handle_ingest` 并写入。
**Step 2:** 跑 → FAIL。
**Step 3:** 二选一(看 Task 2.1):adapter 把 `ingest_obs→ingest`+`content→
