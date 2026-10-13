---
name: orgfuel-ORGH-54d00b428b65b2d1-34dfdfdeb2
description: "commit 85881d97f6c2 2026-04-27 feat: v0.6 · profile 适配 + KPI"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-54d00b428b65b2d1
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 85881d97f6c2 2026-04-27
feat: v0.6 · profile 适配 + KPI 日志
新增:
  · anchors_zenmind.json (25+25 禅心场景锚点)
  · anchors_vc.json (25+25 创投场景锚点)
  · audit_kpi.py (周末跑 · 看 drift_alert + strategy_hit + recall_hit)
  · usage.jsonl 自动记录 (drift / strategy / recall 三类事件)
  · cwd auto-select profile (quantum-buddha → zenmind / venture → vc)

集成扩展:
  · HR Agent agent_loop.py 入口注入 ZenMindMemClient
  · V5 super_agent.respond 入口已注入
  · Kairos _kairos_llm 入口已注入
