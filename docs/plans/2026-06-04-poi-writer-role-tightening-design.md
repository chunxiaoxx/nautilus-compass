# PoI writer role tightening (Phase 2) — design

**Date**: 2026-06-04
**Concept**: compass-poi-central-ledger
**Status**: approved (brainstorming) → writing-plans next
**Predecessor**: `docs/plans/2026-06-03-poi-central-ledger-design.md` (Phase 1, single-table MVP shipped, PR #35 → main, v2.2.0)

## Problem

Phase 1 reused the existing read-only-intended `compass_sub` account as the
poi_credit writer to ship fast (`sql/004_poi_credit.sql:16` TODO). `compass_sub`
is the broadly-used, ssh-tunnel-exposed read account; granting it write on the
PoI ledger widens the blast radius if its credential leaks (an attacker could
poison `cumulative_impact` → manipulate recall boost). Phase 2 enforces least
privilege: `compass_sub` goes back to pure read, a dedicated `poi_writer` role
is the only thing that can touch `compass.poi_credit`.

## Non-goals (YAGNI)

- No multi-row audit log / rotation for poi_credit (Phase 1 decision 6 stands).
- No connection pooling — the reconcile cron is single-shot, one tunnel per run.
- No change to the daemon boost path (it reads the snapshot JSON, never the table).
- Not touching `agent_tool_calls` / `engine_cycle_outcomes` read grants.

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

## 2. Connection split (one tunnel, two connections)

Decision: **single ssh tunnel + two psycopg2 connections** (user-chosen).

- Split the poller's `db_connection` into two reusable pieces:
  - a tunnel context manager (open ssh `-L`, wait for the port, tear down)
  - a connect helper `(cfg, local_port, user, password, readonly) -> conn`
  - keep `db_connection` as a thin backward-compat wrapper composing both, so
    existing callers (`cross_agent_outcome_poller.main`, notifier) are unaffected.
- The reconcile cron opens **one tunnel**, then two connections on it:
  - **read conn** = `compass_sub` (readonly): fetch `agent_tool_calls` outcomes
    from `public`.
  - **write conn** = `poi_writer`: `SET search_path TO compass` →
    `reconcile_central` UPSERT + `fetch_all_credits` snapshot.
- Outcomes are materialized into Python before the write conn is used, so the
  two connections are used sequentially; the tunnel stays up for both.

## 3. Secret provisioning (user-provided)

- New file `~/.claude/plugins/nautilus-compass/.cache/.poi_writer_db_secret`,
  same `key: value` format as `.soul_db_secret` (`password: xxx`; host/port/
  dbname optional, default-inherited from the soul secret / module defaults).
- New env `COMPASS_POI_WRITER_SECRET` (defaults to the path above); reuses
  `parse_secret`.
- **Missing file = honest skip** (same as the current no-secret behavior) — not
  an error. This keeps hosts without the writer credential from crashing.

## 4. Production rollout order (staged, never breaks the running 30-min reconciler)

1. **SQL 005 (additive only)**: CREATE ROLE poi_writer + GRANTs. Does NOT touch
   `compass_sub` → the reconciler keeps running on Phase-1 grants.
2. **User provisions** `.poi_writer_db_secret` (local + cloud, one each).
3. **Deploy split code**, run e2e: dry-run first, then a real run. Verify
   `settled` is normal, snapshot is written, and the write conn authenticates as
   `poi_writer`.
4. **Only after step 3 verifies — SQL 006**: REVOKE compass_sub write + compass
   schema USAGE.
5. **Closing verification** (verification-before-completion):
   - reconciler still green (reads as compass_sub / writes as poi_writer);
   - **negative test**: a write attempt as `compass_sub` on `poi_credit` must
     fail with `permission denied` (proves least privilege actually took effect).

**Rollback**: if anything fails before step 4, just stop (no REVOKE happened
yet). If the reconciler breaks after step 4, re-`GRANT INSERT, UPDATE ON
compass.poi_credit TO compass_sub` (one SQL) returns to the Phase-1 state — no
code rollback needed.

## Testing (TDD, sqlite mock)

Role split lives at the connection layer; sqlite cannot exercise GRANT/REVOKE.
Unit coverage:

- `parse_secret` reads the poi_writer secret;
- missing writer secret → honest skip (no crash, returns 0);
- write conn absent / connect failure → does not crash, honest skip;
- read/write responsibility split: with two mock connections, assert
  `agent_tool_calls` queries only hit the read conn and the `poi_credit` UPSERT
  only hits the write conn.

GRANT/REVOKE and the negative permission test are validated by cloud e2e, not
unit tests.

## Files touched (anticipated)

- `sql/005_poi_writer_role.sql` (new, additive)
- `sql/006_poi_writer_revoke_compass_sub.sql` (new, run after e2e verify)
- `ops/cross_agent_outcome_poller.py` (refactor db_connection → tunnel + connect)
- `ops/poi_reconcile_cron.py` (two-connection reconcile; poi_writer secret load)
- `tests/test_poi_reconcile_cron_roles.py` (new)

## R-guardrail notes

Production DDL → R4 git-state check before ship (main is clean now). REVOKE step
gated behind verification-before-completion (live reconciler + negative write
test). Does not touch V5 / platform-soul turf.
