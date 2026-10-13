---
name: orgfuel-ORGD-f069c1ffc3c8ca40-b8ee769fb2
description: "[## 二 · 提案:verdict-judge(动态权重三态判分器)] - 输入:verdict 工件(criteri"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-f069c1ffc3c8ca40
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 二 · 提案:verdict-judge(动态权重三态判分器)] - 输入:verdict 工件(criteria@catalog 引用+原始读数+被检判分器输出+复算命令)
- 输出:三态 {pass/fail/insufficient_evidence} + 校准置信度(Jev 式:置信度即产品)
- 基线训练:三态 LoRA(Laya 决策头),语料=verdict 库(~50 条)→ 2000 条阈值
