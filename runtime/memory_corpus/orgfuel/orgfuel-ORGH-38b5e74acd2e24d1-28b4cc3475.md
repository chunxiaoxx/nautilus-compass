---
name: orgfuel-ORGH-38b5e74acd2e24d1-28b4cc3475
description: "commit f3131f95db4d 2026-04-30 paper: upgrade LongMemEval-S "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-38b5e74acd2e24d1
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit f3131f95db4d 2026-04-30
paper: upgrade LongMemEval-S to full 500 (primary benchmark)
Final numbers (bge-m3 bi-encoder, no reranker, n=500, 169 min CPU):
· P@1 = 0.576 · P@3 = 0.726 · P@5 = 0.860 · MRR = 0.685

By question_type:
· single-session-assistant n=56  · MRR=0.950 (near ceiling)
· multi-session            n=133 · MRR=0.741
· temporal-reasoning       n=133 · MRR=0.730
· knowledge-update         n=78  · MRR=0.635
· single-session-preference n=30 · MRR=0.537
· single-session-user      n=70  · MRR=0.398 (hardest type)

Honest framing in §4.4:
· subset-12 P@5=0.750 vs full-500 P@5=0.860 → P@5 went UP (+0.110)
· subset-12 MRR=0.732 vs full-500 MRR=0.685 → MRR went DOWN (-0.047)
· explained by 70 single-session-user questions (14% of full · MRR=0.40)
  underrepresented in balanced 
