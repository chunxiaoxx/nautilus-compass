---
name: orgfuel-ORGH-bad90b53bd615d2d-0eb36da236
description: "commit 01cd2fd94763 2026-06-06 feat(fde): Phase A substrate "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-bad90b53bd615d2d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 01cd2fd94763 2026-06-06
feat(fde): Phase A substrate — W6 avoidance corpus + dimension PoI from bus (#40)
* feat(fde): batch avoidance-corpus build driver (W6 substrate · A1)

load_fde_tasks picks latest verdict per task (filename-token fallback for
verdicts without task_uid · UTF-8 CJK); build_corpus feeds injected vtf capsule
callables through the dimension flywheel. Real 6-task build verified: c4/c5
avoidance lines present, cross-task accumulation, recall surfaces dim atoms
(隐私 query → hallucination-control top). 5 tests green. NO LLM.

* feat(fde): dimension PoI auto-driven from verdict-bus (Option C · A2)

credit_dimensions_from_bus joins each bus verdict to its local
<task_uid>_checklist.json by task_uid and runs credit_dimensions_from_verdict
(passed item → +score on mapped d
