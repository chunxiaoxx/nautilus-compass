---
request_id: compass-v5-fde-envelope-v3-first-live-batch-20260722
frame: fde
source_repo: nautilus-compass
target_repo: nautilus-v5
event_time_utc: 2026-07-22T00:00:00Z
author: codex
status: blocked_pending_user_confirmed_bitable_blueprint
supersedes:
  - _OUTBOUND_FROM_COMPASS_TO_V5_20260721_fuel_protocol_ack.md
scope: one formally verified, redacted Phase 3 envelope
---

# Blocker notice: first official FDE Compass v3 export

The prior request to place ten A-class candidates directly into Compass recall
is superseded. Compass will not consume the older event shape or any raw source
material.

## State ownership and current stop condition

The current Compass v3 receiver accepts only
`verification_state=canonical_verified` and `candidate_state=closed`. The V5
v3 exporter also requires that independent canonical verification has already
completed. The Core authority wording that placed `canonical_verified` after
Compass validation was therefore circular.

The minimal authority patch is ready as Core commit `b1c3ab21d`
(`docs(fde): align Compass receipt state ownership`). It defines one order:

```text
canonical_pending
  -> V5 independent canonical verifier + controlled Bitable read-back
  -> canonical_verified
  -> V5 v3 JSONL + manifest
  -> Compass validate/import/read-back receipt
  -> Bitable read-back of the controlled export/receipt linkage
```

Compass never receives a Bitable record ID or writes Bitable directly. Its
receipt implementation is ready as Compass commit `d3b0217`
(`feat: emit verifiable Compass import receipts`). The remaining live gate is
the user-confirmed Bitable table blueprint, its controlled authority state
mapping, and then one formally eligible Bitable-anchored file pair. Do not
generate a candidate JSONL merely to exercise the parser before those gates.

No V5-side Bitable writeback adapter is authorized. `canonical_verified`,
`canonical_blocked`, and `compass_imported` remain Bitable authority states
whose proof comes from the configured read-back path; Compass only emits a
minimal receipt that a controlled owner may correlate with the originating
export.

## Deliverables once unblocked

From V5's existing canonical exporter, provide one restricted handoff pair:

1. `fde_compass_v3_001.jsonl` with schema
   `fde.compass.envelope.v3`.
2. `fde_compass_v3_001.manifest.json` with schema
   `fde.compass.ingest_manifest.v3`, matching the exact JSONL bytes.

Use the existing `prepare_canonical_compass_export(...)` followed by
`write_canonical_compass_export(...)`. Do not add a second exporter or a new
FDE data structure.

## Eligibility of the single event

The exported event must already have:

- `canonical_verified=true`;
- `candidate_state=closed`;
- final `verdict` of `Gold`, `Repair`, or `Reject` from the independent
  canonical verifier;
- P0 interaction checks passed;
- only the v3 allowlisted, minimalized fields.

`buyer_feedback` remains evidence context and `feedback_class`; it is not a
verdict. A record still awaiting repair or acceptance remains blocked/pending
and must not be exported as `Repair`.

## Strict privacy boundary

The handoff must not contain raw UID, identity fields, original task text,
conversation/trajectory text, per-turn reasons, attachments, source materials,
passwords, share URLs, or Feishu payloads. V5 retains those materials in its
controlled ledger.

The manifest must retain only its existing v3 contract fields: schema version,
JSONL SHA-256, event count, event projections, and blocked-row projections.
Do not add attestation or other unknown keys: Compass rejects unknown manifest
fields fail-closed.

## Expected Compass response

Compass will run, in an isolated memory root:

1. manifest/schema/hash dry-run;
2. a single idempotent write and read-back;
3. a read-only `fde_interactive_trajectory` replay under `flat` policy.

The response will include a minimal `fde.compass.import_receipt.v1` bundle
whose entries are matched by `event_id + payload_hash`; the outer local report
is not a Bitable writeback payload. It will report only counts, status, hash
verification, read-back and replay outcomes. It will not claim recall
improvement or change V5 R3, Feishu, buyer systems, income routing, or default
recall policy.

## Unblock criterion

The next permitted action is a controlled owner publishing one officially
Bitable-anchored v3 JSONL/manifest pair after the user confirms the table
blueprint. Until then, retain only the existing exporter, Compass
consumer/receipt tests, and this blocker record.
