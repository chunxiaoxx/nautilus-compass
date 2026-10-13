---
name: orgfuel-ORGG-477087f1e0ae6c5f-9d58c45b16
description: "判读档判例 2026-06-05-gemini-query-rewrite-design · Goal ## Goal "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-477087f1e0ae6c5f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-05-gemini-query-rewrite-design · Goal
## Goal
Optionally rewrite a recall query before retrieval (expand abbreviations, add
synonyms) to lift recall on terse/ambiguous queries. Opt-in, default off →
black-box-local hot path preserved (no LLM unless explicitly enabled).
