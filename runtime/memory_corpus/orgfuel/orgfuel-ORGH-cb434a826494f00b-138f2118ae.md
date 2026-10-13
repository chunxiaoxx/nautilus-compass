---
name: orgfuel-ORGH-cb434a826494f00b-138f2118ae
description: "commit 5cc791403c40 2026-07-17 feat(bmb): 产第4题 GALT/Galactos"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-cb434a826494f00b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 5cc791403c40 2026-07-17
feat(bmb): 产第4题 GALT/Galactosemia + 题干池扩到6句(治 #1/#4 撞车)
- 第4题 bmb_vendor_000004(VCF→变异临床意义·GALT/Galactosemia):3001 真实变异,
  独立验证=本地全扫致病唯一=1 + 远程 VEP/ClinVar 坐实答案变异 c.396C>G(p.His132Gln)Pathogenic
- 题干优化:#2 改单句疑问贴 qes1;题干池 3→6 句,id 1/2/4 各不撞(治模板化回潮)
- 4 题合并验证器 0 REJECT/0 WARN;发送包 65KB 无内部泄露;说明/网页同步
- 持续产出验证:VCF 管线换基因即出新题,本地 QC 秒验唯一性(GALT 例)
