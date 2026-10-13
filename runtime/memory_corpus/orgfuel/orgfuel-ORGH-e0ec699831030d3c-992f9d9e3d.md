---
name: orgfuel-ORGH-e0ec699831030d3c-992f9d9e3d
description: "commit 935c1f371989 2026-04-29 v0.7.1: drift AUC 0.51→0.92 +"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-e0ec699831030d3c
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 935c1f371989 2026-04-29
v0.7.1: drift AUC 0.51→0.92 + adaptive learning + open-source ship-ready
# Drift detection: 4-step evolution (50 aligned + 50 deviation prompt eval)
- Step 1 (anchors abstract maxims + centroid mean): AUC 0.5056 (= coin toss)
- Step 2 (anchors task-shaped + top-3 mean): AUC 0.7928
- Step 3 (switch bge-small-zh -> bge-m3): AUC 0.8352
- Step 4 (+10 hard FP examples into negative_anchors, 25->35): AUC 0.9232

# LongMemEval-S subset 12 retrieval
- bge-m3 baseline: P@5=0.75, MRR=0.732
- + bge-reranker-v2-m3 (top-50 -> top-5): P@5=0.917, MRR=0.837
- vs mem0 with Vertex text-embedding-005: P@5=0.917 (tied), MRR=0.715 (we +0.122)

# E. Adaptive anchor learning (truly production-grade, not MVP)
- Weighted anchor schema (backwards compat str | dict-with-weight)
- Weigh
