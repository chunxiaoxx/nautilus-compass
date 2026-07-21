---
trace_id: 2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720
frame: compass
source_repo: nautilus-compass
target_repo: nautilus-v5
event_time_utc: 2026-07-21T23:20:00Z
author: codex
confidence: 0.92
maturity: replay_package_ready
proof: local_artifact
recall_hit_rate: not_run
overloaded_count: not_run
bge_backfill_status: not_verified
next_planned_qty: 10
replay_package_path: C:/Users/chunx/Projects/nautilus-compass/docs/plans/2026-07-21-v5-fuel-recall-replay.md
---

# Compass outbound to V5: fuel recall replay package

## Status

Compass has created a concrete recall replay package for the first 10 fuel candidates from:

`C:/Users/chunx/Projects/nautilus-v5/fuel_scorecard_20260721_from_feedback_v2.md`

The package is:

`C:/Users/chunx/Projects/nautilus-compass/docs/plans/2026-07-21-v5-fuel-recall-replay.md`

## What This Proves

- The V5 fuel event now has compass-side replay rows with `trace_id`, `problem_key`, `source_row`, `action_tag`, `payload_hash`, and intended recall queries.
- The package distinguishes planned replay from executed recall.

## What This Does Not Prove

- `recall_hit_rate` is `not_run`.
- `overloaded_count` is `not_run`.
- `bge_backfill_status` is `not_verified`.
- No cloud daemon, systemd unit, BGE backfill, or production recall path was touched.

## Next Compass Work

Run the 10-row replay package through the approved recall path, then publish a follow-up outbound with:

- per-row `hit`, `miss`, or `blocked_*` status
- observed overloaded count
- verified BGE/backfill status
- payload hash mismatches, if any
