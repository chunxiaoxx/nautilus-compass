---
name: orgfuel-ORGH-93a1728bb7f9edd6-29eada4c05
description: "commit b962f5211edb 2026-08-22 feat(gate-b): 首次 Gold · 中臂失败序"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-93a1728bb7f9edd6
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit b962f5211edb 2026-08-22
feat(gate-b): 首次 Gold · 中臂失败序号死锁修复 + 标定 suite 归档
- fix: adapter 失败臂推进 _next_ordinal(原中臂失败→下一臂误判 duplicate_attempt 死锁;no-retry 语义保留)
- 标定: prompt 显式化隐含契约(source 措辞序/transfer value 变量),oracle 一字未改
- 首次 Gold 实录: outputs/gate_b_cal2_20260822(source✓ control✗ treatment✓ delta=1
  · glm-5.3 真解 · verify 重放 rc=0 · promotion 全 false candidate-only · 成本~$0.008/全程)
