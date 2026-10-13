---
name: orgfuel-ORGH-2cdc87081f2761bc-4442ca14aa
description: "工具决策记录 exp1_challenger_v2.py exp1 · challenger v2 全量重训实验(eng"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-2cdc87081f2761bc
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 exp1_challenger_v2.py
exp1 · challenger v2 全量重训实验(engineering 票,不入岗)。

目的:P3 首训练单(delta≥200)触发前的配方实验——全量 split_train(1162 条)+
champion 热启动+全精度 3 epochs,读数对比 champion 基线(reg100+test149)。
判据(实验级,预注册):challenger acc 相对 champion Δ;REG-100 零翻转计数;
只记录不 promote,产物落 /root/runtime/judge_lora_p3/exp/,不触 delta 账本。
口径:复用 train_judge_incremental_fixed(R78 修复版)的 PROMPT_TMPL/sample_text,
predict=完整 prompt 末位 logits(截尾=40pt 错位教训)。
