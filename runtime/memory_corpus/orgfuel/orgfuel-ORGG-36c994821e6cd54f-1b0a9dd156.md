---
name: orgfuel-ORGG-36c994821e6cd54f-1b0a9dd156
description: "判读档判例 EIGHTB_COMPARE_TRAIN_CONFIG_20261010 · 一、脚本基座与适配点 ## 一"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-36c994821e6cd54f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 EIGHTB_COMPARE_TRAIN_CONFIG_20261010 · 一、脚本基座与适配点
## 一、脚本基座与适配点

- 基座:`runtime/loop/_r177_l3smoke/_train_judge14b_upgrade_A100.py`(14B QLoRA 版,同构迁移);
- **适配点 1·基模**:`BASE=/root/vdf/models/Qwen3-8B`(8B bf16 全精度基座——**不用 4bit**:8B bf16≈16GB,A100 40G 装 LoRA 训练充裕,且符合 PRECOR 部署精度纪律 bf16/fp16 only——比 14B 时代的 4bit 妥协更干净);
- **适配点 2·判定阈值对齐**:脚本常数 `U6_MARGIN = 0.03`(10/5)与判据档 G1 `+2.0pp`(10/8 冻结)不一致——**触发日以判据档 G1=0.02 为准**,脚本常数改为 0.02(对齐冻结判据,防执行时用错尺子);
- 其余超参沿用现役 recipe:LoRA r16/α32/dropout 0.05/AdamW 1e-4/3 epoch(MAX_STEPS 2000 cap)/SEED 20261005。
