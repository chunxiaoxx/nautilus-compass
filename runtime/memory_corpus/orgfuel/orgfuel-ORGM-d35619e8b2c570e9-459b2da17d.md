---
name: orgfuel-ORGM-d35619e8b2c570e9-459b2da17d
description: "记忆条目 session_20260716_biomysterybench_P1_pipeline.md # BioMy"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-d35619e8b2c570e9
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 session_20260716_biomysterybench_P1_pipeline.md
# BioMysteryBench P1 端到端跑通(2026-07-16)

承接 [[session_20260716_biomysterybench_scaffold]](脚手架+验证器+500设计)。P1 = 证 1 模板端到端,**不铺量**。

## 成果(独立验证非自报 · commit 5da3719)
`vtf/fde_benchmarks/biomysterybench/` 下新增 `build_problem.py` + `solve_problem.py` + `_P1_out/`(问题+溯源)。
- 题 `bmb_vendor_000001` = **VCF→变异临床意义**模板:1 个隐藏 ClinVar Pathogenic 变异(**PAH / Phenylketonuria**)+ 17 个 Benign/VUS 干扰,全部真实 ClinVar 记录 + 真实 GRCh38 坐标(`canonical_spdi`),组装匿名 VCF(剥 rsID→'.'/INFO→'.'/基因名/致病性),18 变异跨 10 染色体,答案埋中间。
- 验收 4 项全达成:① 1 行 problems.csv + data/*.zip ② bmb_validator **0 REJECT/0 WARN/exit 0** ③ **盲解**(solve_problem 只读 zip)→ `PAH|Phenylketonuria`,致病命中**唯一=1**,**36 次工具**(VEP18+ClinVar18,≥10 门),无泄露 ④ 脚本=管线雏形。

## 可复用工具链(已实连,别重造)
- **建题真值源** = NCBI ClinVar E-utili
