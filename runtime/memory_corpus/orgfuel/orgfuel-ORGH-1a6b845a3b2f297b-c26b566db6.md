---
name: orgfuel-ORGH-1a6b845a3b2f297b-c26b566db6
description: "commit f0598244f16d 2026-04-29 paper: 5 figures + LaTeX wiri"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-1a6b845a3b2f297b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit f0598244f16d 2026-04-29
paper: 5 figures + LaTeX wiring + GitHub Actions auto-build
Figures (matplotlib · all in paper/figures/):
  fig1_architecture.pdf      - hook lifecycle + 3-path injection diagram
  fig2_auc_evolution.pdf     - HERO: 4-step AUC line chart 0.51 → 0.92
  fig3_longmemeval_pertype.pdf - zenmind vs mem0 per-type bar chart
  fig4_drift_histogram.pdf   - aligned vs deviation score distribution
  fig5_rerank_lift.pdf       - reranker MRR lift by question type

Wired into LaTeX:
  §1 intro references fig2 (AUC evolution)
  §3.1 references fig1 (architecture)
  §4.2 references fig4 (drift histogram)
  §4.4 references fig3 (per-type), fig5 (rerank lift)

Build infra:
  paper/BUILD.md - 3 build options (Overleaf / local LaTeX / GitHub Actions)
  .github/workflows/build-pa
