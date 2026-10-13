---
name: orgfuel-ORGH-1790d985f3fcdf25-c21916bc9f
description: "工具决策记录 train_judge_baseline.py P2 v1 · verdict-judge 基线训练(bg"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-1790d985f3fcdf25
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 train_judge_baseline.py
P2 v1 · verdict-judge 基线训练(bge-m3 冻结 + 三态头)。

预注册:docs/metering/P2_JUDGE_TRAINING_PREREG_20260930.md
  J1 test 二值 acc ≥85% · J2 ECE ≤0.10 · J3 U 态探索性
  J4 训练禁读 test(仅最终评估一次) · J5 split sha 校验 · J6 读数原样落盘

用法:python tools/train_judge_baseline.py
产出:runtime/judge_baseline/{features.npy,head.pt,eval_report.json,run_log.txt}
