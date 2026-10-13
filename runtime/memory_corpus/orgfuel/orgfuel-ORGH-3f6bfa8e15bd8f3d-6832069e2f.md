---
name: orgfuel-ORGH-3f6bfa8e15bd8f3d-6832069e2f
description: "工具决策记录 rejudge_mechanical_check.py rejudge 500 题抽样复算 · 机械层+抽"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-3f6bfa8e15bd8f3d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 rejudge_mechanical_check.py
rejudge 500 题抽样复算 · 机械层+抽样任务生成+汇总。

预注册判据正本:docs/metering/REJUDGE_RECOMPUTE_PREREG_20260930.md
(J1 冲突率≤5%/J2 盲判一致率≥90%/J3 双绿升级/J4 seed=20260930/J5 盲/J6 原样读数)

用法:
  python tools/rejudge_mechanical_check.py            # 机械层 + 生成抽样任务
  python tools/rejudge_mechanical_check.py summary    # 汇总(需 sample_verdicts.json)
