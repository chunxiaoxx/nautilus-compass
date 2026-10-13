---
name: orgfuel-ORGG-0287b47b28efdb42-10b40f675a
description: "判读档判例 2026-06-05-gemini-query-rewrite-design · Architecture "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-0287b47b28efdb42
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-05-gemini-query-rewrite-design · Architecture
## Architecture
New module `query_rewrite.py` isolates ALL LLM contact:
```
rewrite_query(query: str) -> str
  · flag off                → return query unchanged (byte-identical default)
  · flag on, gemini ok      → return rewritten query
  · flag on, gemini None/err → return ORIGINAL query (recall never degraded/broken)
```
- Flag: `query_rewrite` in `llm_opt_in.py`, env `COMPASS_PROD_QUERY_REWRITE`.
  Effective only when the gemini provider is also enabled
  (`COMPASS_USE_GEMINI_FLASH`); if the provider is off, `rewrite_query` is a
  no-op (defense: never silently require an LLM the user didn't enable).
- Prompt (low temperature, short): "Rewrite this memory-search query to maximize
  retrieval recall: expand abbreviations, add
