---
name: orgfuel-ORGH-02debab0cef9146a-83f40b75dd
description: "commit 351b0869be43 2026-04-29 paper: Section 2 (Related Wor"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-02debab0cef9146a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 351b0869be43 2026-04-29
paper: Section 2 (Related Work) + Section 3 (Method) drafted
§2 Related Work (~750 words):
  - Memory plugins (mem0, Letta, Zep, A-MEM) - retrieval-only assumption
  - White-box persona monitoring (Persona Vectors disambiguation)
  - Cross-encoders (bge-reranker-v2-m3) + null result preview
  - Long-context benchmarks (LongMemEval, LoCoMo, PerLTQA)
  - Anchor-based behavior detection analogies (RLHF, BC, ICL)
  - Strategy distillation (DPT-Agent)

§3 Method (~1300 words):
  - 3.1 Architecture: hook lifecycle + BGE daemon
  - 3.2 Anchor schema (weighted, backwards compat)
  - 3.3 Drift scoring formula (weighted top-k mean cosine)
  - 3.4 Tri-band output (aligned/neutral/deviation thresholds)
  - 3.5 Four-step methodology evolution (key narrative, AUC 0.51→0.92
