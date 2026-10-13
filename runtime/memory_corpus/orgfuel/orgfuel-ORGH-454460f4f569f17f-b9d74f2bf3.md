---
name: orgfuel-ORGH-454460f4f569f17f-b9d74f2bf3
description: "commit cf2cbfdde8d0 2026-05-21 ﻿feat(v1.7.1): gap fix 3 · st"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-454460f4f569f17f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit cf2cbfdde8d0 2026-05-21
﻿feat(v1.7.1): gap fix 3 · storage/self_evolve.py · OV self-evolving session-end pipeline
storage/self_evolve.py · ~145 LOC
  - recent_sessions · lookback window (default 24h)
  - count_ungrouped · sessions not yet in _l1_index.json
  - scan_entity_links · aggregated entity ref stats (reuses entity_extractor)
  - trigger_l1_build_if_due · threshold gate (>=3 ungrouped → invoke L1 pipeline)
  - log_evolve_event · sidecar JSONL audit trail
  - evolve_at_session_end · main orchestrator · idempotent
  - REUSES l1_grouper + l1_renderer + l1_index + entity_extractor
  - NO LLM · pure filesystem + JSON

OV reference verbatim: "At the end of each session, developers can actively
trigger the memory extraction mechanism. The system will asynchronously analyze
task exec
