---
name: orgfuel-ORGG-c1abce3ab28117a9-d42931fb5f
description: "判读档判例 2026-07-31-s4-flywheel-event-log-design · Storage ## S"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-c1abce3ab28117a9
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-07-31-s4-flywheel-event-log-design · Storage
## Storage

The SQLite file contains two append-only tables:

1. `flywheel_events`: accepted canonical envelopes, keyed by
   `source_event_id`, with a unique `event_hash`.
2. `flywheel_quarantine`: safe rejection receipts containing reason code,
   source identifier when safely available, and a fingerprint. Raw unknown input
   is not persisted because it may contain credentials, links, or personal data.

Writes use explicit transactions. The database is reopened in restart tests to
prove persistence. No mutable `pending/finalized/failed` column is added.
