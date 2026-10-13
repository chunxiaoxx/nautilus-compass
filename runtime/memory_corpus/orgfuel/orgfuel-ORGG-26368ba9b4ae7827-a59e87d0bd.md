---
name: orgfuel-ORGG-26368ba9b4ae7827-a59e87d0bd
description: "判读档判例 2026-06-05-gemini-query-rewrite-design · Testing ## Te"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-26368ba9b4ae7827
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-05-gemini-query-rewrite-design · Testing
## Testing
TDD with a MOCKED gemini provider (no live API):
- flag off → identity.
- flag on + provider off → identity (no-op).
- flag on + mock returns rewrite → rewritten used.
- flag on + mock returns None/empty/over-long → original (fallback).
- daemon integration: monkeypatch rewrite + assert the scored query is the
  rewritten one when flag on; identical path when off.
Live gemini verification (real Vertex creds + `COMPASS_USE_GEMINI_FLASH=1`) is a
manual gated smoke, deferred.
