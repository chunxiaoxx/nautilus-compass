---
name: orgfuel-ORGH-57839c79ce02f01f-7d41a3ecb4
description: "commit 2209df9ef509 2026-06-06 feat(recall): opt-in gemini q"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-57839c79ce02f01f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 2209df9ef509 2026-06-06
feat(recall): opt-in gemini query-rewrite (COMPASS_PROD_QUERY_REWRITE) (#38)
* docs(design): gemini query-rewrite · opt-in recall enhancement

Reuse judges/gemini_flash.py provider + llm_opt_in flag registry. New
query_rewrite.py isolates LLM; rewrite_query() = identity when flag off / on
gemini failure (recall never broken). Hook in daemon recall behind
COMPASS_PROD_QUERY_REWRITE. Default off = black-box hot path preserved.

* feat(recall): opt-in gemini query-rewrite behind COMPASS_PROD_QUERY_REWRITE

Reuses judges/gemini_flash.py provider + llm_opt_in flag registry (anchor #5).
- query_rewrite.py: rewrite_query() isolates ALL LLM contact; identity when flag
  off / provider off / gemini None/empty/over-long/exception (recall never broken)
- llm_opt_in: reg
