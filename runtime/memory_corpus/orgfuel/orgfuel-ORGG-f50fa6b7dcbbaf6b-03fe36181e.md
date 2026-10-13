---
name: orgfuel-ORGG-f50fa6b7dcbbaf6b-03fe36181e
description: "判读档判例 2026-06-05-gemini-query-rewrite-design · Build on exis"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-f50fa6b7dcbbaf6b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-05-gemini-query-rewrite-design · Build on existing infra (not reinvent · anchor #5)
## Build on existing infra (not reinvent · anchor #5)
- `judges/gemini_flash.py` `GeminiFlashJudge.generate(prompt) -> str|None` —
  complete lazy opt-in Gemini 2.5 Flash provider (Vertex SA, returns None on any
  failure). Reused for the rewrite call.
- `llm_opt_in.py` — flag registry (`OptInFlag`, `is_enabled(flag)` per-call).
  Add a `query_rewrite` flag.
