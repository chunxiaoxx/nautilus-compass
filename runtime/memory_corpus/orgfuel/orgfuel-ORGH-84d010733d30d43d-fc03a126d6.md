---
name: orgfuel-ORGH-84d010733d30d43d-fc03a126d6
description: "commit 07dc715d3c94 2026-05-06 paper §6.5 cross-benchmark on"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-84d010733d30d43d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 07dc715d3c94 2026-05-06
paper §6.5 cross-benchmark on EverMemBench (draft)
189 LOC · evidence-driven · 4 tables · 6 subsections:
  · An anomaly worth surfacing (EverCore omission)
  · Protocol (Add→Search→Answer→Evaluate · matches paper)
  · Results: BM25 lower bound 14.8/25.2/30.6/38.1
  · End-to-end preliminary + what we cannot yet claim
  · Self-criticism (30-QA smoke 70% → 488-QA 36.5% · 33pt swing)
  · Differentiation summary (SaaS vs 100% local)

Honest claims only:
  · No "compass beats X" until BGE-m3 + reranker numbers in
  · 30-QA smoke walked back as over-optimistic
  · BM25 e2e 0% acknowledged (false-positive heavy · LLM correctly UNKNOWNs)
  · v1.1 update planned with full retrieval stack on T4

Cite-ready blocks:
  · Hu et al. 2026 (arxiv 2602.01313) for EverMemBench
 
