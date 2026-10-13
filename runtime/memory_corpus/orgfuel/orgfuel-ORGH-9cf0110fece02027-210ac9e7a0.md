---
name: orgfuel-ORGH-9cf0110fece02027-210ac9e7a0
description: "commit 6b2a506b60d4 2026-05-06 v0.9 production: audit Stage "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-9cf0110fece02027
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 6b2a506b60d4 2026-05-06
v0.9 production: audit Stage 0+1 · validation · onboarding · landing v2
Stage 0+1 deployed (compass.nautilus.social):
- audit_retention_cron with VACUUM (Stage 0 · disk reclaim)
- compass_http_v09: login + oauth 1/10 sampling · async batch insert
- write_audit() now appends to deque · background flusher every 5s · 100% backward-compat
- signup adds audit row (sync · scrypt-bound) · login/oauth sampled
- 6-dim validation PASS: 1281 req/s healthz · 138ms signup · 12s self-heal · audit 100% tracked

Stage 2-3 spec ready:
- paper/AUDIT_PARTITION_SPEC.md (monthly partition · trigger 1M rows · DROP TABLE replaces DELETE)
- v1.0 Postgres switch trigger @ p95 > 100ms or MAU > 10K

Tooling:
- scripts/stress_audit.sh (4-scale benchmark · auto Postgres trigger recommend
