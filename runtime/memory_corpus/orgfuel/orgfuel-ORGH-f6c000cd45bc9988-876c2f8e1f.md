---
name: orgfuel-ORGH-f6c000cd45bc9988-876c2f8e1f
description: "commit 8d100f733b63 2026-05-21 ﻿feat(v1.7.1): S5 · drift/rou"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-f6c000cd45bc9988
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 8d100f733b63 2026-05-21
﻿feat(v1.7.1): S5 · drift/routing.py · drift-as-routing (Layer 1 COMPLETE)
drift/routing.py · ~145 LOC
  - infer_route · label or score-based classification (green/yellow/red)
  - route_target_dir · maps route to _quarantine/_warning/canonical dirs
  - is_recall_eligible · green always · yellow with caveat · red opt-in only
  - route_entry · dry-run or apply_move (filesystem rename)
  - log_routing_decision · _routing_log.jsonl audit trail
  - filter_eligible · post-recall filter for red/yellow exclusion
  - SCORE_RED_BELOW = -0.04 (matches anchor R1 drift alert threshold)
  - NO LLM · pure rule-based classification

tests/test_drift_routing.py · 11/11 pass

Refs: paper/COMPASS_V2_SPEC_DRAFT.md Layer 1 verify criteria
Next: S6 L2 nightly Ollama dream-layer (h
