---
name: orgfuel-ORGG-c4e35b888f278be2-d167be964f
description: "判读档判例 2026-07-31-s4-flywheel-event-log-design · Admission an"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-c4e35b888f278be2
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-07-31-s4-flywheel-event-log-design · Admission and idempotency
## Admission and idempotency

`CompassS4AgentHarness` is a thin deterministic adapter around `FlywheelEventLog`.
It receives structured mappings from registered runtimes and never imports chat,
Codex, Claude, Feishu, or robot SDK code.

Admission returns an immutable receipt with one of four statuses:

- `accepted`: a new valid event was appended
- `duplicate`: the same `source_event_id` and `event_hash` already exist
- `conflict`: the same `source_event_id` refers to different content
- `quarantined`: schema, hash, timestamp, payload, or agent registration failed

The log receives a set of registered integer agent IDs from its caller. It does
not create another agent registry. Replaying a valid event is idempotent; 
