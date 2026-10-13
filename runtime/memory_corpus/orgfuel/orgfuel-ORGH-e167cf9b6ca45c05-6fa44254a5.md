---
name: orgfuel-ORGH-e167cf9b6ca45c05-6fa44254a5
description: "commit 70510ef45e72 2026-05-06 spec(audit): real stress numb"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-e167cf9b6ca45c05
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 70510ef45e72 2026-05-06
spec(audit): real stress numbers · Postgres trigger 100K → 5M rows
Stress benchmark (cloud · sqlite 3.37.2 · 2026-05-06):
  1K:    22,727 ins/s  p95  6ms  vacuum   17ms  140→112 KB
  10K:   26,455 ins/s  p95  7ms  vacuum   35ms  1.2→0.9 MB
  100K:  15,987 ins/s  p95  7ms  vacuum  268ms  11.7→8.5 MB
  1M:     9,905 ins/s  p95  7ms  vacuum 3157ms  117→86 MB

Findings:
- SELECT p95 = 7ms across 4 orders of magnitude (idx_user_ts perfect)
- INSERT drops only 2.3× from 1K → 1M
- VACUUM linear: 1M=3.2s tolerable, 5M≈16s painful

Revised Postgres switch trigger:
  was: 100K rows (over-conservative)
  now: 5M rows OR DB > 1GB OR vacuum > 30s

Live deployments verified:
  ext https://compass.nautilus.social/.well-known/agent.json → 200 (A2A discovery)
  ext https://co
