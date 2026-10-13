---
name: orgfuel-ORGD-38d9bbc12c2e49c9-ec50ebc197
description: "[## 当前状态(本 session 结束时)] - daemon **仍在 T4 跑**(`pgrep -f "pyt"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-38d9bbc12c2e49c9
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 当前状态(本 session 结束时)] - daemon **仍在 T4 跑**(`pgrep -f "python3 daemon.py"` · 127.0.0.1:9876 · GPU 6.3G)。
- 这是**手动 setsid demo daemon**,**非** systemd。Phase 2 完整 Task 7(systemd unit + spot 抢占 2min handler + drain + 自动重拉)+ Task 8(客户端指 T4 · kill→fallback 实测)= 仍待做(需 spot 实例策略 + 客户端 recall hook 接 recall_with_fallback)。
- corpus_sync/snapshot_pull/recall_with_fallback 代码已 TDD ship(Phase 0 Task 2/3/4)。
