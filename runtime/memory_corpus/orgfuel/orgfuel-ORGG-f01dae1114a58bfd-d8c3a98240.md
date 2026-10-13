---
name: orgfuel-ORGG-f01dae1114a58bfd-d8c3a98240
description: "判读档判例 2026-06-04-poi-writer-role-tightening-design · Testing"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-f01dae1114a58bfd
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-04-poi-writer-role-tightening-design · Testing (TDD, sqlite mock)
## Testing (TDD, sqlite mock)

Role split lives at the connection layer; sqlite cannot exercise GRANT/REVOKE.
Unit coverage:

- `parse_secret` reads the poi_writer secret;
- missing writer secret → honest skip (no crash, returns 0);
- write conn absent / connect failure → does not crash, honest skip;
- read/write responsibility split: with two mock connections, assert
  `agent_tool_calls` queries only hit the read conn and the `poi_credit` UPSERT
  only hits the write conn.

GRANT/REVOKE and the negative permission test are validated by cloud e2e, not
unit tests.
