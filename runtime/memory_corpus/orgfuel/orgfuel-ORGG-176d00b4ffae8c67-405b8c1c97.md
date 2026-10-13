---
name: orgfuel-ORGG-176d00b4ffae8c67-405b8c1c97
description: "判读档判例 S6_RERUN_SCHEDULE_20261008 · 1. 排期(10/12 前完成,留一日缓冲) ##"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-176d00b4ffae8c67
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 S6_RERUN_SCHEDULE_20261008 · 1. 排期(10/12 前完成,留一日缓冲)
## 1. 排期(10/12 前完成,留一日缓冲)

| 日 | 动作 | 出口判据 |
|---|---|---|
| **10/9** | cloud 环境预检+管道搭建:磁盘审计(现余 62G)/swebench 安装/30 题 repo 镜像预拉(按 repo 去重,预计 15-20 个)/preds_arm_a.json+board_b patches 上传 | 镜像预拉完成或受阻点当日回报(勿静默) |
| **10/10** | 30 题双臂复跑(官方口径零改:`swebench.harness.run_evaluation`,max_workers 4) | 全量跑完,error 率披露 |
| **10/11** | 读数对表(复跑 resolved vs 26.7%/16.7% 判分侧实测)+S6 复跑判定档(证据三层) | 判定档入 10/11 终检,外网可引 |
| 10/12 | 开业引用(信任链闭合:客户可按同管道复算) | — |
