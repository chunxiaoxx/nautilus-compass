---
name: orgfuel-ORGM-rsibench-adoption-202610-235b88b0b1
description: "--- name: rsibench-adoption-20261002 description: "rsi-bench"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-rsibench-adoption-202610
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: rsibench-adoption-20261002
description: "rsi-bench 考场借轨提案被对方当天实现落地(PR #2)=第三方采纳我方验证协议设计首例;样例包=本周交付承诺"
metadata: 
  node_type: memory
  type: project
  originSessionId: 202e18d7-9c37-49e6-9407-62ade2b030d8
  modified: 2026-10-02T13:41:34.696Z
fact_status: inferred
---

2026-10-02:9/17 发给 sunghunkwag/rsi-bench 的认证轨提案(诚信计分+仅收据排名)被对方当天实现并 merge——PR #2 "Add opt-in transcript replay certification and trusted receipts"(六轴 replay+Ed25519 审计收据+verifier-key allowlist+仅收据排名+UNVERIFIABLE 墙+诚信分七 claim 组单列+防重复占位),docs/certification.md 明确引用我方 Issue #1。

**Why**:gtaras7 案例=方法论被采纳进其 evals;本例=协议设计被第三方完整实现=验证机构定位的外部背书升级;certification.md 的"replay≠truth of system-provided observations"信任边界与我们的口径互证。

**How to apply**:
- 我方已回(comment 5953691509):承诺**本周**交机读四件套样例包(判据锚 ticket+fix commits+复算轨迹+时间链,含失败全窗,逐
