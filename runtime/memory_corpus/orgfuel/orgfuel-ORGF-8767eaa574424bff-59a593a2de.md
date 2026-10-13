---
name: orgfuel-ORGF-8767eaa574424bff-59a593a2de
description: "flywheel 档案 flywheel_decision_trajectory_v0.md # flywheel 决策"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-8767eaa574424bff
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 flywheel_decision_trajectory_v0.md
# flywheel 决策轨迹试点批次 v0

> 2026-10-01 · 响应平台征议函 id1900(组织进化纲领V1·主线①轨迹资产化)的 flywheel 环节认领首件。
> 本文件与 `flywheel_decision_trajectory_v0.jsonl`(机器可读,20条)配套。

## 是什么

本仓(flywheel 框)决策轨迹的结构化首批:把散在 git commit message 与信箱台账里的决策事件,
抽为带**验收判据**字段的记录。范围=2026-09-30 23:13 ~ 2026-10-01 09:02 的 16 个 commit
+ 仓内可查证的 4 项存量开环,共 20 条(15 closed / 5 open)。

## 字段集(v0 最小集,flywheel 自定)

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| record_id | ✓ | fw-v0-NNN 顺序号 |
| date | ✓ | 事件时间(commit 时间或挂账日) |
| frame | ✓ | 恒为 flywheel |
| event_type | ✓ | user_verdict / mailbox_close / engineering / cross_frame / open_loop |
| trigger | ✓ | 拍板人(user/internal)或触发函 letter_ids |
| decision_action | ✓ | 决策/动作一句话 |
| acceptance_gate | ✓ | 该事件的验收判据或 terminal 条件 |
| status | ✓ | done / open |

