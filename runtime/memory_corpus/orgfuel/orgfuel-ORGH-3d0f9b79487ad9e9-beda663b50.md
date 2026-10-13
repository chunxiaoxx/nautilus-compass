---
name: orgfuel-ORGH-3d0f9b79487ad9e9-beda663b50
description: "commit fbceaa69ed2e 2026-05-21 ﻿test(v1.7.1): integration E2"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-3d0f9b79487ad9e9
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit fbceaa69ed2e 2026-05-21
﻿test(v1.7.1): integration E2E · 12 steps cross 7 subpackages · 架构融合 verified
tests/test_integration_e2e.py · ~290 LOC · end-to-end data flow audit

Verifies 7 subpackages wire correctly through realistic session lifecycle:

  ingest → drift.routing → entity_extractor → self_evolve → l1_grouper +
  l1_renderer + l1_index → l1_recall_overlay → poi_schema + poi_calculator +
  poi_emitter → cumulative_impact frontmatter mutation → drift.gate_act →
  poi_weighting boost → job_queue → skill_registry → judges (DISABLED)

ALL 12 STEPS PASS · key cross-module evidence:
  - STEP 6 PoI writes cumulative_impact=0.667 to session_a + session_b
  - STEP 9 poi_weighting re-ranks · session_a goes to TOP despite lower base cosine
    (PROVES: PoI side-effect propagates to rec
