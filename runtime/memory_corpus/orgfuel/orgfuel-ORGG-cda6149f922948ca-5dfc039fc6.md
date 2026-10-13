---
name: orgfuel-ORGG-cda6149f922948ca-5dfc039fc6
description: "判读档判例 2026-05-29-compass-comprehensive-uplift-implementation"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-cda6149f922948ca
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-05-29-compass-comprehensive-uplift-implementation-plan · Phase 0 · Pre-flight Verification (D1 · 2h)
## Phase 0 · Pre-flight Verification (D1 · 2h)

### Task 0.1: Confirm Sprint 0 baseline still reproducible

**Files:**
- Read: `paper/baseline_v201_sprint0.json`
- Read: `paper/results/longmemeval_v201_summary_1780056202.json`

**Step 1:** Verify json valid + completeness 5/5

Run: `python -c "import json; d=json.load(open('paper/baseline_v201_sprint0.json',encoding='utf-8')); assert d['_meta']['completeness'].startswith('5/5'); print('OK')"`
Expected: `OK`

**Step 2:** Confirm v3-full-fusion HEAD includes design doc commit

Run: `git log --oneline -3`
Expected: `faf2a09 docs(plan): compass v3 全方位提升 design` at HEAD

**Step 3:** No commit (verification only)

---
