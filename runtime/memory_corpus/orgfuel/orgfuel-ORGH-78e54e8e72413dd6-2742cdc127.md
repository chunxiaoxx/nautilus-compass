---
name: orgfuel-ORGH-78e54e8e72413dd6-2742cdc127
description: "工具决策记录 verify_batch001_recheck.py Independent recheck of fly"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-78e54e8e72413dd6
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 verify_batch001_recheck.py
Independent recheck of flywheel batch001 utility report (VerifyPack v0 原型实践).

Protocol: utility-metrics-protocol-v1-frozen. Reads ONLY the pack
(runtime/verify_batch001/{verify_pack,payload}.json, report.md) and the batch
directory it points to. Outputs per-claim agree/disagree + recomputed value.
compass 边界:技术验证与回执,不作验收/结算决定。

Usage: python tools/verify_batch001_recheck.py [flywheel_root]
