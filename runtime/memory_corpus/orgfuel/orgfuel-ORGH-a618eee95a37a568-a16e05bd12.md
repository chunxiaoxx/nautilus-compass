---
name: orgfuel-ORGH-a618eee95a37a568-a16e05bd12
description: "commit 23f1f5bff8ee 2026-05-06 paper §6.5 + driver · BGE+rer"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-a618eee95a37a568
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 23f1f5bff8ee 2026-05-06
paper §6.5 + driver · BGE+reranker e2e 40.0% on EverMemBench (n=100)
compass paper-grade benchmark numbers:
  recall@20     91.0%  (vs BM25 38.1% · 51pt dense+rerank uplift)
  e2e accuracy  40.0%  (vs paper baselines 34-42.55%)

Position vs paper Table 4 (GPT-4.1-mini answerer · 9-subtask Avg):
  Full Context 37.44 · MemoBase 34.27 · Mem0 37.09
  Zep 39.97 ← compass tied here
  MemOS 42.55 ← compass -2.5
  EverCore NOT REPORTED ← we filled this independently

Caveats (paper §6.5):
  - n=100 sample · ±10pt 95% CI
  - topic 01 only (vs 5-topic Average)
  - V4-flash answerer (vs GPT-4.1-mini) · not strict apples-to-apples
  - No Profile-Understanding subtask yet
  - 5-topic 2400-QA full run pending for paper-defensible ranking

Bug archeology (3 blockers found t
