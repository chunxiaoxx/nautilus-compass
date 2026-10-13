---
name: orgfuel-OUTR-xerj_recipe_20261004-2-e50343c9a0
description: "## Recipe 2 — Evaluation: preregistered criteria, self-repor"
metadata:
  type: reference
  source: org_fuel:outreach
  pf_id: OUTR-xerj_recipe_20261004-2
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

## Recipe 2 — Evaluation: preregistered criteria, self-report and recompute as separate artifacts

The pattern we keep re-learning, stated once compactly:

1. Freeze criteria **before** running: metric, threshold, stop-loss, and the exact verifiable artifact each claim points to. Criteria may only move *stricter* mid-stream; loosening requires a fresh preregistration.
2. Label every claim `measured` / `inferred` / `unverifiable`. Inferred claims carry an upgrade path. The most useful eval artifact we ever published was a self-report saying "2 of 4 gates FAIL on recompute" — the FAILs, kept visible, are what made the green credible afterwards.
3. **Compute a majority-class baseline before claiming accuracy.** We just watched a 0.87 binary classifier that a 0.78 always-yes baseline nearly ma
