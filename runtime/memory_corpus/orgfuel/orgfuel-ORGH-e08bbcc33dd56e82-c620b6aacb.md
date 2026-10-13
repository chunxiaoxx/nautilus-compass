---
name: orgfuel-ORGH-e08bbcc33dd56e82-c620b6aacb
description: "commit 4ca132a9ae01 2026-05-08 docs(zh): sync comparison tab"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-e08bbcc33dd56e82
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 4ca132a9ae01 2026-05-08
docs(zh): sync comparison table with English · add MemOS + Smriti rows
Chinese comparison table was stale:
- still claimed AUC 0.92 (in-set only) — replaced with 0.83 held-out
  to match the honest number used in English README + paper
- added MemOS row (EM 42.55) — top of reported Table 4 baselines, was
  missing
- added Smriti row with explicit out-of-scope note (team archive +
  git share, not a runtime memory layer)
- collapsed retrieval column to show LongMemEval + EverMemBench numbers
  side by side (44.4-47.3% e2e + 56.6%) instead of the stale MRR 0.84
