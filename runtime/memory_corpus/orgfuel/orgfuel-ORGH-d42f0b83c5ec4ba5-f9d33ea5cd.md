---
name: orgfuel-ORGH-d42f0b83c5ec4ba5-f9d33ea5cd
description: "commit 602a55514e94 2026-05-06 ci · skip selftest/eval_recal"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-d42f0b83c5ec4ba5
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 602a55514e94 2026-05-06
ci · skip selftest/eval_recall (need user data) · fix paper1 cite→natbib
CI Test matrix:
  · removed selftest.py (smoke against ~/.claude/projects/<proj>/memory · CI absent)
  · removed eval_recall.py (P@5 leave-one-out on user memories · CI absent)
  · kept eval_drift.py (100 hardcoded prompts · anchors-only · works on CI)

paper1 (nautilus-compass.tex):
  · sections use \citep{} / \citet{} (natbib syntax)
  · main was \usepackage{cite} (plain) · undefined \citep → 45 unresolved
  · switch to \usepackage[round]{natbib} · resolves all 10 cite keys
