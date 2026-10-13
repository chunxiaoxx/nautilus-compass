---
name: orgfuel-ORGH-df86f2488887fc2d-2966db5c4b
description: "commit c23e6961c65b 2026-05-11 ship(adapter): v0.9 HTTP gate"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-df86f2488887fc2d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit c23e6961c65b 2026-05-11
ship(adapter): v0.9 HTTP gateway → v1.4 BGE daemon · dual flywheel WIRED
The 7-day "L2 not live" narrative was wrong · platform agents WERE calling
compass (2843 calls / 7d in PostgreSQL agent_tool_calls) · but hitting v0.9
port 8770 with no anchors loaded · returning drift=0.000 false-green every
time. Worse than zero calls. False-negative version of 305-case / P1-1.

ops/v0.9_to_v14_adapter_patch.py · idempotent surgical patch
  · injects _call_v14_daemon helper (TCP socket → port 9876)
  · replaces /v1/drift_check body · v1.4 BGE-m3 primary · jaccard fallback
  · adds GET /v1/v14/recall and POST /v1/v14/ingest_obs (A2)
  · response shape unchanged · platform clients no code change required

Deployed to cloud 2026-05-11 18:48 CST (verified):
  · sudo python
