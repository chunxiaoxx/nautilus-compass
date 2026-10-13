---
name: orgfuel-ORGG-fdef7aafb0e0034a-90e54a7266
description: "判读档判例 2026-07-31-s4-flywheel-event-log-design · Pure reducer"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-fdef7aafb0e0034a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-07-31-s4-flywheel-event-log-design · Pure reducer
## Pure reducer

Runtime state is a derived view, not a mutable source of truth. The first reducer
maps admitted `episode` events to `awaiting_verdict`. Later PRs will extend the
same pure function for linked verdict and promotion events. Given the same ordered
events, it must always return the same state.
