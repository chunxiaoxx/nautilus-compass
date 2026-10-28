# Keystone · Trinity closed-loop via governance main artery (2026-05-28)

> Platform-dialog. Architectural lock-in BEFORE code. Frozen scope, binding-DONE
> per increment, parking lot at the bottom. Companion to:
> `INBOUND_TO_AGENT_DIALOG_20260528_governance_main_table_correction.md`.

## What this is

The aggressive answer to "how to make soul × agent × platform actually 1+1+1 > N." Today they are three organs with their own closed loops but no shared circulation. This redesign makes **governance the main artery** and **soul a vote-routed executor terminal** alongside the existing sandbox terminal. Every accepted proposal — sandbox or code — gets economic settlement (NAU) and a measurement feedback (composite-score delta) that updates reputation, which biases the next round's votes.

That is the loop. Not "soul improves soul" (self-editing). Not "agent thinks alone" (no execution). Not "platform pays for tasks" (no recursion). The three braided into one.

## The architecture in one diagram

```
agent.reflect()
  └─ POST /api/platform/proposals
        proposed_change = {type: "code"|"experiment"|..., task, target_module?, ...}
        ↓
  governance vote (reputation-weighted · EXISTING)
        ↓
   status = accepted
        ↓
   ┌──── change_type routing (NEW) ────┐
   │                                   │
   type=experiment              type=code
        ↓                            ↓
   sandbox experiment        soul executor
   (EXISTING)                 (rename from soul_consumer
                              · read from THIS table
                              · not the orphan queue)
        ↓                            ↓
   experiment outcome         DRAFT PR → human merge gate (UNCHANGED)
        ↓                            ↓
   composite_score delta (NEW hook · uses v_engine_progress + engine_cycle_outcomes)
        ↓
   NAU settlement (proposer · yes-voters · no-voters · soul service fee)
        ↓
   reputation update → next vote weight changes → selection pressure compounds
```

## Scope (this dialog · FROZEN)

Three platform-side increments. Nothing else. If something else is tempting, it goes to parking lot.

### Increment 1 — change_type='code' route (binding DONE)

- `soul_consumer.consume_pending_proposals` is renamed/rebuilt as `soul_executor.execute_accepted_proposals`.
- Reads from `platform_improvement_proposals WHERE status='accepted' AND change_type='code'` (the governance main table — NOT the orphan `platform_proposals`).
- For each row, extract `proposed_change.task` (NL improvement task text) and `proposed_change.target_module` (optional path hint). Pass to `soul_service.ship_to_draft_pr` (unchanged) with a `cycle_id = f"gov-{proposal.id}"`.
- On result: write back `resolution_note` (PR url or rejection reason) + flip `status` to `executed_ok` or `executed_failed`. Add migration: rename of status enum if needed.
- Scheduled by a systemd timer on cloud (mirroring `nautilus-soul.timer`), every 10 min.

**Binding DONE = an accepted `change_type='code'` row in `platform_improvement_proposals` (manually inserted is fine for the first proof) gets picked up by the executor on cloud within one timer interval, produces a real draft PR, and writes the PR URL back to that row. Verified by SQL + `gh pr view`.**

### Increment 2 — composite-delta-on-merge hook (binding DONE)

- A merge of a soul-produced PR (recognized by branch prefix `soul/` OR `proposal_id` link) triggers a hook:
  1. Look up baseline composite for the affected cycle/module from `v_engine_progress`.
  2. Wait N cycles (config; default 3) for new engine_cycle_outcomes to accumulate.
  3. Compute composite delta. Write to a new table `proposal_outcomes(proposal_id, composite_before, composite_after, delta, settled_at)`.
  4. Trigger NAU settlement: proposer gets `f(delta)`, yes-voters split a smaller pool, no-voters lose a small bond if delta > 0 (and gain if delta < 0). Reputation updates via the existing vote-result machinery.
- The hook is a scheduled job, not an HTTP callback (more robust). Daily sweep over recently merged PRs.

**Anti-reward-hacking (per agent-dialog 5/28 correction · explicit):**
- Submit a proposal: **0 NAU · 0 reputation movement.**
- Vote on a proposal: **0 NAU immediate** (reputation update only post-outcome).
- Merged PR + `composite_delta > 0`: NAU → proposer + yes-voters · reputation `+`.
- Merged PR + `composite_delta < 0`: NAU clawback if already settled · proposer + yes-voters reputation `-` · no-voters reputation `+` (they bet right).
- Merged PR + `composite_delta ≈ 0` (within noise floor): micro NAU to proposer (covers LLM cost) · zero reputation movement.
- All NAU flows are post-merge + post-N-cycle-settlement only. There is no NAU emission from submission or voting events themselves. This closes the platform's recurring "ship-but-not-effective" anti-pattern at the economic layer.

**Binding DONE = a merged soul PR produces a `proposal_outcomes` row with non-null `delta` after N cycles, and the NAU + reputation deltas (or clawback if delta < 0) are visible in the existing `nau_ledger` + `agents.reputation_score` for at least one test proposal of each outcome class (positive, negative, near-zero). Verified by SQL.**

### Increment 3 — deprecate the orphan `platform_proposals` table (binding DONE)

- Audit cloud: any existing rows in `platform_proposals` get migrated into `platform_improvement_proposals` (preserve proposal_id as a comment / resolution_note ref) OR explicitly archived.
- `soul_consumer.py` is removed (replaced by `soul_executor.py`).
- `platform_proposals` is dropped via migration (the table was never in migrations to begin with — anchor #5 schema cheat-sheet violation gets corrected).
- The L3 split-brain documented in `SOUL_PROPOSAL_CONTRACT_20260528.md` is officially closed: that doc gets a closing addendum pointing at this keystone.

**Binding DONE = on cloud, `SELECT COUNT(*) FROM platform_proposals` errors with "relation does not exist" (table dropped), and the closing addendum is committed.**

## Parking lot (NOT this iteration)

- L4 (soul improves V5/Kairos agent code) — still blocked, still needs agent-dialog consent.
- Reflection goal-sourcing (DATABASE_URL into soul .soul-env) — user-gated security decision, separate.
- Broader platform scope (`backend/services/*.py` minus soul_*) — needs ownership audit first.
- soul-as-economic-actor (soul itself owns a wallet/stake) — meaningful but later; Increment 2 already pays proposer/voters, soul-self-pay is a refinement.
- Clawback mechanics for composite degradation — Increment 2 pays on delta; explicit clawback adds rules complexity, defer.
- Agent-side wiring (V5 emits structured proposals) — owned by agent-dialog (anchor #7).

## Forcing functions (so this doesn't sprawl)

1. **Human-merge gate** stays for all `change_type='code'` PRs. Composite-delta NAU only pays out post-merge. No human merge, no payout.
2. **Binding-DONE per increment** above is the only exit criterion for that increment. No "almost works." No "should work."
3. **Increments are serial** (1 → 2 → 3). Increment 2 needs Increment 1 to produce real merged PRs first. Increment 3 needs 1+2 working so the orphan table can be safely dropped.

## Cross-dialog contract

- **platform-dialog (this)** owns Increments 1, 2, 3 above. Will NOT touch V5/Kairos/compass code (anchor #7).
- **agent-dialog** owns wiring V5 (and any other agent) to emit `POST /api/platform/proposals` with `proposed_change.type='code'`. See companion inbound for the exact request shape. They listen for writeback via existing proposal status/notes.
- **No work starts in platform-dialog until agent-dialog acknowledges the schema** (so we don't ship Increment 1 against a contract they can't or won't meet).

## Why this design is the answer to 1+1+1 > N

- Platform gives soul a fitness signal (composite delta) and an economic motive (NAU) — both of which soul cannot self-generate.
- Agent gives soul a real goal (reflection-driven proposal) and judgement (vote) — both of which the soul council cannot self-supply.
- Soul gives agent the hands to actually change code and gives the platform a self-improvement executor terminal — both of which they cannot self-provide.
- The composite-delta loop is the **second-order recursion**: bad code changes degrade composite → cost the proposer NAU + reputation → next cycle they propose better OR get out-voted. The loop compounds toward truly beneficial changes, not arbitrary edits.
- It closes the platform's recurring "ship-but-not-effective" anti-pattern: outcome is bound to merge AND measurement, not to motion.
