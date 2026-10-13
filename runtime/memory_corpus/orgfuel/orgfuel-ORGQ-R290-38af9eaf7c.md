---
name: orgfuel-ORGQ-R290-38af9eaf7c
description: "### R290 · 2026-10-07 早(E-NACRE-1 收数判门:负结果照报✅) - **四发后跑通收数[实"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R290
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R290 · 2026-10-07 早(E-NACRE-1 收数判门:负结果照报✅)
- **四发后跑通收数[实测]**:A 臂(现役)0.8767 vs B 臂(三域片路由)0.5103,Δ=-36.6pp,主门+不回退门(三域)全 FAIL——**按预注册语义:"路由无增益坐实",负结果照报**(判定档 PRECOR_ENACRE1_VERDICT_20261007.md,CSV 584 行行级写零丢失+v2 教训兑现)。
- **归因三条**:域片训练量不足(400 条 vs 全量 1454)+loss 0.0004 域内过拟合+评测混合分布;**升级路径=语料≥3000 前动态权重路线整体挂起**(与 7B 同因同果——三条实验线全指向攒语料,corpus_pipeline 触发器即总闸)。
- 判读段日志:发车四发三崩(语料缺/B路由 API/PM NameError)——每次崩即修即发,负结果本身=判读段管线(训练+评测双臂)首次端到端实战验证。
