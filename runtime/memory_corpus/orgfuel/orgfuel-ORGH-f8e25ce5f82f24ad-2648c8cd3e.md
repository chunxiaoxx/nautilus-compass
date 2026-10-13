---
name: orgfuel-ORGH-f8e25ce5f82f24ad-2648c8cd3e
description: "commit 1ec3dbbe8560 2026-05-09 handshake §7.1: dispatch_mark"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-f8e25ce5f82f24ad
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 1ec3dbbe8560 2026-05-09
handshake §7.1: dispatch_marketing_bounty SQL contract · production-verified
Per platform dialog's follow-up after PR-merge path was abandoned (their
stale branch · main has subsumed the §2.F/§2.G concepts via the BP1+BP3
file stubs). They asked for one doc-level patch: document the SQL
function we e2e-verified yesterday so the file-stub path and the SaaS
production path sit side-by-side in §7.

Adds §7.1 with:
- full function signature (discovered via \df on nautilus_production)
- caller pattern (the actual SQL we ran for mkt-597d4f9026...)
- state machine across platform_bounties row updates
- e2e timeline table (29s round-trip · 3.1× faster than estimate)
- Stage 1 cutover state (dev.to live · X/GH dry-run · email pending SMTP)
- platform_external_events t
