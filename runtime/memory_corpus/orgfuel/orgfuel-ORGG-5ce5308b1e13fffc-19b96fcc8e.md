---
name: orgfuel-ORGG-5ce5308b1e13fffc-19b96fcc8e
description: "判读档判例 2026-07-21-v5-fuel-recall-replay · Replay Contract ## "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-5ce5308b1e13fffc
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-07-21-v5-fuel-recall-replay · Replay Contract
## Replay Contract

- `replay_status=not_run` means no recall query was executed in this task.
- `overloaded_status=not_run` means no cloud daemon or BGE path was probed in this task.
- `payload_hash` is SHA-256 over a stable string containing `trace_id`, `source_row`, `action_tag`, type, score, short problem phrase, and feedback phrase.
- This artifact is ready for a later compass recall replay task that is allowed to query cloud recall or local recall fixtures.
