---
name: orgfuel-ORGD-e5c3b05d178f4d1a-89f1771ec4
description: "[## L6 · 首训练单线(P3 管道首转)【语料 ≥200 触发】] - **触发**:p3_ticket.py 报"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-e5c3b05d178f4d1a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## L6 · 首训练单线(P3 管道首转)【语料 ≥200 触发】] - **触发**:p3_ticket.py 报 ISSUED(pending ≥200;L1 errata+L3 E1+案源任一凑齐)
- **步骤**:①人工批准执行(ticket PENDING_APPROVAL→APPROVED)②4090 短租(1.65/h,API 层,守门 exit42)③train_judge_incremental.py(--ticket, epochs≤5)④双臂 preds 拉回⑤p3_gate --record⑥PASS→p3_promote 上岗;FAIL→rejected/ 冠军不动(重训限 2 次)
- **验收**:ledger 记 GATE/PROMOTE;组织 RSI 循环首次完整转一圈
- **成本上限**:ticket cost_cap ¥5
