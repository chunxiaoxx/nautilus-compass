---
name: orgfuel-ORGG-822ee1661cef1e19-dbdf479f9d
description: "判读档判例 2026-07-31-s4-flywheel-event-log-design · Goal ## Goal"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-822ee1661cef1e19
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-07-31-s4-flywheel-event-log-design · Goal
## Goal

Turn `ExperiencePacket` into the first durable input of the Compass S4 external
post-training flywheel without building a mutable workflow engine. The runtime
boundary is one strict, immutable event protocol. Every later stage will emit a
new linked event instead of editing earlier experience.

This change implements only `episode` admission. Verdict, policy preference,
capsule, and replay events are later PRs.
