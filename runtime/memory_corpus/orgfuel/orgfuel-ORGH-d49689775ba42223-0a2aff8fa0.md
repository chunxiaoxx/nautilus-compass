---
name: orgfuel-ORGH-d49689775ba42223-0a2aff8fa0
description: "commit b095cb59e47f 2026-04-30 paper: full 500 reranker re-e"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-d49689775ba42223
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit b095cb59e47f 2026-04-30
paper: full 500 reranker re-eval lands · upgrade primary benchmark
GPU run on GTX 1060 6GB · 67 min wall clock · 23x speedup over CPU.

Headline result (full 500):
· bge-m3 + bge-reranker-v2-m3:  P@1=0.802 · P@5=0.920 · MRR=0.855
· bi-encoder only baseline:      P@1=0.576 · P@5=0.860 · MRR=0.685
· Δ from reranker:               +0.226 / +0.060 / +0.170

Per-type lift on full 500 (largest gains on hardest types):
· single-session-preference  MRR 0.537 → 0.788  (+0.251)
· knowledge-update           MRR 0.635 → 0.848  (+0.213)
· single-session-user        MRR 0.398 → 0.586  (+0.188)
· temporal-reasoning         MRR 0.730 → 0.914  (+0.184)
· multi-session              MRR 0.741 → 0.920  (+0.179)
· single-session-assistant   MRR 0.950 → 0.939  (-0.011 · ceiling)


