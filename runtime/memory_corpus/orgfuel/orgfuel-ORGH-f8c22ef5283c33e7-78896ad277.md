---
name: orgfuel-ORGH-f8c22ef5283c33e7-78896ad277
description: "commit 9c710d96ff78 2026-04-30 feat: gateway v0.7.2 · API ke"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-f8c22ef5283c33e7
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 9c710d96ff78 2026-04-30
feat: gateway v0.7.2 · API key auth + per-tenant anchor routing + rate limit
Gateway (compass_http.py):
· X-API-Key header auth · 401 on invalid/missing
· COMPASS_AUTH_MODE=none disables (internal-only deploys)
· Per-tenant config in tenants.json (mtime-cached · live-reload)
· Per-tenant anchor profile passed to daemon as anchors_path arg
· Sliding-window rate limit (rate_limit_per_min · in-memory · 429 on exceed)
· /mcp/tools/call also gated through same auth + rate limit path

Daemon (daemon.py):
· _state['anchor_caches'] dict · multi-profile in-memory cache
· get_anchors(anchors_path) accepts per-request profile path
· Per-tenant profile cache stays in-memory only (no .pkl leak across tenants)
· Default anchors.json still persisted to anchors.pkl (back-com
