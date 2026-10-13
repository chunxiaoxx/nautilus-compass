---
name: orgfuel-ORGH-ee79ac28a2b929e6-7a515a2c16
description: "工具决策记录 rejudge_errors.py Re-judge the 71 judge-disconnect qu"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-ee79ac28a2b929e6
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 rejudge_errors.py
Re-judge the 71 judge-disconnect questions (task #40).

Same judge model & prompt as the arm-a runs (imported from the harness, not
reimplemented) so the verdict stays in-protocol; only adds retry with backoff,
because the original failures were connection-layer (403/timeout), not model
verdicts. Answers are reused verbatim -- subjects are NOT re-run.

Writes vtf/_e2e_diag/arm_a_rows_rejudged.json + prints recomputed by-type.
