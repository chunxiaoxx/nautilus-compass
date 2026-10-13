---
name: orgfuel-ORGG-5548ba1fa9bac35a-d4e29ccd6d
description: "判读档判例 2026-09-14-merge-rehearsal · 四、9/15 runbook 修正版 ## 四、9"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-5548ba1fa9bac35a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-09-14-merge-rehearsal · 四、9/15 runbook 修正版
## 四、9/15 runbook 修正版

1. 生产 worktree checkout `merge-ready-0915`(不要 merge feat/memory-gate-trio)
2. 受控重启(测试实例验过后再做生产)
3. `python ops/regression_gate.py` 对照基线(J4 三 fact)
4. J1-J3 读数回填预注册档(docs/plans/2026-09-09-rsi-trial1-preregistered.md)
5. 非实现者复算(RSI 环第四段)
6. 判据只许更严
