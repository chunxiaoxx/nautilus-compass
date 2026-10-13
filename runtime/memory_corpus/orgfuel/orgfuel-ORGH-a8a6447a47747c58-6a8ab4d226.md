---
name: orgfuel-ORGH-a8a6447a47747c58-6a8ab4d226
description: "工具决策记录 e1_j2_batch_judge_3b.py E1·J2 OOD 盲判批处理(Qwen2.5-VL-3B"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-a8a6447a47747c58
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 e1_j2_batch_judge_3b.py
E1·J2 OOD 盲判批处理(Qwen2.5-VL-3B·4bit bnb · 与 gen4 训练共存版)。

判读协议照《判官须知》:五组作答(完成度/执行质量/置信/正问/反问),直觉式
短判断,看不清→无法判断+低置信;独立作答。断点续跑(逐题落 jsonl,重跑跳过)。
输出 viewer 兼容 CSV(goldpack_J2.csv)。
材料: /root/runtime/e1_judge_pack/judge_pack/(blind_data.js + frames/)
产出: /root/runtime/e1_judge_pack/j2_answers.jsonl + goldpack_J2.csv
