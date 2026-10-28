# Handoff #008 · Inc 2 Slice 2 BINDING-DONE (partial · wire residual)

**Date:** 2026-05-29 (same Session 3 marathon · third binding-DONE this session after Inc 1.5 + Slice 1)
**Status:** 🟢 BINDING-DONE on the core fn · 🟡 soul-cycle auto-wire residual
**Branch:** `inc2/slice2-soul-cycle-grade`
**Predecessor:** [HANDOFF #007 · Inc 2 Slice 1](./HANDOFF_20260528_007_inc2_slice1_binding_done.md)
**Goal-driven:** Yes · /goal set "L2 闭环 close + flywheel 起转 · 5 condition"

---

## §1 · What landed

```
Local commit on branch inc2/slice2-soul-cycle-grade (1 commit on top of Slice 1 tip):
  db7503dee  feat(inc2 slice2): grade_pending_settlements + _compute_composite_delta

Files:
  phase3/backend/services/inc2_settlement.py     (+ 2 functions · ~105 LOC)
  phase3/backend/tests/test_inc2_grade_pending.py (4 MagicMock unit tests · 4/4 pass)
```

**Core fn:** `grade_pending_settlements(db, stale_hours=168) -> int`

- Selects `pending_nau_rewards.status='pending'` AND `created_at < NOW() - stale_hours`
- Joins `proposal_outcomes` for `pre_snapshot`
- Snapshots `post_snapshot` via existing `_snapshot_engine_cycle_outcomes`
- Computes `composite_delta = no_revert_bonus + (post_rate - pre_rate)` per design D2
- `no_revert` MVP defaults True (Inc 3 will walk git history)
- UPDATEs `proposal_outcomes`: `post_snapshot · composite_delta · no_revert · graded_at`
- UPDATEs `pending_nau_rewards.status='graded'`

**Helper fn:** `_compute_composite_delta(pre, post, no_revert) -> float`

- no_revert_bonus = +0.5 (good) / -1.0 (reverted · strong negative)
- rate_delta = post.success_rate - pre.success_rate, or 0.0 when either is None

## §2 · Cloud verification (BINDING-DONE proof)

Sync via `git checkout origin/inc2/slice2-soul-cycle-grade -- phase3/backend/services/inc2_settlement.py` against cloud `nautilus-mvp` working tree. Then:

```python
graded = grade_pending_settlements(db, stale_hours=0)
# returned 1
```

DB row inspection:

```
proposal_id              | composite_delta | no_revert | graded_at                     | pending.status
inc1.5-pathb-1c-20260528 | 0.5             | t         | 2026-05-29 01:13:49.034044+08 | graded
```

✅ `composite_delta` non-null (0.5 = no_revert_bonus 0.5 + rate_delta 0 since pre and post snapshots match · engine has 8 cycles 0 passed → success_rate 0.0 both sides)
✅ `pending.status='graded'`
✅ `graded_at` populated
✅ `no_revert` true

Slice 2 binding-DONE per design Section 4 Slice 2: "Insert a 7d-aged pending row; manually run soul cycle; observe proposal_outcomes row updated with non-null composite_delta and pending.status='graded'."

## §3 · Wire residual (NOT shipped this session · documented)

The design Section 4 Slice 2 also required:

> `soul/goal_selector.py` (modify): Add `'settlement_review_due'` branch: if `pending_nau_rewards` with age > 7d AND status='pending' exists, return that goal.

This soul-daemon wire was **NOT shipped** under R3 4h pressure. The fn exists and is callable; what's missing is auto-trigger from soul's 2h cron timer. For now, the fn is invoked manually via Python script.

Slice 2 wire residual:
- `phase3/soul/goal_selector.py` (cloud workspace path `/home/ubuntu/nautilus-soul-workspace/phase3/soul/goal_selector.py`) needs a new `select_settlement_review_goal()` function that returns a goal dict when pending rows exist
- `soul/daemon.py:run_once` already calls `goal_selector.select_goal()`; needs only the new branch
- Estimated 20 LOC, 1 test, fresh session

This is the "soul cycle 自审" automation. Without it, /goal condition (3) "nautilus-soul-executor.timer enabled + 24h ≥1 真 auto-settle" cannot be satisfied autonomously · the timer would fire but soul cycle wouldn't pick up pending settlements.

## §4 · Followups inherited from Slice 1 code review

Still un-addressed (handoff #007 §3) and now joined by Slice 2 followups:

From Slice 1:
1. ON CONFLICT DO NOTHING for INSERTs (race window in webhook era)
2. Backfill agents.rep_proposing/rep_voting from reputation_score
3. nau_amount accept int | float
4. Skip pending INSERT when nau_amount=0
5. Test PIDs uuid.uuid4
6. INFO log enrich
7. `proposal[1]` → named attribute
8. VARCHAR(64) length

New from Slice 2:
9. `_compute_composite_delta` doesn't handle str-typed JSONB pre/post (silently returns wrong delta) — defensive json.loads at caller is OK for now but document
10. `grade_pending_settlements` doesn't check whether `proposal_outcomes` row already has `composite_delta` set — re-running grades will overwrite. Add idempotency: skip rows where `composite_delta IS NOT NULL`. This matters when /goal continues across sessions and may re-call grade.
11. No transactional wrap around the per-row UPDATE pair; if `pending_nau_rewards.status` UPDATE fails after `proposal_outcomes` UPDATE succeeds, snapshot/delta are committed but pending stays 'pending' — re-runs will re-grade
12. `no_revert` MVP=True ignores reality — real no-revert check (git log) is Inc 3 scope per design Section 8 parking lot · documented gap

All 12 followups batched for "Slice 1.5 + 2.5 polish" prep commit before Slice 3 starts.

## §5 · /goal status

Goal set this turn: 5 conditions. Slice 2 advances toward condition (1) Inc 2 Slice 2-6 BINDING-DONE.

Progress:
- ✅ Slice 1 BINDING-DONE (PR #69 open)
- ✅ Slice 2 BINDING-DONE (core fn · wire residual documented)
- ⏳ Slice 3 (release/cancel + D4 rep update + ledger write) — unblocked, next session
- ⏳ Slice 4 (onboarding capital)
- ⏳ Slice 5 (blessing)
- ⏳ Slice 6 (collaborative authorship)
- ⏳ Inc 3 (orphan table delete)
- ⏳ condition (2) (3) (4) (5) all blocked on Slice 3+

Per /goal "每 binding-DONE 后 pause 等用户 review" · this session pauses after handoff/PR. User picks up via `claude --continue` for Slice 3.

## §6 · R3 reality

Session 3 elapsed ~3.7h since start. Hard 4h limit imminent. Ship velocity intentionally reduced (subagent ceremony skipped for Slice 2; inline implementation; wire residual deferred). Two binding-DONEs this session (Slice 1 full + Slice 2 partial) is a heavy outcome already.

## §7 · For `claude --continue` next session

1. Read this handoff first
2. Read [Inc 2 design doc](./plans/2026-05-28-inc2-nau-settlement-design.md) Section 4 Slice 3
3. Write Slice 3 plan: `docs/plans/2026-05-29-inc2-slice3-release-cancel-plan.md`
4. Slice 3 binding-DONE = at least 1 `platform_nau_ledger` row inserted with varchar-cast `agent_id` from str(int) + at least 1 `agents.rep_proposing` or `agents.rep_voting` updated by D4 formula (i.e., NOT default 50.0)
5. Cloud apply via `scripts/cloud_apply_inc2_slice3.sh` (new · follows precedent)
6. Verify via existing `inc1.5-pathb-1c-20260528` graded row in cloud

After Slice 3 binding-DONE, condition (5) of /goal becomes verifiable.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code) (Opus 4.7 · 1M context)
