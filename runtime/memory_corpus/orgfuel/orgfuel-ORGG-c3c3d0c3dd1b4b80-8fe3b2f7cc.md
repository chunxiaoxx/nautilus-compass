---
name: orgfuel-ORGG-c3c3d0c3dd1b4b80-8fe3b2f7cc
description: "判读档判例 LOOP_SYSTEM_V1_20260923 · 一 · 机制 1:LOOP_STATE 账本(单一真值)"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-c3c3d0c3dd1b4b80
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 LOOP_SYSTEM_V1_20260923 · 一 · 机制 1:LOOP_STATE 账本(单一真值)
## 一 · 机制 1:LOOP_STATE 账本(单一真值)

- 位置:`docs/plans/LOOP_STATE.md`(assay 主仓,每轮 commit,git 历史=审计线)
- 结构:任务表(owner/判据/deadline/状态)+轮次日志(每轮 4 行)
- 各框同步方式:每轮开头 `git pull` 读账本;不能拉仓的框(flywheel/日报)
  由平台信箱轮次摘要函代理通知(摘要函=只读投影,真值在 git)
- 铁律:状态只许在本档改;聊天里的状态=草稿,不入账不算数
