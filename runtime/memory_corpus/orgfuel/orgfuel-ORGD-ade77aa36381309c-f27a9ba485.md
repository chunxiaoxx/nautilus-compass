---
name: orgfuel-ORGD-ade77aa36381309c-f27a9ba485
description: "[## 任务定义(承 A2-v4,吸收三课)] - **同域文本对设计**(A2v4 教训:两侧文本域差过大即人亦难配)"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-ade77aa36381309c
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 任务定义(承 A2-v4,吸收三课)] - **同域文本对设计**(A2v4 教训:两侧文本域差过大即人亦难配):
- effect 侧:`reason_span`(自然语言判分理由)
- cause 侧:**判据引用的自然语言展开**——criteria_refs 展开为判据文本(仓内判据库可查)+source_trace 尾段;不裸拼结构化字段
- 检索:effect 表征在 1454 条 cause 表征池中 top-5,命中同 anchor_id
- 表征提取:冻结主干,**倒数第二层 hidden states,mean pooling**(双主干同协议)
