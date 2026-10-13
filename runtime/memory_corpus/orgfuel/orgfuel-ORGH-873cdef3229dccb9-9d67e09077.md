---
name: orgfuel-ORGH-873cdef3229dccb9-9d67e09077
description: "commit 5750ffd11d40 2026-05-06 add EverMemBench reproducibil"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-873cdef3229dccb9
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 5750ffd11d40 2026-05-06
add EverMemBench reproducibility scripts (smoke + e2e)
evermembench_smoke.py · BM25 retrieval@K baseline
  · pulls 5 topics · 2400 QAs from EverMind-AI/EverMemBench-Dynamic HF
  · SQLite FTS5 (BM25 only · no GPU needed)
  · 17.5s for 2400 QAs on cloud
  · output (lower-bound · BM25 only):
      R@1   14.8%    R@5   25.2%
      R@10  30.6%    R@20  38.1%

evermembench_e2e.py · BM25 + DeepSeek V4-flash answerer + judge
  · mirrors paper Table 4 protocol (retrieve → answer → judge)
  · DeepSeek instead of OpenRouter (paper) · cross-judge κ 0.772 in our paper
  · BM25 lower-bound result (50 QAs · topic 01):
      recall@20  70-74%
      e2e acc      0%  (BM25 false-positive too high · LLM answers UNKNOWN)
  · expected with BGE-m3 + reranker (T4 GPU · pending V4 c
