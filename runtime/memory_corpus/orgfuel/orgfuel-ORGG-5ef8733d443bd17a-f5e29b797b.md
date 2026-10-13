---
name: orgfuel-ORGG-5ef8733d443bd17a-f5e29b797b
description: "判读档判例 S6_REGISTRY_COORDS_REPLY_20261008 · 二、复算 26.7%(A 臂)的最短"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-5ef8733d443bd17a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 S6_REGISTRY_COORDS_REPLY_20261008 · 二、复算 26.7%(A 臂)的最短路径
## 二、复算 26.7%(A 臂)的最短路径

1. 判据:上表判据档(预注册 12 字段+开跑记录+smoke 记录全在档);
2. 判分命令(官方口径零改):`python -m swebench.harness.run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified --predictions_path preds_arm_a.json --run_id l3r1_a --max_workers 4`(predictions 生成器与对齐断言在判据档 §judging);
3. 判定模型:nacre-judge-v1(HF `nautilus-compass/nacre-judge-v1`,adapter sha16=dbcbab6fd1ff5821,模型卡带部署精度表);bf16/fp16 仅可部署(int8/int4 禁用,PRECOR 表);
4. 读数对照:Round1 A 臂 26.7% / B 臂 16.7%(+10.0pp),判读卡与判例集 v1.4 同窗发布。
