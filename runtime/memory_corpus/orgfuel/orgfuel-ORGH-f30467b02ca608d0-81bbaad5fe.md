---
name: orgfuel-ORGH-f30467b02ca608d0-81bbaad5fe
description: "commit afb40a17b0ff 2026-07-17 feat(bmb): 试点交付包(3 题/2 模板)+ 可"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-f30467b02ca608d0
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit afb40a17b0ff 2026-07-17
feat(bmb): 试点交付包(3 题/2 模板)+ 可复用投递打包器
- make_delivery.py:合并各题目录→买方格式单一投递包(problems.csv N 行 + data/*.zip);
  硬断言答案键/溯源不进买方包(泄露即废 benchmark)
- _DELIVERY/:3 题合并,验证器复验 0 REJECT/0 WARN;买方投递=problems.csv+data/*.zip,
  _INTERNAL_provenance.json(答案+ClinVar/RefSeq accession 溯源)留内部
- DELIVERY_NOTES.md:验收证据(门+盲解唯一性+工具数)/数据真实性溯源/500 无GPU生产环境结论
