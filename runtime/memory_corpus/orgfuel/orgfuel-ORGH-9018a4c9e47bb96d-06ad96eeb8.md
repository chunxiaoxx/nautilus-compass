---
name: orgfuel-ORGH-9018a4c9e47bb96d-06ad96eeb8
description: "commit 74ec8f4d5b65 2026-05-12 fix(ops): Connection: close o"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-9018a4c9e47bb96d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 74ec8f4d5b65 2026-05-12
fix(ops): Connection: close on /v1/v14/* · true root-cause fix for V5 RemoteProtocolError
Why keep-alive 75 (commit 50708a2) was insufficient:
- V5/V6 production call recall every 10-15 min · idle gap >> 75s
- Previous smoke used 10s idle · false-positive
- V7 retry decorator reused stale pool conn · 2nd attempt also failed

Real fix:
- Middleware adds `Connection: close` header for /v1/v14/* paths only
- httpx honors HTTP/1.1 Connection: close · drops pool entry · next call fresh TCP
- /v1/drift_check unchanged · high-freq · keep-alive pool reuse OK

Verified:
- curl: /v1/v14/recall returns Connection: close ✓
- curl: /v1/drift_check returns no Connection header ✓
- smoke_long_idle.py: 3/3 OK with 90s idle (> 75s keep-alive) · 0 errors

Self-audit (4th repet
