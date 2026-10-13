---
name: orgfuel-ORGH-65371ce437aa7601-89cde9cc9a
description: "commit e1cb1b8be50c 2026-06-21 doc(verdict): 难倒门pass vs 解对pa"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-65371ce437aa7601
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit e1cb1b8be50c 2026-06-21
doc(verdict): 难倒门pass vs 解对pass 口径备忘 — bvh_001已订正·6条不动
齿轮③语义混根因文档化。实测:真bug仅bvh_001(score=0却pass=t·已UPDATE→f)。
6条阈值候选各有正当语义(3难倒门+3解对)不mutate。未来ingest守卫给soul
(verdict_kind分流+solver路径score=0强制f)。compass对fde_verdicts只读不重造写入器。
