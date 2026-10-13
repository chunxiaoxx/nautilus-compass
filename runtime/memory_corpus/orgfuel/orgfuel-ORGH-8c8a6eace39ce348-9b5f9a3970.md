---
name: orgfuel-ORGH-8c8a6eace39ce348-9b5f9a3970
description: "commit 6c41f59e7845 2026-05-09 feat: scripts/v7_monitor_cron"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-8c8a6eace39ce348
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 6c41f59e7845 2026-05-09
feat: scripts/v7_monitor_cron.py · platform bounty funnel health probe
Drop-in cron the platform runs every 30 min · governance only · no
execution. Catches the 3 funnel-health failure modes V7 was designed for:

1. orphan_open_24h    · matchmaking lag · no agent claims
2. stuck_claimed_12h  · executor accepted but not delivering
3. stuck_submitted_12h · scoring queue backlog (kairos/scoring agents)
4. failed_24h         · upstream asset_not_found / router misroute
5. settle_rate_7d     · end-to-end throughput drop

Surfaces:
  · stdout · human digest
  · stderr · alerts (cron MAILTO picks up)
  · /var/lib/v7-monitor/last_report.json · machine-readable archive
  · optional Telegram POST when TG_BOT_TOKEN + TG_CHAT_ID set

Optional integration with compass gov
