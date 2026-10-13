---
name: orgfuel-ORGD-a9cf204a67d96ee0-03e067d5d9
description: "[## 二、因果倒置的当前载体:动态权重小判分器路线] - 判官 LoRA(verdict-judge 88.51%)是"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-a9cf204a67d96ee0
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 二、因果倒置的当前载体:动态权重小判分器路线] - 判官 LoRA(verdict-judge 88.51%)是"验证"环节的模型化;
- P3 管道是"因果倒置"环节:外部 errata/复算差值→delta 批→QLoRA 更新→REG-100 零翻转回归门→上岗;
- 反自指护栏:判官自产标签永久禁入训练燃料(白名单四类,`tools/p3_delta.py`),模型不能给自己发教材。
