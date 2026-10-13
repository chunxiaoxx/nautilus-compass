---
name: orgfuel-ORGD-fafa0d29b86fd1a6-289bba4c64
description: "[## 一 · 机制 1:LOOP_STATE 账本(单一真值)] - 位置:`docs/plans/LOOP_STAT"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-fafa0d29b86fd1a6
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 一 · 机制 1:LOOP_STATE 账本(单一真值)] - 位置:`docs/plans/LOOP_STATE.md`(assay 主仓,每轮 commit,git 历史=审计线)
- 结构:任务表(owner/判据/deadline/状态)+轮次日志(每轮 4 行)
- 各框同步方式:每轮开头 `git pull` 读账本;不能拉仓的框(flywheel/日报)
