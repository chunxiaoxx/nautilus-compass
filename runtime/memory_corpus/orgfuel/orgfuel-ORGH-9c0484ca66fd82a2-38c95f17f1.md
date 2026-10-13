---
name: orgfuel-ORGH-9c0484ca66fd82a2-38c95f17f1
description: "工具决策记录 e1_calib60_sample.py 人类抽检标定 60 题材料包·抽样脚本(JUDGE_UPGRAD"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-9c0484ca66fd82a2
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 e1_calib60_sample.py
人类抽检标定 60 题材料包·抽样脚本(JUDGE_UPGRADE_PREP_20261004 §三协议)。

分层:主包 498 帧按 3B v4 定版判读(goldpack_main_J2.csv)dim3 三层(高/中/低)各 20。
层内选择:seed 洗牌后,7B/3B dim2 分歧帧(判据二义点主场)优先,一致帧补足。
双盲纪律:产出作答表不含任何判官读数;判官读数只进 SAMPLING.md 的层标记账(供汇总期对表)。
seed=202610042 冻结,重跑零漂移。
