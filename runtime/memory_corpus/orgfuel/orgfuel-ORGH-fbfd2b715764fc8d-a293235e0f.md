---
name: orgfuel-ORGH-fbfd2b715764fc8d-a293235e0f
description: "commit 5ba5829b1266 2026-06-24 merge(mcp): durable transport"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-fbfd2b715764fc8d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 5ba5829b1266 2026-06-24
merge(mcp): durable transport layer (EventStore + Last-Event-ID resume + watchdog) into v2.3.0
11 commits · 6-task TDD · two-stage review per task · 1062-test full suite green.
EventStore ring buffer (thread-safe) → server _eid tagging → session-scoped registry
+ Last-Event-ID resume → bridge replay → watchdog heartbeat → E2E zero-loss proof.
