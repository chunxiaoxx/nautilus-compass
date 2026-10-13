---
name: orgfuel-ORGG-eea41d4dc3502147-df1e18195f
description: "判读档判例 P2_JUDGE_TRAINING_PREREG_20260930 · 执行坐标 ## 执行坐标  - 切分"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-eea41d4dc3502147
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 P2_JUDGE_TRAINING_PREREG_20260930 · 执行坐标
## 执行坐标

- 切分:`python tools/corpus_split.py`(幂等,seed 固定)
- 训练+评估:tools/train_judge_baseline.py(P2 v1 待写;输入=split_train,
  早停用 dev,最终一次 test)
- 复算:训练脚本 + split 文件即可复现(权重与读数落 runtime/judge_baseline/)

split sha16(冻结,2026-09-30):
- split_train.jsonl: 35683198dd3c4992
- split_dev.jsonl: 942e4daeaedca2fb
- split_test.jsonl: 4bcaf1c9b551f336
