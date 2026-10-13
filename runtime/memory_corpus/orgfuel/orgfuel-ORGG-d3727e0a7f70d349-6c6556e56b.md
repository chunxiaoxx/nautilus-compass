---
name: orgfuel-ORGG-d3727e0a7f70d349-6c6556e56b
description: "判读档判例 2026-07-31-s4-flywheel-event-log-design · Event envelo"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-d3727e0a7f70d349
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-07-31-s4-flywheel-event-log-design · Event envelope v1
## Event envelope v1

`FlywheelEvent` is immutable and accepts an exact allowlist of fields:

- `schema_version`: exactly `compass.flywheel.event.v1`
- `event_kind`: exactly `episode` in this PR
- `source_event_id`: stable non-empty producer identifier
- `episode_id`: stable non-empty episode identifier
- `parent_event_id`: optional lineage identifier
- `agent_id`: positive integer; booleans are rejected
- `occurred_at`: timezone-aware RFC 3339 UTC timestamp ending in `Z`
- `payload_schema`: exactly `compass.experience_packet.v0`
- `payload`: strict `ExperiencePacket` frontmatter
- `payload_hash`: `sha256:<64 lowercase hex>` over canonical payload JSON

The payload must contain `episode_id`, and it must equal the envelope's

