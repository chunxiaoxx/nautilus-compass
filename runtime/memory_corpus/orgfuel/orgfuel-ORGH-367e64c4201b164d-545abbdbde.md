---
name: orgfuel-ORGH-367e64c4201b164d-545abbdbde
description: "commit d26ef9ec3f30 2026-05-13 feat(eval): ZMM_SUBJECT_TEMPE"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-367e64c4201b164d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit d26ef9ec3f30 2026-05-13
feat(eval): ZMM_SUBJECT_TEMPERATURE env gate · prep Gate48 Run C'
closes #149 · prep for #36:

· call_vertex_gemini gains temperature param (default 0.1 · byte-identical
  to pre-gate behavior for judge + any legacy caller)
· subject call at line 318 passes SUBJECT_TEMPERATURE (judge stays 0.1 ·
  only subject diversifies for self-consistency vote)
· ZMM_SUBJECT_TEMPERATURE env (default 0.1 · Run C' uses 0.7)
· summary json records subject_temperature + vote_n for audit trail
· startup print echoes subject temp + reminder judge stays 0.1

Run C' command:
  ZMM_VOTE=3 ZMM_SUBJECT_TEMPERATURE=0.7 python tests/eval_longmemeval_accuracy.py --subset 48

hypothesis from paper2 §4.6: flash at temp=0.1 deterministic · 3-sample
vote collapsed to single answer · vote g
