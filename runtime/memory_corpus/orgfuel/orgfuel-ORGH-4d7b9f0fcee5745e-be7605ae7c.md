---
name: orgfuel-ORGH-4d7b9f0fcee5745e-be7605ae7c
description: "commit 912baee88739 2026-07-03 feat(compass): 推 ABC 三件真 ship"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-4d7b9f0fcee5745e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 912baee88739 2026-07-03
feat(compass): 推 ABC 三件真 ship
A · auto-surface hook(ops/auto_surface_hook.py)
  6/17 rootcause 钉的'用户当人肉 relay'病真解
  扫 _OUTBOUND_FROM_*_TO_compass_*.md 多路径 + watermark .seen_compass
  实跑扫到 76 条 6/11-6/17 平台对话框历次发的 compass 真 inbound
  复用 anchor #5 不重写 hook 架构,env 控路径/对话框名/watermark

B · ale_eval.py 接 V5 rsi_two_arm 注入
  新增 eval_fn_factory(problem_id) 闭包 · 复用现有 eval_fn · 不改主逻辑
  V5 端 rsi_two_arm.run_two_arm 已有 eval_fn 注入槽 · 即可对接

C · liveness 真跑(20260703 17:50)
  liveness_audit.py --json 跑出 3 GREEN:
  - ledger_growth = 1510 行
  - snapshot_freshness = 120h < 168h
  - impact_axis = wiring 双标记全在
  PoI binding-DONE §3 真验证通过
  outbound 给 platform-soul 报数(76 条 inbound 之一)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
