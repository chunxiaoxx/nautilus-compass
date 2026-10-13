---
name: orgfuel-ORGG-68b885b0ad0980d9-d41d4a4196
description: "判读档判例 2026-07-21-v5-fuel-recall-replay · Next Execution Gate"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-68b885b0ad0980d9
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-07-21-v5-fuel-recall-replay · Next Execution Gate
## Next Execution Gate

The next compass-side runner should update each row to one of:

- `hit`: recall returned an expected matching payload.
- `miss`: recall ran but did not return the payload.
- `blocked_overloaded`: recall path returned daemon overload.
- `blocked_missing_payload`: payload was not available for indexing or replay.
- `blocked_not_indexed`: payload exists but BGE/backfill status is not complete.
