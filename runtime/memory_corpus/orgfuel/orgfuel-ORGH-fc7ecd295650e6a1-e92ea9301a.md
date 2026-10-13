---
name: orgfuel-ORGH-fc7ecd295650e6a1-e92ea9301a
description: "commit 2b23f18a5be5 2026-05-08 paper2 §6.5: add bootstrap 95"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-fc7ecd295650e6a1
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 2b23f18a5be5 2026-05-08
paper2 §6.5: add bootstrap 95% CI for Run 2 + honesty caveat re MemOS
Run percentile bootstrap (B=10000, seed 20260507) on the 497-row
em_bge_v3_per_question.jsonl Run 2 log. Overall accuracy 47.3% with
95% CI [42.9%, 51.7%]. Saved summary to paper/results/.

Inserted into Table 1 as a new "Run 2 95% CI" row. Caption
extended with the methodology footnote.

Caption of Table 2 (vs MemOS et al.) now carries an honesty caveat:
the Run 2 lower CI bound (42.9%) is only 0.35 pts above MemOS
(42.55), so a single-run strict-significance claim is not
warranted; the 2-run mean (45.84%) provides the +3.29 pt cushion
that does support a meaningful gap, but a definitive paired test
would require sampling variance from MemOS or a matched-pair
re-run on their public artifac
