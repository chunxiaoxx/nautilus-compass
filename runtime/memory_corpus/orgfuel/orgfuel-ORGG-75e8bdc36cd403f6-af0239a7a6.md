---
name: orgfuel-ORGG-75e8bdc36cd403f6-af0239a7a6
description: "判读档判例 2026-07-31-s4-flywheel-event-log-design · Acceptance #"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-75e8bdc36cd403f6
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-07-31-s4-flywheel-event-log-design · Acceptance
## Acceptance

- Replaying one valid event 100 times produces one accepted row.
- Reopening the database preserves canonical bytes, hashes, and derived state.
- Same source ID with different content cannot overwrite the original.
- Invalid, hash-mismatched, and unregistered events leave safe quarantine receipts.
- A one-shot harness fixture completes without chat/runtime framework imports.
- Focused GEP tests, full GEP tests, Ruff, and `git diff --check` pass.
