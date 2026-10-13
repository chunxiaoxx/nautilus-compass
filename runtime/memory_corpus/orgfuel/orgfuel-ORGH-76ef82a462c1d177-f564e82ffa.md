---
name: orgfuel-ORGH-76ef82a462c1d177-f564e82ffa
description: "commit 40d2bcf56ead 2026-05-12 ship(anchors): v1.1 self_audi"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-76ef82a462c1d177
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 40d2bcf56ead 2026-05-12
ship(anchors): v1.1 self_audit · 4 new neg + 8 pos · today's 4 fake-closures baked in
Ground truth · 4 caught-by-self fake-closures from today's MCP wire saga:
  1. service restart treated as root-cause fix (was queue clear only)
  2. 10s idle smoke OK but production P95 idle = 10-15 min (smoke happy-path)
  3. uvicorn keepalive + V7 retry as 'double insurance' (retry reused stale pool)
  4. agent_tool_calls DB success-row as 'recall flowing' (soft-fails not in DB)

Added 4 neg anchors + 4 mirror-pos + 4 anti-mirror-pos (same vocab, correct reasoning).
Version bumped 1.0 → 1.1.

Calibration result (ops/test_self_audit_v11.py · local GTX 1060 BGE-m3 cuda):
  TP 3/4 (75%) · missed 'restart=fixed' (anchor too verbose vs short query)
  FP 3/4 · BGE-m3 surface-wor
