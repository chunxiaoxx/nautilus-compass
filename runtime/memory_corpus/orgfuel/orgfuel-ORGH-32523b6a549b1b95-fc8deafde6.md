---
name: orgfuel-ORGH-32523b6a549b1b95-fc8deafde6
description: "工具决策记录 train_judge14b_smoke.py 14B QLoRA 判读器 smoke(PREFOR_JU"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-32523b6a549b1b95
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 train_judge14b_smoke.py
14B QLoRA 判读器 smoke(PREFOR_JUDGE14B_SMOKE_20261004.md S1-S5)。

现役配方迁移:tools/train_judge_lora.py(P2v2 verdict-judge,verbalizer 三态)。
smoke 只回答"14B 管线可跑否",升格决策另立预注册。
判据:S1 训练 200 步零 OOM 正常退出 / S2 显存峰值<36G / S3 loss 末20<首20
     S4 test 抽 20 题三态输出格式合规 20/20 / S5 gold 一致率如实申报(无门槛)。
启动守门:GPU 显存占用 >2G 即退出(B 臂/flywheel 优先,不抢卡)。
