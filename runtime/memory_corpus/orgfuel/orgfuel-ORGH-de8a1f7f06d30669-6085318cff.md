---
name: orgfuel-ORGH-de8a1f7f06d30669-6085318cff
description: "commit 1c5a700ca8e5 2026-05-12 fix(ops): ssh tunnel keepaliv"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-de8a1f7f06d30669
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 1c5a700ca8e5 2026-05-12
fix(ops): ssh tunnel keepalive · ServerAliveInterval=30 · prevent silent death
Symptom: nautilus-compass-cloud MCP × failed mid-session · /mcp reconnect
returns -32000 because SSH tunnel on 9877 silently died (NAT/firewall
killed idle conn after ~10-15min).

Fix:
- compass_start.ps1 · cstart now starts ssh with:
  · ServerAliveInterval=30 (send keepalive every 30s)
  · ServerAliveCountMax=3 (give up after 3 missed = 90s)
  · ExitOnForwardFailure=yes (die fast on port conflict not zombie)
- new `ctunnel` function · mid-session revive without exiting Claude:
  PS> ctunnel
  /mcp reconnect

Prior failure mode (without keepalive):
  1. cstart launches ssh -fN
  2. tunnel idle 10-15min
  3. NAT silently drops conn
  4. Claude Code MCP gets stuck connecting to dead
