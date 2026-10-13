---
name: orgfuel-ORGG-df555973de263984-7ed107b6f1
description: "判读档判例 P2V2_LORA_PLAN_20260930 · 二 · 模型方案 ## 二 · 模型方案  - 底模:*"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-df555973de263984
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 P2V2_LORA_PLAN_20260930 · 二 · 模型方案
## 二 · 模型方案

- 底模:**Qwen3-1.7B**(SOTA 日教训:0.6B 无效——推理力不够;1.7B 是 24G 卡
  QLoRA 舒适区)+ QLoRA(r16/α32/dropout 0.05,4bit)
- 任务头:三态 verbalizer(pass/fail/insufficient_evidence),输入=P2 v2 的
  工件文本(sample_text v2,**无 judge_output 作弊通道**,已证 ECE 0.045)
- 数据:split 三折冻结不变(sha16 同预注册,零改动);train 1162 微调,
  dev 143 早停,test 149 仅终评一次
- 训练:epochs ≤8 · lr 1e-4 · batch 8×grad_accum 2 · bfloat16
