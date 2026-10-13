---
name: orgfuel-ORGH-34a0e3fe7e559e46-8a22ef2beb
description: "commit 016afc297ef5 2026-04-29 paper: §4-§7 drafted · all te"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-34a0e3fe7e559e46
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 016afc297ef5 2026-04-29
paper: §4-§7 drafted · all text complete · figures TBD
§4 Evaluation (~1500 words):
  4.1 Setup (synthetic 50/50 + LongMemEval-S subset 12)
  4.2 Drift four-step ablation table (key narrative · 0.51→0.92)
  4.3 Cross-encoder null result (Δ AUC +0.0008 @ 36x latency)
  4.4 LongMemEval-S retrieval table (zenmind-mem vs mem0 vs no-rerank)
  4.5 Per-type breakdown (single-session-user 5x lift)
  4.6 mem0 head-to-head (P@5 tied · MRR +0.122)
  4.7 Local recall sanity check
  4.8 Latency table

§5 Discussion (~900 words):
  5.1 Anchor design as dominant variable
  5.2 Black-box vs white-box complementarity (Persona Vectors)
  5.3 Why reranker helps retrieval but not drift
  5.4 The subset 4 vs subset 12 lesson (don't conclude from n=4)
  5.5 Active learning in prac
