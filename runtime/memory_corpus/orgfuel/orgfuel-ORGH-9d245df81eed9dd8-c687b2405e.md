---
name: orgfuel-ORGH-9d245df81eed9dd8-c687b2405e
description: "commit 65595e24c602 2026-05-18 release(v1.6.0): consolidate "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-9d245df81eed9dd8
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 65595e24c602 2026-05-18
release(v1.6.0): consolidate ops/cron + 7-file version sync + clear stale PyPI 1.2.x
## version sync (7 sources → 1.6.0)
- pyproject.toml: 1.5.1 → 1.6.0
- package.json (root NPM): 1.2.0 → 1.6.0
- npm/package.json (MCP NPM): 0.9.5 → 1.6.0
- .claude-plugin/plugin.json: 1.1.0 → 1.6.0
- recall.py PLUGIN_VERSION: v1.5.1 → v1.6.0
- mcp_server.py SERVER_VERSION: 1.5.0 → 1.6.0
- server.json (MCP registry · new): 1.6.0

## new ops/cron (5 publishers + 5 .sh wrappers)
- arxiv_discovery_cron · 论文发现 6h cron
- engagement_followup_cron · outreach engagement followup
- gmail_inbound_monitor_cron · Gmail 入站监控
- memory_compact_cron · memory 压缩
- outreach_metrics + cron · outreach 度量

## new data files
- anchors_outreach_quality.json · 25 pos + 35 neg anchors · drift_check gat
