---
name: orgfuel-ORGH-790dcec68897fb6b-c861ce5808
description: "commit 5a540c695153 2026-05-08 paper2: report EverMemBench R"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-790dcec68897fb6b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 5a540c695153 2026-05-08
paper2: report EverMemBench Run 1 (44.4%) + Run 2 (47.3%) honestly
Replace single-run 44.4% headline with both independent identical-pipeline
runs and an explicit cross-run mean. Run 2 (2026-05-08, n=497) hit 47.3%
acc / 98.2% recall@30; 3 questions skipped from topic 04 due to transient
DeepSeek API 5xx errors. Both endpoints sit above all four reported
Table 4 baselines; we report the lower (44.4%) as the abstract headline
to avoid cherry-picking.

§6.5 table changed from 5x3 (single run) to 5x4 (both runs side-by-side
plus Mean and Range rows). Comparison table against MemOS et al. now
shows compass Run 1, Run 2, and 2-run mean (45.84%, +3.3 pts above MemOS).
Abstract updated with the same honest range.
