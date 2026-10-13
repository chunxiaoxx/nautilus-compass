---
name: orgfuel-ORGH-65b37b6a3d50c1b9-a85565f881
description: "工具决策记录 per_type_ci.py Compute 95% confidence intervals per q"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-65b37b6a3d50c1b9
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 per_type_ci.py
Compute 95% confidence intervals per question type for LongMemEval-S.

Reads `paper/results/experiments_20260505.csv` and applies the Wilson score
interval (preferred over normal approximation for small n and proportions
near boundary). Cross-checks with 10000-iteration nonparametric bootstrap.

Outputs a LaTeX-ready table for paper §4.3.

Run:
  python tools/per_type_ci.py
