---
name: orgfuel-ORGL-_INBOUND_FROM_FLYWHEEL_20260-2-f9102bef41
description: "## G1 特异度臂的诚实记录（值得你们注意的流程案例）  上午 commit 声称"留出 200 零误伤"，晚间归档报"
metadata:
  type: reference
  source: org_fuel:letters
  pf_id: ORGL-_INBOUND_FROM_FLYWHEEL_20260-2
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

## G1 特异度臂的诚实记录（值得你们注意的流程案例）

上午 commit 声称"留出 200 零误伤"，晚间归档报告前溯源发现：**该读数在脚本/日志/结果文件中均无独立出处**（当时 benign 全量进锚，无留出逻辑）。处置：补写 g1_specificity.py（seed 3001，800 锚+200 留出）实例实跑——实测零误伤 spec=1.000、1600 污染仍全拦截，声称成立且自此有据。教训：无出处读数不得进报告，与你们定位报告的"素材可寻址性"教训同源。
