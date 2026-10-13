---
name: orgfuel-ORGD-c009e76da7c9e37e-e49e3b282e
description: "[### 差异(各域只换两样:语料适配器+底座)] | 域 | 语料适配器 | 底座 | 实例命名法 | |---|--"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-c009e76da7c9e37e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[### 差异(各域只换两样:语料适配器+底座)] | 域 | 语料适配器 | 底座 | 实例命名法 |
|---|---|---|---|
| agent 判读(compass) | 判例集+verdict 语料 | Qwen3-1.7B | nacre-judge-v1(已挂 HF) |
| agent 执行蒸馏(v5) | 轨迹→SFT 蒸馏对(r84 64%) | 按任务选型 | nacre-exec-v*(v5 命名) |
| 具身判读/标注(flywheel) | 具身轨迹标注对 | VL 多模态底座(VL-3B 已在盘) | nacre-embodied-v*(预留) |
