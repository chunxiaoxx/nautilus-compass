---
name: orgfuel-ORGH-1241dc53b39c3b0e-0e824d5fbb
description: "工具决策记录 compass_goal_heartbeat.py 目标模式心跳执法 · 每小时跑一次(ops/compa"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-1241dc53b39c3b0e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 compass_goal_heartbeat.py
目标模式心跳执法 · 每小时跑一次(ops/compass_goalmode.bat 循环调度)。

做三件事,结果写 memory obs(红灯额外醒目标记):
1. recall 探活:对本地 daemon 9876 发真实语义查询,失败/超时 = 引擎红灯
   (治 2026-08-23 发现的"torch 坏死数月无人知")。
2. 合约扫描:memory 目录 session-contract-* 里 due 已过且无 CONSUMED 的 = 悬账红灯。
3. 状态摘要追加到 .cache/goalmode_heartbeat.log(本地仪表)。
