---
name: orgfuel-ORGG-124739cdd2d1337d-81ade2e50b
description: "判读档判例 2026-05-29-compass-comprehensive-uplift-design · 3. 规划"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-124739cdd2d1337d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-05-29-compass-comprehensive-uplift-design · 3. 规划 (Planning · 并行三线 · 2-3 周)
## 3. 规划 (Planning · 并行三线 · 2-3 周)

R2 override 接受: 4 gates 超期 risk 接受。

### 3.1 Workstream 1 · 理念 · 2-3 天

| 日 | 动作 |
|---|---|
| D1 | 落 philosophy doc 到 docs/plans/ (即此 doc) · cover 北星 + 4 H 对应 + anchor 对位 + defer |
| D2 | issue 2 个 cross-agent contract: compass↔Soul role spec / compass↔V5 outcome sub spec |
| D3 | 等 contract consumer ack (Soul / V5 dialog 回写 consumed_by) · ack 完后 lock 理念 |

### 3.2 Workstream 2 · 架构 · 2 周

#### Week 1 · 并 4 件
- (a) ship L2 metamemory engine 骨架 (confidence vector + gap surface) · ~16h
- (b) PoI emitter 从 SPEC 落代码 (复用 SPEC_PROOF_OF_IMPACT) · ~10h
- (c) drift specificity 修 (target FP <5% · 现 ~90%) · ~8h
- (d) L4 cross-agent contract consumer-side scanner (修 consumed_by e
