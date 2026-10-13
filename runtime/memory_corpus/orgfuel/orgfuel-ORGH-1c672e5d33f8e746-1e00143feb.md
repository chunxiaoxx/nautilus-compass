---
name: orgfuel-ORGH-1c672e5d33f8e746-1e00143feb
description: "工具决策记录 eval_14b_bf16.py 实验 A(U5 归因翻案检验):14B **bf16** 推理对拍。 首"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-1c672e5d33f8e746
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 eval_14b_bf16.py
实验 A(U5 归因翻案检验):14B **bf16** 推理对拍。
首跑口径不对称:14B=4bit(nf4) vs 1.7B=bf16——本脚本唯一变量=14B 加载精度(bf16,无量化),
复用 train_judge14b_upgrade 的 LABELS/PROMPT/evaluate/load_split(零逻辑改动)。
判据不变:同 292 held-out 同 gold;与首跑 4bit、1.7B 三方对账,含逐条 pred 翻转计数。
启动守门同原档(GPU>2G 退出)。读数正反照报(勘误文化)。
