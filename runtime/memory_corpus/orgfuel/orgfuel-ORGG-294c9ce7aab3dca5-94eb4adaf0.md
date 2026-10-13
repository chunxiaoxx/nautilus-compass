---
name: orgfuel-ORGG-294c9ce7aab3dca5-94eb4adaf0
description: "判读档判例 2026-08-15-compass-dogfood-mvp-rescue-design · 5. One "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-294c9ce7aab3dca5
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-08-15-compass-dogfood-mvp-rescue-design · 5. One append-only truth, several projections
## 5. One append-only truth, several projections

Every run writes:

```text
<run-directory>/
  plan.json
  events.sqlite3
  artifacts/
  independent_receipt.json
  report.json
```

`events.sqlite3` is the only state history and directly uses the existing
`FlywheelEventLog` immutable tables. `ExperiencePacket`, receipt, and report
are deterministic projections from bound artifacts and events. The run-local
database is the self-contained flight recorder; no global database, parallel
status file, or second journal is introduced.

The reducer must be able to recreate `report.json` from a clean process. A
report that cannot be reproduced is invalid.
