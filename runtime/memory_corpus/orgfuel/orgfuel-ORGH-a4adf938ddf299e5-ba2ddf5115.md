---
name: orgfuel-ORGH-a4adf938ddf299e5-ba2ddf5115
description: "工具决策记录 train_judge_lora.py P2 v2 · verdict-judge LoRA 训练(Qwe"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-a4adf938ddf299e5
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 train_judge_lora.py
P2 v2 · verdict-judge LoRA 训练(Qwen3-1.7B QLoRA + verbalizer 三态)。

预注册:docs/metering/P2_JUDGE_TRAINING_PREREG_20260930.md(J1-J6)
       + docs/plans/P2V2_LORA_PLAN_20260930.md(J7 v1/v2 对照≥+10pt)
运行环境:GPU 实例(4090 48G);输入=split 三折(sha 冻结)。
设计:verbalizer 下一 token 训练("pass"/"fail"/"insufficient_evidence"),
推理取三词 softmax=天然校准概率(ECE 直接可算)。
