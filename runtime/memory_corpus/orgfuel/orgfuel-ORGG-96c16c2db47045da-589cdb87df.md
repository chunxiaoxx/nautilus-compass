---
name: orgfuel-ORGG-96c16c2db47045da-589cdb87df
description: "判读档判例 2026-05-29-compass-comprehensive-uplift-implementation"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-96c16c2db47045da
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-05-29-compass-comprehensive-uplift-implementation-plan · Phase 4 · 5th Bonus · 才燊 Audit Pack Adopter (Conditional)
## Phase 4 · 5th Bonus · 才燊 Audit Pack Adopter (Conditional)

Only start if Phase 1-3 gates pass + R3 time available.

### Component L · 才燊 Phase 2 块 3 Grounding

#### Task L.1: SSH 验云端活性

Run: `ssh ubuntu@43.155.195.48 'systemctl status caishen-* 2>&1 | head -10'`

If alive → proceed. If dead → punt to next cycle.

#### Task L.2: Wire compass PoI candidate to 残保金 outcome

TDD: 残保金审计 outcome 写表 → compass 订阅 → PoI candidate emit · joint with platform NAU settlement

#### Task L.3: audit_brief.md §4 evidence pack E1+E2+E3

Generate E1 (算法机制) + E2 (训练数据) + E3 (决策可解释) · binary 评判 · 3 类符合即 Gate 4 pass.

Commit each evidence file separately.

---
