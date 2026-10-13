---
name: orgfuel-ORGH-83573037de89334a-3ea5ac2d80
description: "commit 18d2d64ff59a 2026-05-21 ﻿feat(v1.7.1): S4 module 2 · "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-83573037de89334a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 18d2d64ff59a 2026-05-21
﻿feat(v1.7.1): S4 module 2 · proof/poi_calculator.py · deterministic impact formula
proof/poi_calculator.py · ~75 LOC
  - OUTCOME_WEIGHT table (success +1.0 / partial +0.5 / failure -0.5 / pending 0)
  - cite_factor(n) = min(1.0, n/3) · spread credit across cites
  - drift_penalty_from_paths · reads drift field from cited memory frontmatter
    · all green/none → 1.0 · any yellow → 0.5 · any red → 0.1
  - compute_impact_score · pure arithmetic · writes back to poi.impact_score
  - compute_with_drift · convenience wrapper · drift+score
  - NO LLM · all formulas verbatim from SPEC

proof/l1_grouper_compat.py · ~20 LOC shim
  - Reuses storage.l1_grouper.parse_session_frontmatter
  - Try relative + absolute imports · graceful

tests/test_poi_calculator.py · 10/10
