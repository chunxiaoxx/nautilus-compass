---
name: orgfuel-ORGG-1c475a282d8b443f-17e44af070
description: "判读档判例 2026-07-31-s4-flywheel-event-log-design · Security and"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-1c475a282d8b443f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-07-31-s4-flywheel-event-log-design · Security and trust boundary
## Security and trust boundary

An action-producing agent may submit an episode, but it cannot assign its own
verdict, PoI, capsule promotion, or routing preference. `capsule_candidate` remains
an observation-level hint only; independent later gates decide promotion.

Physical verification will be treated as strong external evidence, not infallible
truth. Sensor, calibration, verifier-version, and environment lineage belong in
later verdict events.
