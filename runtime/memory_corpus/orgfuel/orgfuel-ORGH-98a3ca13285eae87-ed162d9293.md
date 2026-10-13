---
name: orgfuel-ORGH-98a3ca13285eae87-ed162d9293
description: "commit 6fb1de302c2c 2026-05-22 feat: #1 + #2 · Layer 2 + PoI"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-98a3ca13285eae87
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 6fb1de302c2c 2026-05-22
feat: #1 + #2 · Layer 2 + PoI boost wired to production recall + SessionEnd self-evolve trigger
After honest audit, paradigms from OV/llm-wiki2/GBrain were shipped as a
library in v2.0.0 but NOT wired into the production recall path. This
commit closes the integration loop for two of them:

#1 · recall.py:render_v02_vector_mode now invokes:
  - recall_pkg.poi_weighting.boost_top_k · re-ranks top-K by each entry's
    cumulative_impact frontmatter (LLM-free, deterministic arithmetic)
  - storage.l1_recall_overlay.collapse_to_l1 · substitutes member L0
    sessions with their L1 summary when {mem}/_l1/_l1_index.json exists
  Both are graceful NO-OPs on cold projects (no PoI events yet · no L1
  index built yet), so v0.8 path stays byte-identical for first recal
