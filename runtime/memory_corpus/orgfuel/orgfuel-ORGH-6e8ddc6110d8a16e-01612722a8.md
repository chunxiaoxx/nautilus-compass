---
name: orgfuel-ORGH-6e8ddc6110d8a16e-01612722a8
description: "commit bb3f741c9e99 2026-05-21 fix(bench): Gemini Flash thin"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-6e8ddc6110d8a16e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit bb3f741c9e99 2026-05-21
fix(bench): Gemini Flash thinking-token budget + simpler deps
Two preflight findings while validating the Colab notebook locally:

1. Gemini 2.5 Flash uses internal "thinking tokens" that consume the
   max_tokens budget before any visible text is emitted. With
   max_tokens=10 (cell 8) and max_tokens=200/300 (cell 12) the model
   returns empty (finish_reason=MAX_TOKENS, no text).
   Bumped: verify cell 10 → 200, subject 300 → 800, judge 200 → 500.
   Added an assert in the verify cell so a regression is caught
   immediately, not 4h into a run.

2. Removed unused deps: FlagEmbedding + peft + datasets. The notebook
   uses sentence-transformers' CrossEncoder for bge-reranker-v2-m3 and
   downloads the dataset JSON via urlretrieve directly · neither
   FlagEm
