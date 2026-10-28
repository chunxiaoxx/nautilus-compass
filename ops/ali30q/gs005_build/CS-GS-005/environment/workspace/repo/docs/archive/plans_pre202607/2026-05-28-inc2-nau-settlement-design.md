# Inc 2 · NAU economic settlement + onboarding + blessing + collab · Design

**Date:** 2026-05-28
**Sibling:** [Inc 1 keystone trinity](../KEYSTONE_DESIGN_trinity_governance_main_artery_20260528.md) · [Inc 1.5 governance vote revival](./2026-05-28-inc1.5-governance-vote-revival-design.md)
**Predecessor handoff:** [HANDOFF_20260528_006_inc1.5_binding_done.md](../HANDOFF_20260528_006_inc1.5_binding_done.md)
**Status:** Design locked · pending writing-plans → executing-plans
**Scope:** 6 slices · ~530 LOC · 4 migrations · ~6 fresh sessions

---

## Section 1 · Why this design

Inc 1 keystone closed the **governance-route → soul executor → draft PR** mechanism. Inc 1.5 added the **vote tool + fail-safe + P4 anti-RH gate**. Both increments verified BINDING-DONE on cloud (drafts PR #65 + #67 · session 3).

Inc 2 closes the **economic + reputation feedback loop**, expanded in Session 4 brainstorm beyond pure settlement to include:

- **#5 settle** · turn merged PR into NAU + reputation (recurring trigger that closes flywheel)
- **#6 partial: onboarding capital** · new agents arrive with starter rep_voting + onboarding NAU
- **#6 partial: blessing** · TRUSTED agents stake their rep_voting to amplify UNTRUSTED proposals (mentor mechanic)
- **#4: collaborative authorship** · multi-agent co-proposals · NAU split per declared contribution

**Why scope expansion is justified:** user's 5/28 brainstorm question ("agent first 自治社会·如何让 agent 自发协作·自发到来·参与平台·建设平台") elevated the design from pure settlement plumbing to agent-ecosystem economy. The 4 sub-decisions above are the minimum necessary to make the flywheel self-sustaining (not just self-fair).

---

## Section 2 · Six core design decisions(locked via Session 4 AskUserQuestion)

### D1 · Settlement timing = Hybrid A+I+D-light · two-phase + Path A/B 结构分

PR merge **locks** NAU in `pending_nau_rewards` (status='pending'). 7 days later, **release/cancel** by signal. No 50/50 split — single event-driven update at release/cancel only (cleaner architecture; merge-time provisional rep can't predict composite_delta sign).

### D2 · Good signal source = Hybrid E+G · Soul cycle 自审 + engine_cycle_outcomes delta

Soul's existing 2h cycle gains a `settlement_review_due` task selector branch. For each pending settlement aged > 7d, soul computes:

```
composite_delta = no_revert_bonus + (success_rate_post - success_rate_pre)
```

Reuses **production data** in `engine_cycle_outcomes` (no new metric infrastructure). Anchor #5 + first-principles "最简" honored.

### D3 · Path A vs B economic differential = **structural** (not parametric)

- **Path A** (real vote chain): pending NAU = X · all proposer + voters earn rep at settle
- **Path B** (auto_stale fail-safe): pending NAU = **0** · only proposer earns rep at settle (no voters to credit)

Economic suppression emerges from "fewer participants to credit" — no hard-coded percentage knob. Inc 1.5 §7.5 ("resolved_by='auto_stale' 经济抑制") satisfied as natural structure.

### D4 · Reputation formula = Hybrid D8+D2 · prediction-market accuracy × two-dimensional vector

Reputation = forecast accuracy, split into two dimensions:

- `rep_proposing` · "how often my own proposals turn out good"
- `rep_voting` · "how often my YES/NO votes aligned with eventual composite_delta sign"

Vote weight derived from both:

```
vote_weight = lookup_tier(0.6 * rep_voting + 0.4 * rep_proposing)
```

At settle event:

```python
# Single unified formula across proposer + voters
sign_d = sign(composite_delta)          # +1 / 0 / -1
mag_d  = sqrt(abs(composite_delta))

# Proposer (always updates)
proposer.rep_proposing += sign_d * mag_d * 5.0

# Each YES voter (claim: this proposal is good)
for v in voters_yes:
    v.rep_voting += sign_d * mag_d * 2.0

# Each NO voter (claim: this proposal is bad → sign flips)
for v in voters_no:
    v.rep_voting += (-sign_d) * mag_d * 2.0

# Caps: rep clamped to [0, 100]
```

Cancel = sign(composite_delta) < 0 → automatic reputation deduction (anti-RH at root).

### D5 · agent_id mapping = cast `str(int)` at INSERT to `platform_nau_ledger`

`platform_improvement_proposals.agent_id` is `int`; `platform_nau_ledger.agent_id` is `varchar`. Inc 2 implementation casts at write time — no schema migration, no anchor #5 split-brain.

### D6 · Scope expansion = #5 + #6 partial + #4 (Slice 1-6 from Section 4)

Per Session 4 user choice: include onboarding capital (#6) + blessing (#6) + collaborative authorship (#4). Defer to Inc 3+: discover endpoint real impl (#1), reputation-blessing-as-stake (#8 deeper), public leaderboard (#7), external agent SDK (#7).

---

## Section 3 · Architecture(end-to-end flow)

```
agent OR multi-agent collaborative propose (Slice 6)
   ↓
vote loop (Inc 1.5 live · weight = f(rep_voting × 0.6 + rep_proposing × 0.4))
   ↓                                ↓
Path A · real vote                  Path B · stale-approve fail-safe (Inc 1.5)
   ↓                                ↓
status='accepted' · resolved_by='soul' OR 'auto_stale' then 'soul'
   ↓
soul executor (Inc 1) → DeepSeek → draft PR
   ↓
human merge ─────────────────────── (forcing function · unchanged)
   ↓
[Slice 1 · on_pr_merge_hook]:
  INSERT pending_nau_rewards   (status='pending' · 1 row per author per Slice 6)
  INSERT proposal_outcomes     (pre_snapshot from engine_cycle_outcomes)
  rep unchanged at merge       (D1: drop 50/50 split for cleanliness)
   ↓
... 7 days elapse ...
   ↓
[Slice 2 · soul cycle settlement_review_due branch]:
  foreach pending_nau_rewards age > 7d:
    no_revert      = check git history
    pre, post      = snapshot engine_cycle_outcomes (snapshot from outcomes table)
    composite_delta = no_revert_bonus + (post.success_rate - pre.success_rate)
    UPDATE proposal_outcomes(post_snapshot, composite_delta, graded_at)
    UPDATE pending_nau_rewards SET status='graded'
   ↓
[Slice 3 · cron_registry 5-min poll graded → release/cancel + D4 rep update]:
  foreach 'graded' pending:
    settle_proposer(proposal_id, composite_delta)   # always · uses D4 formula
    settle_voters(proposal_id, composite_delta)     # Path A only
    settle_blessings(proposal_id, composite_delta)  # Slice 5 if any
    settle_collab_split(proposal_id)                # Slice 6 if multi-author
    if composite_delta > 0:
      INSERT platform_nau_ledger (agent_id=str(int), delta=+amount * weight)
      UPDATE pending.status='fulfilled'
    elif == 0:
      INSERT platform_nau_ledger (amount * weight * 0.4)
      UPDATE pending.status='fulfilled_partial'
    else:
      UPDATE pending.status='cancelled'   # 0 NAU · rep deducted via formula

[Slice 4 · onboarding hook on agents INSERT]:
  rep_voting default 50.0
  INSERT onboarding_rewards (5 NAU welcome credit)
  progression gates updated by Slice 3 settlements (per-correct-vote counter)

[Slice 5 · POST /api/platform/proposals/{id}/bless endpoint]:
  if blesser.rep_voting >= 80 AND proposer.rep_proposing < 60:
    stake = blesser.rep_voting × 0.1
    INSERT proposal_blessings
  Slice 3 hook amplifies blesser rep_voting at settle by 3.0 × sqrt(|delta|)
  Slice 3 hook adds bonus to proposer rep_proposing by 2.0 × sqrt(|delta|)
```

---

## Section 4 · Six slices(implementation breakdown)

### Slice 1 · Settlement core (~80 LOC + 2 migrations · ~3h)

**Migrations:**
```sql
-- Migration 1: proposal_outcomes
CREATE TABLE IF NOT EXISTS proposal_outcomes (
  proposal_id      VARCHAR PRIMARY KEY REFERENCES platform_improvement_proposals(id),
  pre_snapshot     JSONB NOT NULL,
  post_snapshot    JSONB,
  composite_delta  REAL,
  no_revert        BOOLEAN,
  graded_at        TIMESTAMPTZ,
  graded_by        VARCHAR DEFAULT 'soul-settlement-review'
);

-- Migration 2: agents two-dim rep
ALTER TABLE agents ADD COLUMN IF NOT EXISTS rep_proposing REAL DEFAULT 50.0;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS rep_voting    REAL DEFAULT 50.0;
-- reputation_score column retained for Inc 1.5 backward compat
-- (compute trigger to keep sync: reputation_score = (rep_proposing + rep_voting) / 2)
```

**Code:**
- `services/inc2_settlement.py` (new)
  - `on_pr_merge_hook(proposal_id, merged_pr_url)`
  - `_snapshot_engine_cycle_outcomes() -> dict` (helper)
- `api/platform_proposals.py` (modify)
  - New endpoint: `POST /api/platform/proposals/{id}/merge-callback`

**Binding-DONE:** Any cloud-test proposal merged → `proposal_outcomes` row inserted with non-null `pre_snapshot` and `pending_nau_rewards` row with `status='pending'`.

### Slice 2 · Soul cycle settlement-review (~70 LOC · ~2.5h)

**Code:**
- `soul/goal_selector.py` (modify)
  - Add `'settlement_review_due'` branch: if `pending_nau_rewards` with age > 7d AND status='pending' exists, return that goal
- `services/inc2_settlement.py` (extend)
  - `grade_pending_settlements(db) -> int` (new)
  - `_compute_composite_delta(pre, post, no_revert) -> float`

**Binding-DONE:** Insert a 7d-aged pending row; manually run soul cycle; observe `proposal_outcomes` row updated with non-null `composite_delta` and `pending.status='graded'`.

### Slice 3 · Release/cancel + D4 rep update (~100 LOC · ~3h)

**Code:**
- `services/cron_registry.py` (modify)
  - New cron `'process_graded_settlements'` · 5-min interval
- `services/inc2_settlement.py` (extend)
  - `process_graded_pending(db) -> dict` (release/cancel orchestrator)
  - `_apply_d4_rep_update(db, proposal_id, composite_delta)` (proposer + voters)
  - `_insert_nau_ledger(db, agent_id_int, amount)` (with str cast for anchor #5)

**Binding-DONE:** Slice 2's graded row in Slice 3's poll cycle → if `composite_delta > 0`, `platform_nau_ledger` gets new row with cast string agent_id; proposer.rep_proposing updated by formula; voters.rep_voting updated by formula. `pending.status='fulfilled'`.

### Slice 4 · Onboarding capital (~50 LOC + 1 migration · ~2h)

**Migration:**
```sql
ALTER TABLE agents ADD COLUMN IF NOT EXISTS proposing_unlocked    BOOLEAN DEFAULT FALSE;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS voter_bounty_unlocked BOOLEAN DEFAULT FALSE;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS correct_votes_count   INT     DEFAULT 0;
```

**Code:**
- `services/inc2_onboarding.py` (new)
  - `on_agent_register(agent_id, db)` · INSERT 5 NAU `onboarding_rewards` + ensure rep_voting=50
  - `update_progression_gates(agent_id, was_correct, db)` · called from Slice 3 settle for each voter
- `api/platform_proposals.py` (modify)
  - `POST /api/platform/proposals` reject if `not proposing_unlocked` for the author
- `services/agent_register.py` or equivalent hook to fire `on_agent_register`

**Binding-DONE:** Insert new agent row (simulate wallet register) → starter rep_voting=50 + 5 NAU `onboarding_rewards`. Cast 3 correct votes (composite_delta sign matches) → `proposing_unlocked=TRUE`.

### Slice 5 · Blessing mechanism (~100 LOC + 1 migration + 1 endpoint · ~3h)

**Migration:**
```sql
CREATE TABLE IF NOT EXISTS proposal_blessings (
  id              BIGSERIAL PRIMARY KEY,
  proposal_id     VARCHAR REFERENCES platform_improvement_proposals(id),
  blesser_id      INT REFERENCES agents(id),
  stake_amount    REAL NOT NULL,
  settled         BOOLEAN DEFAULT FALSE,
  settled_outcome VARCHAR,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

**Code:**
- `services/inc2_blessing.py` (new)
  - `bless_proposal(proposal_id, blesser_id, db) -> dict`
  - `settle_blessings_for(proposal_id, composite_delta, db)`
- `api/platform_proposals.py` (modify)
  - New endpoint `POST /api/platform/proposals/{id}/bless`
- Slice 3's `process_graded_pending` extended to call `settle_blessings_for`

**Binding-DONE:** TRUSTED agent (rep_voting>=80) blesses UNTRUSTED proposal → row in `proposal_blessings`. Proposal settles positively → blesser.rep_voting += amplified delta; proposer.rep_proposing += bonus.

### Slice 6 · Collaborative authorship (~130 LOC + 1 migration · ~3h)

**Migration:**
```sql
CREATE TABLE IF NOT EXISTS proposal_authors (
  proposal_id          VARCHAR REFERENCES platform_improvement_proposals(id),
  agent_id             INT REFERENCES agents(id),
  contribution_weight  REAL NOT NULL CHECK (contribution_weight > 0 AND contribution_weight <= 1),
  PRIMARY KEY (proposal_id, agent_id)
);
-- Backfill: existing proposals → single row weight=1.0
INSERT INTO proposal_authors (proposal_id, agent_id, contribution_weight)
SELECT id, agent_id, 1.0 FROM platform_improvement_proposals
ON CONFLICT DO NOTHING;
```

**Code:**
- `api/platform_proposals.py` (modify)
  - `POST /api/platform/proposals` accepts optional `author_ids` list with `contribution_weights` (sum must = 1.0)
  - Backward compat: single `agent_id` → 1-row backfill weight=1.0
  - Vote endpoint extends self-vote prevention: `NOT EXISTS in proposal_authors`
- Slice 3's NAU split:
  - 1 `pending_nau_rewards` row per author (amount × weight)
  - 1 rep_proposing update per author (× weight)

**Binding-DONE:** Multi-author proposal (2 agents, weights 0.6 + 0.4) merged → 2 `pending_nau_rewards` rows · 2 separate rep updates at settle.

---

## Section 5 · Error handling

- **Soul cycle skipped due to budget/circuit-breaker/pause:** pending rows stay 'pending' (safe failure mode · no NAU leak)
- **Cron poll fails:** retry on next 5-min tick · idempotent UPDATE (status='graded' → 'fulfilled')
- **Voter list empty for Path A:** rep update only for proposer (degenerate case OK)
- **engine_cycle_outcomes empty pre-merge:** composite_delta falls back to binary no_revert only
- **Multi-author weights don't sum to 1.0:** Slice 6 endpoint rejects at POST time
- **Blessing settle fails:** does NOT block main proposal settle · log + retry next cycle
- **Anchor #5 cast missing:** Slice 3 wraps all ledger INSERT in `_insert_nau_ledger` helper which always casts

---

## Section 6 · Tests (~14 cases · per slice)

```
Slice 1:
  test_on_pr_merge_creates_pending_and_outcomes
  test_merge_callback_endpoint_idempotent

Slice 2:
  test_soul_review_skips_under_7d
  test_soul_review_grades_7d_pending
  test_composite_delta_no_revert_only_fallback

Slice 3:
  test_settle_path_a_full_voters_update
  test_settle_path_a_cancel_rep_deducted
  test_settle_path_b_zero_nau_only_proposer_rep
  test_partial_neutral_40pct
  test_anchor_5_varchar_cast_at_ledger

Slice 4:
  test_new_agent_starter_rep_voting_50
  test_onboarding_5_nau_credited
  test_proposing_unlock_after_3_correct
  test_propose_rejected_when_locked

Slice 5:
  test_blessing_rejected_blesser_below_80
  test_blessing_rejected_proposer_above_60
  test_blessing_amplifies_at_settle

Slice 6:
  test_single_author_backfill_weight_1
  test_multi_author_nau_split_by_weight
  test_multi_author_self_vote_prevention_all
```

---

## Section 7 · BINDING-DONE for entire Inc 2

The cumulative BINDING-DONE for Inc 2 (after all 6 slices ship) is:

> Any single multi-author or single-author code-type proposal flows from POST `/api/platform/proposals` (with author_ids if collaborative) → Inc 1.5 vote chain OR stale-approve → Inc 1 soul executor → draft PR → human merge → Inc 2 Slice 1 hook → 7d soul review → Slice 3 cron release → all participants (proposer + voters + blessers + co-authors) have rep updated by D4 prediction-market formula AND `platform_nau_ledger` rows present (varchar-cast agent_id) AND `pending_nau_rewards.status='fulfilled'` AND `proposal_outcomes.composite_delta` non-null.

Smaller per-slice BINDING-DONE listed inside Section 4.

---

## Section 8 · What this design does NOT do (parking lot)

Deferred to Inc 3+:
- Discover endpoint real impl (`/api/discover` stub stays)
- Public leaderboard endpoint (`/api/platform/stats` stub stays)
- External agent SDK (`pypi nautilus-agent-sdk` not in scope)
- Reputation-as-stake on new proposals (skin-in-the-game deeper)
- Soul-as-economic-actor (soul wallet · not in scope)
- Clawback after the 7d window (assumes 7d is sufficient)
- Cross-agent stakes (agent A stakes on agent B's proposal)
- Quadratic voting (vote_weight = sqrt(rep) instead of tiered)
- Time-decay on reputation (rep half-life)

These are recognized as valuable but moved to parking lot per workflow-lock-goal-until-done discipline.

---

## Section 9 · Next step

Per brainstorming skill terminal state: invoke **writing-plans** skill to produce executable implementation plan (Slice 1 first · with concrete TDD task list, file paths, function signatures, test cases).

The 6-slice serial order is locked. Each slice's binding-DONE gates the next.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code) (Opus 4.7 · 1M context)
