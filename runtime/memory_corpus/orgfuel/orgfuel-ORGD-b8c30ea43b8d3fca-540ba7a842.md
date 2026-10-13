---
name: orgfuel-ORGD-b8c30ea43b8d3fca-540ba7a842
description: "[## M3 · 隔离验收自动化(与 M2 并行)] - [ ] **T6 四探针脚本化**:① 跨用户读 DENY ②"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-b8c30ea43b8d3fca
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## M3 · 隔离验收自动化(与 M2 并行)] - [ ] **T6 四探针脚本化**:① 跨用户读 DENY ② 跨用户写 DENY ③ 同用户跨设备命中同一空间 ④ 撤销即时生效。判据:signup 后无人值守自动产出四绿报告(探针即 T4 e2e 的产品化)。
- [ ] **T7 常态回归**:四探针进 cron/supervisor 定期跑(防后续改动破坏隔离)。判据:连续 7 天自动报告无红。
