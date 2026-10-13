---
name: orgfuel-ORGH-c41ee978e3d9f278-0b3df93237
description: "commit 9241ed362f32 2026-05-11 feat(ops): L2 evidence gate T"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-c41ee978e3d9f278
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 9241ed362f32 2026-05-11
feat(ops): L2 evidence gate Telegram alert · 6h cron · prevent fake closure
ops/monitor_l2_evidence_gate.sh + .py
  · reads /var/log/compass-l2-metrics.json (from compass_l2_metrics.py */5min)
  · tracks per-agent consecutive miss streak in ~/.cache/compass/
  · alerts after 3 consecutive 6h windows missed (= 18h continuous miss)
  · 24h cooldown per agent to avoid spam
  · plain text (no Markdown · backticks confused Telegram parser)

Required agents:
  · nautilus-v5 / nautilus-v6 / v7-souls-fusion / kairos
  · gate: ≥ 10 calls/day per agent_type

Cron installed on cloud:
  0 */6 * * * /home/ubuntu/nautilus-compass/ops/monitor_l2_evidence_gate.sh

Smoke verified · Telegram ok=True after Markdown removal.

Closes #109. Blocks L5 dispatch (SPEC-S1 to V5) until
