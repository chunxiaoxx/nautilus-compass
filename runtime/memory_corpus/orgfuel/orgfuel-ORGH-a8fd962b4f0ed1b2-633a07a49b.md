---
name: orgfuel-ORGH-a8fd962b4f0ed1b2-633a07a49b
description: "commit e883095f0c55 2026-07-18 fix(lifecycle): 把 reinforce_o"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-a8fd962b4f0ed1b2
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit e883095f0c55 2026-07-18
fix(lifecycle): 把 reinforce_on_recall_hit 接进 MCP 召回服务路径(access 闭环真断点)
诊断(2026-07-18 实测):reinforce_count 全语料=0,差异化 tier 层 eval +0.000。
根因非'gated on V5',而是 reinforce 只接在 recall.py CLI try_daemon_recall,
生产真召回面(MCP/daemon/plugin)都不触发 → access 事件从不落地 → tier 永停 working。
修:tool_recall 拿到 hits 后按 project 分组 reinforce(guarded/永不破召回)。
验证:reinforce 真 frontmatter 0→1 → promote_lifecycle_tier working→episodic。
限:仅向前累积(无 access 日志可回填);可测 MRR delta 仍需密度(件数≠价值)。
生效=MCP server 重启后。
