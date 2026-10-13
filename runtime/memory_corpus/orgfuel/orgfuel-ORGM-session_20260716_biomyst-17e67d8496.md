---
name: orgfuel-ORGM-session_20260716_biomyst-17e67d8496
description: "--- name: session_20260716_biomysterybench_P1_pipeline descr"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-session_20260716_biomyst
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: session_20260716_biomysterybench_P1_pipeline
description: BioMysteryBench P1 端到端跑通:VCF→变异临床意义模板,build/solve 管线雏形,独立盲解坐实 PAH/Phenylketonuria 唯一+36工具+无泄露
metadata:
  node_type: memory
  source_session: 2026-07-16 compass BioMysteryBench P1
  type: project
  originSessionId: 18a77e1b-1920-42a2-be4e-5cb76091e10d
---

# BioMysteryBench P1 端到端跑通(2026-07-16)

承接 [[session_20260716_biomysterybench_scaffold]](脚手架+验证器+500设计)。P1 = 证 1 模板端到端,**不铺量**。

## 成果(独立验证非自报 · commit 5da3719)
`vtf/fde_benchmarks/biomysterybench/` 下新增 `build_problem.py` + `solve_problem.py` + `_P1_out/`(问题+溯源)。
- 题 `bmb_vendor_000001` = **VCF→变异临床意义**模板:1 个隐藏 ClinVar Pathogenic 变异(**PAH / Phenylketonuria**)+ 17 个 Benign/VUS 干扰,全部真实 ClinVar 记录 + 真实 GRCh38 坐标(`canonical_spdi`),组装匿名 VCF(剥 rsID→'.'/INFO→'.'/基因名/致病性),18 变异跨
