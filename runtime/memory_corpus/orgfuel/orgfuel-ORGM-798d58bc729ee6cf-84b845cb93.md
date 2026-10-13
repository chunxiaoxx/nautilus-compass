---
name: orgfuel-ORGM-798d58bc729ee6cf-84b845cb93
description: "记忆条目 judging-evidence-tiers-20261003.md 2026-10-03 G1 双臂判分:我"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-798d58bc729ee6cf
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 judging-evidence-tiers-20261003.md
2026-10-03 G1 双臂判分:我初判把"零增量帧"的**数学推断**写成断言发出(材料无 state 字段,由 pred≈act+ratio 数千倍反推);用户问"你进行判读了吗"→补深:16 帧全目检+直读数据集实测(‖act−state‖=3.5e-5~7.4e-5)才坐实。用户随即将"实测/推断/不可验三层标注"拍板为判分纪律。

**Why**:判分机构的核心资产是输出的可信度分层——推断冒充实测一次,整个 verdict 的证据链都变得不可分;U 态与证据层是两个独立维度(实测也能得出 U 态)。

**How to apply**:
- 正本 docs/metering/JUDGING_EVIDENCE_TIERS_20261003.md;CLAUDE.md 报数纪律段已引用(每会话注入)
- 每条结论性陈述标 [实测](命令+sha)/[推断](依据链+upgrade_path)/[不可验](缺什么);coverage 如实记(目检几帧写几帧)
- 判分脚本 g1_judge_v1.py 后续版本应内嵌 evidence_tier 字段
- 关联 [[judge-lessons-20260926]](第一二课:全部判定门+判绩账双向)——本条为第三课
