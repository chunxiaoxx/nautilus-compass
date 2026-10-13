---
name: orgfuel-ORGG-9de97fcf650c8fe2-93da5cce39
description: "判读档判例 2026-06-03-p5-v14-poi-emission · Verification checklis"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-9de97fcf650c8fe2
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-03-p5-v14-poi-emission · Verification checklist (no silent "done")
## Verification checklist (no silent "done")
- [ ] Task 1–2: tests green (`pytest tests/test_v14_poi_emission_patch.py`)
- [ ] Task 3: SSH-cat shows `actor=test-poi-001` candidate line on cloud — **the gating proof**
- [ ] Task 6: local `--dry-run` shows DB tunnel works + settled=0 (honest, fuel-gated)
- [ ] Task 7: full suite green + PR open + V5 live signal sent
