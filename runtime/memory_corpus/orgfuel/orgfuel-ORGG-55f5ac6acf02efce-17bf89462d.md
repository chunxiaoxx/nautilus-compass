---
name: orgfuel-ORGG-55f5ac6acf02efce-17bf89462d
description: "判读档判例 2026-05-29-compass-comprehensive-uplift-design · 5. 测试"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-55f5ac6acf02efce
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-05-29-compass-comprehensive-uplift-design · 5. 测试 (Testing Strategy)
## 5. 测试 (Testing Strategy)

### 5.1 不放过的实测

1. **Pilot 0' 复现 + 升级** · 用 compass v3 (H1+H2+H5 active) 跑同 24 task · 看是否仍 ≈ A2 或拉开
2. **N=20 controlled · 加 4 H 维度** · ssa-like (metamemory) / contradiction-prone (drift) / cross-session (sub) / value-laden (PoI)
3. **integration test · wire 接口** · Soul engine_cycle_outcomes 写 mock event · compass 是否 24h 内 ingest
4. **regression test · byte-equal v2.0.1** · COMPASS_USE_LLM_* 全 off 时 · 行为 byte-equal 今天 baseline (Sprint 0 已 lock)

### 5.2 per-anchor 验证清单

| anchor | gate 哪条验 |
|---|---|
| #1 agent first | Gate 3 (cross-agent consumed) · Gate 4 (外部 adopter 若启) |
| #2 递归自我提升 | Gate 1 (act-on rate) · Gate 2 (recursive metric) |
| #3 反 D 维护 | metamemory layer 治掉 ssa hallu
