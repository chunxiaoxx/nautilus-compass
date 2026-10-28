# Handoff #013 · Inc 2 closeout (Slice 5 + 6) BINDING-DONE

**Date:** 2026-05-29 (continuation of Session 4 fresh · post handoff #012)
**Status:** 🟢🟢 Slice 5 + Slice 6 both BINDING-DONE on cloud · PR #75 ready
**Branch:** `worktree-slice5-blessing` (commits `605ee4fbb` Slice 5 + `5f2ec7f5f` Slice 6)
**Cloud branch:** `soul-audit-increment1` HEAD `b0ee38f42`
**Master tip pending merge:** still `b828b84aa`

---

## 1 · What shipped this session

| Slice | Migration | Code | Endpoint | Tests | Cloud verify |
|-------|-----------|------|----------|-------|--------------|
| 5 (blessing) | `e5c8b9a3d1f7_inc2_proposal_blessings.py` + `scripts/cloud_apply_inc2_slice5.sh` | `bless_proposal`, `settle_blessings_for`, `_apply_proposer_blessing_bonus` + wiring | `POST /bless` | 3 (test_inc2_slice5_blessing.py) | 3/3 PASS + HTTP live |
| 6 (collab) | `f6d9e2b8a4c1_inc2_proposal_authors.py` + `scripts/cloud_apply_inc2_slice6.sh` | `_get_proposal_authors` helper + `on_pr_merge_hook` per-author + weight params on D4 + bonus | `POST /` accepts author_ids + vote self-vote check | 3 (test_inc2_slice6_collab.py) | 3/3 PASS + HTTP live |

Total: **+1099 LOC** across 10 files. 6 new tests · 6 pure-unit regression tests green.

## 2 · Inc 2 cumulative BINDING-DONE

After PR #75 merge, Inc 2 is 6/6 complete:

| # | Slice | PR | State |
|---|---|---|---|
| 1 | Settlement core (on_pr_merge_hook + outcomes) | #69 | merged |
| 2 | Soul cycle grade (composite_delta) | #70 | merged |
| 3 | Release/cancel + D4 rep + ledger | #71 | merged |
| 4 | Onboarding capital + progression gates | #73 | merged |
| 4.5 | platform_agents FK pre-check polish | #74 | merged |
| 5 | Blessing mechanism (mentor) | #75 | **pending merge** |
| 6 | Collaborative authorship | #75 | **pending merge** |

End-to-end loop closes: POST (with optional `author_ids`) → vote (rejects all authors) → executor → DeepSeek → draft PR → human merge → `on_pr_merge_hook` (N pending rows per author × weight) → soul cycle grades after 7d → cron release with per-author D4 rep_proposing × weight + per-author ledger varchar-cast + blessing amplification when present.

## 3 · Cloud state diff vs handoff #012

### Schema additions

```
proposal_blessings (Slice 5 · 7 cols + partial idx)
proposal_authors (Slice 6 · 3 cols composite PK)
```

### Data backfill

```
proposal_authors: 12 rows inserted (one per existing proposal · weight=1.0)
```

### Services state

```
nautilus-backend: restarted once for Slice 5 endpoint · once for Slice 6
proposal_blessings table: empty production state (verified)
proposal_authors table: 12 backfill rows · 0 multi-author production rows
```

### Test residue

```
0 leftover test agents (Slice 5 IDs 9_100_50x + Slice 6 IDs 9_100_60x + HTTP probe 9_100_70x · all deleted)
0 leftover test proposals
0 leftover pending_nau_rewards test rows
```

## 4 · Cloud BINDING-DONE evidence

### Slice 5

```
Case A: blesser rep_voting=79.99 → blessed=false reason="not TRUSTED" · 0 rows
Case B: proposer rep_proposing=72.00 → blessed=false reason="not UNTRUSTED" · 0 rows
Case C E2E:
  bless: stake=8.5 (= 85.0 × 0.1)
  idempotent re-bless: blessed=false reason="already blessed"
  settle_blessings_for(Δ=+1.0):
    rep_delta = +1.0 × √1.0 × 3.0 = +3.0
    blesser rep_voting: 85.0 → 88.0
    settled_outcome = '+'
  re-settle: returns []
  _apply_proposer_blessing_bonus(Δ=+1.0):
    rep_delta = +1.0 × √1.0 × 2.0 = +2.0
    proposer rep_proposing: 45.0 → 47.0
HTTP live: POST /bless → 200 envelope with correct reason
```

### Slice 6

```
Case A: legacy proposal · helper returned [(9100603, 1.0)] (fallback to platform_improvement_proposals.agent_id)
Case B multi-author 0.6+0.4:
  helper: {A: 0.6, B: 0.4}
  on_pr_merge_hook(nau_amount=100):
    pending rows: A=60 · B=40
    idempotent re-run: authors_credited=[] · count unchanged
  grade_pending_settlements(stale_hours=0): graded=2
  process_graded_settlements:
    rep_delta A = √0.5 × 5.0 × 0.6 = 2.1213
    rep_delta B = √0.5 × 5.0 × 0.4 = 1.4142
    ratio = 1.5 (exact match to weight ratio 0.6/0.4)
    both fulfilled
Case C: helper author set = {A, B}
HTTP live:
  POST /api/platform/proposals with author_ids=[9100701, 9100702] weights=[0.7, 0.3]
    → 200 envelope · data.authors list returned
  POST /vote as 9100701 → 200 · error="self-vote forbidden · voter is among proposal authors"
  POST /vote as 9100702 → same blocked
```

## 5 · Decisions locked this session

- **Inline vs new file**: Slice 5+6 inlined into `inc2_settlement.py`. Design Section 4 specified `inc2_blessing.py` and (implicitly) `inc2_collab.py`; shipped code consistency (Slice 1-4 single-module) won.
- **Slice 3 voter-rep gap NOT addressed**: existing L339 comment "Slice 5 will add voter rep updates" is stale. Slice 5 scope (per design Section 4) = blessing only. Voter rep is parking lot for separate followup.
- **D4 + bonus weighting**: Slice 6 added optional `weight: float = 1.0` param to `_apply_d4_rep_update` and `_apply_proposer_blessing_bonus`. Single-author defaults preserve Slice 3/5 behavior. Multi-author scales linearly per contribution_weight.
- **Helper fallback**: `_get_proposal_authors` falls back to `(proposal.agent_id, 1.0)` when table missing OR no rows. Backward compat for legacy proposals · defensive against pre-migration test runs.
- **HTTP endpoint validation**: Slice 6 enforces sum=1.0 ± 1e-6, primary submitter in author_ids, unique IDs, all agents exist. Defensive INSERT into proposal_authors with `ON CONFLICT DO NOTHING` in case migration backfill races.
- **PR strategy**: Slice 5 + Slice 6 ship on same branch `worktree-slice5-blessing` → single PR #75 retitled "Inc 2 closeout · Slice 5 (blessing) + Slice 6 (collab authorship)". Atomic merge.

## 6 · Open items 真 carry-over to next session

### Carried from handoff #012

1. **V5 governance dormancy fix** (agent-dialog turf · INBOUND already shipped 5/29 · awaiting V5 dialog answer)
2. **2 borderline soul PRs** #58 #72 (user decide)
3. **GitHub PAT revoke** (carry-over multiple sessions · still pending)
4. **condition (3) 24h auto-settle journal verify** (time gate · 2 fires recorded)
5. **condition (4) production proposal full chain** (waits on V5 fire of soul-check-passing proposal)
6. **soul-audit-increment1 vs origin/master 756 commits sync** (long-term)

### New from this session

7. **Slice 3 voter-rep gap closeout** (D4 voter formula at settle · separate followup PR · ~2h)
8. **PR #75 merge to master** (user decides · this is the Inc 2 closeout merge)
9. **Inc 3 design start** (discover endpoint real impl · public leaderboard · clawback · etc · parking lot)

## 7 · Key file entry points

### Design

```
docs/plans/2026-05-28-inc2-nau-settlement-design.md (Section 4 Slice 5+6)
```

### Handoffs (this session)

```
docs/HANDOFF_20260529_012_final_session3_marathon.md (predecessor)
docs/HANDOFF_20260529_013_inc2_closeout.md (this)
```

### Slice 5 + 6 code (on PR #75 / `worktree-slice5-blessing` branch)

```
phase3/backend/services/inc2_settlement.py (Slice 1-6 single module · 7 fns + 2 helpers)
phase3/backend/api/platform_proposals.py (POST + vote + bless endpoint)
phase3/backend/alembic/versions/e5c8b9a3d1f7_inc2_proposal_blessings.py
phase3/backend/alembic/versions/f6d9e2b8a4c1_inc2_proposal_authors.py
phase3/backend/tests/test_inc2_slice5_blessing.py
phase3/backend/tests/test_inc2_slice6_collab.py
scripts/cloud_apply_inc2_slice5.sh
scripts/cloud_apply_inc2_slice6.sh
```

### Cloud verify scripts (transient · `/tmp/`)

```
/tmp/verify_slice5_cloud.py (3/3 pass)
/tmp/verify_slice6_cloud.py (3/3 pass)
```

## 8 · `claude --continue` pickup pattern

```bash
# fresh session 第 1 句话:
"接 handoff #013 · Inc 2 closed · 选项: (a) merge PR #75 (b) Slice 3 voter-rep gap closeout (c) V5 dormancy answer review (d) Inc 3 design start"
```

预估各路径:
- (a) merge + cloud sync = ~30min
- (b) Slice 3 voter-rep closeout = ~2h fresh session
- (c) V5 dormancy answer reading + design = ~1h depending on inbound response
- (d) Inc 3 design = ~3-4h brainstorm + writing-plans

---

🤖 Generated with [Claude Code](https://claude.com/claude-code) (Opus 4.7 · 1M context)
