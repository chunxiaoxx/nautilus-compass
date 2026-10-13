---
name: orgfuel-ORGH-512e33e2310f9aa5-da0457a9c6
description: "commit 20a8d351bee8 2026-05-21 ﻿feat(v1.7.1): S4 module 6 · "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-512e33e2310f9aa5
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 20a8d351bee8 2026-05-21
﻿feat(v1.7.1): S4 module 6 · recall_pkg/poi_weighting.py (S4 COMPLETE · 6/6)
NEW · nautilus_compass.recall_pkg subpackage (auxiliary recall extensions)

recall_pkg/__init__.py · subpackage marker
recall_pkg/poi_weighting.py · ~70 LOC
  - apply_poi_boost · asymptotic boost from cumulative_impact
  - boost_top_k · re-sort top-K by boosted score
  - BOOST_FACTOR_DEFAULT 0.1 · BOOST_CAP 1.0 (2x) · BOOST_FLOOR -0.5 (0.5x)
  - Graceful · missing field / corrupt value → no boost
  - NO LLM · pure arithmetic + frontmatter parse

pyproject.toml · add nautilus_compass.recall_pkg subpackage

tests/test_poi_weighting.py · 9/9 pass

S4 LAYER 4 PROOF-OF-IMPACT COMPLETE · 6/6 modules shipped this session:
  · poi_schema (97063bc) · ProofOfImpact dataclass + validators
  · p
