---
name: orgfuel-ORGM-judging-evidence-tiers-2-011d140d4b
description: "--- name: judging-evidence-tiers-20261003 description: "判分方法"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-judging-evidence-tiers-2
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: judging-evidence-tiers-20261003
description: "判分方法论第三课(用户拍板)——实测/推断/不可验三层强制标注,G1 初判把推断写成断言的教训;正本 docs/metering/JUDGING_EVIDENCE_TIERS_20261003.md"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 202e18d7-9c37-49e6-9407-62ade2b030d8
  modified: 2026-10-03T00:09:11.422Z
fact_status: inferred
---

2026-10-03 G1 双臂判分:我初判把"零增量帧"的**数学推断**写成断言发出(材料无 state 字段,由 pred≈act+ratio 数千倍反推);用户问"你进行判读了吗"→补深:16 帧全目检+直读数据集实测(‖act−state‖=3.5e-5~7.4e-5)才坐实。用户随即将"实测/推断/不可验三层标注"拍板为判分纪律。

**Why**:判分机构的核心资产是输出的可信度分层——推断冒充实测一次,整个 verdict 的证据链都变得不可分;U 态与证据层是两个独立维度(实测也能得出 U 态)。

**How to apply**:
- 正本 docs/metering/JUDGING_EVIDENCE_TIERS_20261003.md;CLAUDE.md 报数纪律段已引用(每会话注入)
- 每条结论性陈述标 [实测](命令+sha)/[推断](依据链+upgrade_path)/[不可验](缺什么);coverage 如实记(目检几帧写几帧)
- 判分脚本 g1_judge_v1.py 后续版本应内嵌 evide
