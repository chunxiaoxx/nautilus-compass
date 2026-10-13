---
name: orgfuel-ORGG-bfcee1b70f103282-c4d185f820
description: "判读档判例 2026-06-04-poi-writer-role-tightening-design · 1. Role"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-bfcee1b70f103282
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-04-poi-writer-role-tightening-design · 1. Role & privilege model
## 1. Role & privilege model

- **New** `poi_writer` (LOGIN role, own password):
  - `GRANT USAGE ON SCHEMA compass`
  - `GRANT SELECT, INSERT, UPDATE ON compass.poi_credit`
  - Touches `poi_credit` only; no access to `public`.
- **`compass_sub` back to read-only**:
  - `REVOKE INSERT, UPDATE ON compass.poi_credit`
  - `REVOKE USAGE ON SCHEMA compass` (after the split it never enters the
    compass schema — the snapshot read moves to the writer connection).
  - Its original `public` read grants are untouched.

Net: the read account (used everywhere, exposed on the tunnel) can no longer
write the ledger; the one account that can is single-purpose and independently
rotatable.
