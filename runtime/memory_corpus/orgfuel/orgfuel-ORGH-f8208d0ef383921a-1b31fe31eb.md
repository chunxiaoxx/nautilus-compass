---
name: orgfuel-ORGH-f8208d0ef383921a-1b31fe31eb
description: "工具决策记录 exp_runner.py P3 实验通用 runner(engineering 票,不入岗)——exp2"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-f8208d0ef383921a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 exp_runner.py
P3 实验通用 runner(engineering 票,不入岗)——exp2 系扫描用。

用法:exp_runner.py --tag exp2a --lr 5e-5 --epochs 3
口径:复用 train_judge_incremental_fixed 的 PROMPT_TMPL/sample_text;predict=完整
prompt 末位 logits;champion 基线复用 exp1 同机读数(reg=0.91/test=0.9128),
不重测(可比性:同机同 session 段同口径,刚测)。
预注册 exp2 判读规则:Δtest≥+1pt 且 flip≤1 记"配方候选";全部不过线=结论
"重训无增益坐实,首单增益等 delta"——先注册后跑,不事后挑读数。
