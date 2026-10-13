---
name: orgfuel-ORGH-a2b2d99659ea7c6b-b3275299c8
description: "commit 50708a2f70d1 2026-05-11 fix(ops): uvicorn --timeout-k"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-a2b2d99659ea7c6b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 50708a2f70d1 2026-05-11
fix(ops): uvicorn --timeout-keep-alive 75 · fix V5 RemoteProtocolError
Root cause:
- uvicorn default --timeout-keep-alive 5s
- V5 httpx via httpcore process-level pool reuses TCP idle > 5s
- low-freq endpoints (recall, ingest_obs) idle > 5s · hit closed conn
- drift_check high-freq · never idle > 5s · masked the issue

Symptoms before fix (V7 report 10:27):
- recall 7 fail/h with RemoteProtocolError
- ingest_obs 2 fail/h with ReadError
- drift_check 0 fail (different freq · same handler path)

Fix:
- patch_keepalive.py · idempotent systemd unit patch · 75s industry std
- smoke_keepalive_fix.py · verify with idle 10s between calls · 6/6 OK
- notify_v7_keepalive_fix.py · request V5 add RemoteProtocolError retry

Self-audit (anchors_self_audit v1.0 caught this 3
