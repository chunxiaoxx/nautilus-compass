---
name: orgfuel-ORGH-08efcd289086300a-eac2160932
description: "commit 145a95f98bce 2026-07-16 feat(bmb): BioMysteryBench P1"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-08efcd289086300a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 145a95f98bce 2026-07-16
feat(bmb): BioMysteryBench P1 端到端跑通 VCF→变异临床意义模板
- build_problem.py 建题管线:1 ClinVar Pathogenic(PAH/Phenylketonuria)+ 17 Benign/VUS
  干扰,全真实 GRCh38 坐标(canonical_spdi),组装匿名 VCF(剥 rsID/INFO/基因/致病性)
- solve_problem.py 盲解 QC:只读 zip,VEP+ClinVar 独立解,坐实唯一性+工具数
- P1 独立验证:bmb_validator 0 REJECT · 盲解 PAH|Phenylketonuria 致病命中唯一=1 ·
  36 次工具调用(≥10 门)· 9 干扰项同为 missense→无捷径守住难度
- 溯源 _source_manifest.json(每变异 ClinVar accession)· answer_key 不进 zip
