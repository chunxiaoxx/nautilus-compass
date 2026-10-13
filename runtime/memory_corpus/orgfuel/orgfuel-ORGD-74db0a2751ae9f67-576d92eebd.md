---
name: orgfuel-ORGD-74db0a2751ae9f67-576d92eebd
description: "[### 2.3 LoRA 持续学习与遗忘] - 学界 [实测·二手]:ICLR 2026 LoRA 遗忘理论;正交子空"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-74db0a2751ae9f67
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[### 2.3 LoRA 持续学习与遗忘] - 学界 [实测·二手]:ICLR 2026 LoRA 遗忘理论;正交子空间 LoRA(spectral thresholding,每任务独立子空间);SAE 引导激活正则(plasticity/stability 权衡)。
- 我方对应:P3 回归门(REG-100 零 correct→incorrect 翻转)=行为级防遗忘;热启动+replay 1:1。
- 实测(10/3 S3 工程):challenger(2 epochs delta14+replay14)binary 0.9122 vs champion 0.9189,微降 0.7pt 三门全绿——行为门在微增量下天然少触发。
