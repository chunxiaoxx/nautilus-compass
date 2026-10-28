# Handoff #007 · Inc 2 Slice 1 BINDING-DONE

**Date:** 2026-05-28 (same Session 3 as Inc 1.5 BINDING-DONE)
**Status:** 🟢 BINDING-DONE end-to-end on cloud
**Branch:** `inc2/slice1-settlement-core`
**Predecessor:** [HANDOFF_20260528_006](./HANDOFF_20260528_006_inc1.5_binding_done.md)
**Plan:** [2026-05-28-inc2-slice1-settlement-core-plan.md](./plans/2026-05-28-inc2-slice1-settlement-core-plan.md)
**Design:** [2026-05-28-inc2-nau-settlement-design.md](./plans/2026-05-28-inc2-nau-settlement-design.md)

---

## Section 1 · BINDING-DONE evidence

Cloud smoke test against Inc 1.5 sentinel `inc1.5-pathb-1c-20260528` (handoff #006 §1.3 audit row):

### Happy path
```
POST /api/platform/proposals/inc1.5-pathb-1c-20260528/merge-callback
  Body: {"merged_pr_url":"https://github.com/chunxiaoxx/nautilus-core/pull/65","nau_amount":10}
Response: {"success":true,"data":{"proposal_id":"inc1.5-pathb-1c-20260528","pending_created":true,"outcomes_created":true},"error":null}
```

### Idempotency proof (re-fire same body)
```
Response: {"success":true,"data":{"proposal_id":"inc1.5-pathb-1c-20260528","pending_created":false,"outcomes_created":false},"error":null}
```

### DB state
```
proposal_id              | pre_snapshot                                                  | composite_delta | amount | status
inc1.5-pathb-1c-20260528 | {"success_rate":0.0,"total_cycles":8,"successful_cycles":0}   | NULL            | 10     | pending
```

Slice 1's binding criterion is met verbatim: `proposal_outcomes` row inserted with non-null `pre_snapshot` AND `pending_nau_rewards` row with `status='pending'`. `composite_delta` stays NULL until Slice 2 grades it (correct · Slice 1 doesn't grade).

---

## Section 2 · What landed

### On master (this session prior · before Slice 1)
- Inc 1.5 PRs #62 + #42 + handoff #006 + fix PR #66 + 9 stubs inbound + Inc 2 design v3 + Inc 2 Slice 1 plan
- Master tip prior: `80182533d`

### On branch `inc2/slice1-settlement-core` (Slice 1 work · 7 commits)
- `6b4831419` Task 1: proposal_outcomes table migration + test
- `6d831197a` Task 2: agents rep_proposing + rep_voting columns
- `d105fb222` Task 3: _snapshot_engine_cycle_outcomes helper
- `07356ceca` Task 4: on_pr_merge_hook idempotent settlement on-ramp
- `8420a2e89` Task 5: POST /api/platform/proposals/{id}/merge-callback
- `63d7534d3` cloud raw-SQL apply script
- `0cf5a82af` schema reality fix · semantic_pass AND tests_pass

### On cloud (`nautilus-mvp` working tree · not committed to soul-audit-increment1)
- Raw SQL migrations applied via `scripts/cloud_apply_inc2_slice1.sh`:
  - `proposal_outcomes` table created (0 rows initially · 1 row after smoke test)
  - `agents.rep_proposing REAL DEFAULT 50.0` added (337 rows · all default-initialized)
  - `agents.rep_voting REAL DEFAULT 50.0` added (same · all default 50.0)
- Runtime files synced via `git checkout origin/inc2/slice1-settlement-core -- <files>`:
  - `phase3/backend/services/inc2_settlement.py` (new · 4204 bytes · 2 functions)
  - `phase3/backend/api/platform_proposals.py` (modified · merge-callback endpoint appended at line 328)
- `nautilus-backend` restarted · clean start · 0 NRestarts · endpoint live at line 364 of platform_proposals.py

---

## Section 3 · Followups (code quality review · address before Slice 2)

The code-quality reviewer marked **Approve-with-followups** · 0 Critical · 12 Important · 7 Minor. Highest-priority items to address as a "Slice 1.5 polish" prep commit before Slice 2 starts:

1. **`ON CONFLICT DO NOTHING`** for both INSERTs to harden race window when Slice 2 timer + Inc 3 webhook open concurrent paths (Important #2)
2. **`rep_proposing/rep_voting` default 50.0 vs production reputation_score migration**: 337 existing rows all initialized to mid-tier 50.0 · semantically erases existing TRUSTED/UNTRUSTED tier distribution from the two-dim view. Backfill via `reputation_score` value in same migration is required before Slice 3 sync trigger lands (Important #9)
3. **`nau_amount`** accept `int | float` (Important #3 · Inc 3 Path B fractional rewards)
4. **Skip `pending_nau_rewards` INSERT when `nau_amount == 0`** (Important #4 · wasteful queue rows)
5. **Test PIDs**: switch to `uuid.uuid4()` to avoid CI collision (Important #7 · #8)
6. **INFO log enrichment**: add `merged_pr_url + nau_amount` (Important #6 · operability)
7. **`proposal[1]` → `proposal.agent_id`** named attribute access (Important #12 · style)
8. **`VARCHAR(64)`** length on proposal_outcomes.proposal_id (Important #10 · matches sibling tables)

Full list in code-quality review output (Session 3).

---

## Section 4 · Real bug caught during binding-done (good signal)

The plan's `_snapshot_engine_cycle_outcomes` SQL assumed `engine_cycle_outcomes.passed BOOLEAN`. Production reality: schema has `semantic_pass BOOLEAN` + `tests_pass BOOLEAN`. Caught at first smoke test against cloud. Fixed in commit `0cf5a82af` and re-verified. The code-quality reviewer had flagged this as Minor #13 ("opaque SQL error if `passed` column missing") · the smoke test made it visible.

**This is the right pattern.** TDD + cloud verify catches gap that local-only testing would have hidden behind `pytest.mark.skipif`.

---

## Section 5 · What this unlocks

Slice 1 is the on-ramp. Subsequent slices are now unblocked (each gated by prior slice's binding-DONE):

| Slice | Next step | Unblocked by | Status |
|---|---|---|---|
| 2 | Soul cycle settlement_review_due branch · grade pending → graded | Slice 1 (pending rows exist) | ⏳ ready to plan |
| 3 | Cron poll graded → release/cancel + D4 rep update + ledger write | Slice 2 (graded rows exist) | ⏳ blocked on Slice 2 |
| 4 | Onboarding capital + progression gates | Slice 1 (settlements drive correct_votes_count) | ⏳ partly blocked on Slice 3 |
| 5 | Blessing mechanism | Slice 4 (TRUSTED/UNTRUSTED determined) | ⏳ blocked on Slice 4 |
| 6 | Collaborative authorship | Slice 3 (NAU split needs settlement infra) | ⏳ blocked on Slice 3 |

---

## Section 6 · Finishing instructions for Session 3 close

Branch `inc2/slice1-settlement-core` is ready for merge. Per finishing-a-development-branch skill:
- Tests verified (8 collected · 2 MagicMock executed locally · 6 Postgres-only skip locally · cloud-side smoke + idempotency passed)
- Real bug caught + fixed inline (commit `0cf5a82af`)
- Cloud schema applied · backend live · endpoint serving

Recommended: PR to master so the master tip stays auditable + the followup list (Section 3) lives in the PR thread.

---

## Section 7 · Carry-over

- 🔴 GitHub PAT revoke pending (security · from Inc 1 carry-over) — unchanged
- 🟡 nautilus-soul-executor.timer disabled (user-gate) — unchanged from handoff #006
- 🟡 V5 `_governance_inject_loop` autonomous fire on `inc1.5-patha-target-20260528` — unchanged (observe-only)
- 🟡 Cloud `soul-audit-increment1` branch 756+ commits behind origin/master — unchanged
- 🆕 9 router stubs inbound to agent-dialog (handoff #006 §5 item 2) — unchanged
- 🆕 12 Slice 1 followups in Section 3 above — Slice 2 prep

---

🤖 Generated with [Claude Code](https://claude.com/claude-code) (Opus 4.7 · 1M context)
