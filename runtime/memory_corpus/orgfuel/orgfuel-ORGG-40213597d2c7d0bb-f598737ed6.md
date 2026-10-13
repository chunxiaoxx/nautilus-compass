---
name: orgfuel-ORGG-40213597d2c7d0bb-f598737ed6
description: "判读档判例 2026-08-15-compass-dogfood-mvp-rescue-design · 3. Exis"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-40213597d2c7d0bb
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-08-15-compass-dogfood-mvp-rescue-design · 3. Existing assets to reuse
## 3. Existing assets to reuse

The MVP must reuse these assets and may not replace them:

- `gep.experience_packet.ExperiencePacket` for the atomic learning candidate;
- `gep.flywheel_event` and `gep.flywheel_log` for append-only events and
  deterministic state reduction;
- existing capsule schema and candidate-only semantics;
- C2's frozen paired-run, independent-verifier, no-retry, and fail-closed
  patterns, migrated only as narrowly required;
- the existing Compass CLI and MCP package;
- the existing local memory daemon after its Python/runtime installation is
  repaired.

The run directory is the only new durable artifact. It is a self-contained
flight recorder, not a second database or policy ledger.
