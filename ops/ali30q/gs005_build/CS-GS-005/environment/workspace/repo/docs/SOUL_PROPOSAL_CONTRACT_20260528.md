# L3 · agent → soul proposal contract + reality audit (2026-05-28)

> Platform-dialog. Output of the L2/L3 fresh session. This documents the ACTUAL
> state of the "agent → soul" path (verified against code + cloud), corrects a
> schema mix-up in handoff #002, and proposes the minimal reconciliation. It
> deliberately does NOT build the missing pieces — that's a cross-dialog +
> agent-dialog decision (anchor #7). Verify-don't-assume throughout.

## TL;DR — L3 is not actually wired (3 concrete gaps)

The handoff said: "`platform_improvement_proposals` table + `services/soul_consumer.py::consume_pending_proposals` already work (LIVE E2E)". **That conflates two different tables and overstates "work".** Verified findings:

1. **Schema split-brain.** There are TWO proposal tables with different shapes and owners:
   - `platform_improvement_proposals` — the **governance/voting** system. Written by `POST /api/platform/proposals` (`api/platform_proposals.py`). Columns: `id, task_id, root_cause, agent_id, proposed_change(jsonb), expected_impact, rollback_plan, vote_score, vote_count, status, created_at`. Reputation-weighted voting → on `accepted`, triggers a sandbox experiment. **Nothing here goes to soul.**
   - `platform_proposals` — the **soul consumer queue**. Read/updated ONLY by `services/soul_consumer.py::consume_pending_proposals`. Columns (from the code): `proposal_id, proposed_change, change_type, status, created_at, resolution_note, resolved_at, resolved_by`. Not defined in any migration (created via raw SQL on cloud).
2. **No API writes to the soul queue.** Repo-wide, `platform_proposals` is referenced in exactly one place: `soul_consumer.py` (SELECT pending / UPDATE resolved). There is **no endpoint, tool, or service that INSERTs** into it. The prior "LIVE E2E" was a manual `INSERT` into `platform_proposals` by hand.
3. **The consumer is not scheduled.** `systemctl list-timers` on cloud shows `nautilus-soul.timer` (the L1 self-improve daemon) and `nautilus-ext-events-consumer.timer` — but **no soul-consumer timer**. So even a hand-inserted proposal only gets consumed if someone runs the consumer manually.

Net: an agent has no supported way to submit a coding proposal to soul, and even if it did, nothing consumes it on a schedule.

## What DOES work (verified)
- `soul_consumer.consume_pending_proposals(db, base_dir)` is correct in isolation: SELECT `status='pending'` → `soul_service.ship_to_draft_pr` (dry-run → `soul_pr_gate.gate` → apply on new branch → commit → DRAFT PR, never auto-merge) → UPDATE `resolution_note` + `status='reviewed'` + `resolved_by='soul'`. Writeback path is sound.
- `soul_service.ship_to_draft_pr(task, base_dir, branch, commit_msg, cycle_id=...)` returns `{success, stage?, detail?, pr_url?, branch, commit?, cycle_id}`. Never touches master.
- L1 self-improve daemon is genuinely live (separate path, `phase3/soul/`): timer active, real draft PRs #55/#56 on 2026-05-28.

## The contract (target state, once wired)

An agent (e.g. V5) submits a structured coding proposal; soul consumes it and writes back a verdict + draft PR URL. Two clean options for the submit side:

### Option A (lowest cost) — direct INSERT into `platform_proposals`
The consumer already reads this exact shape. Minimal agent-facing INSERT:
```sql
INSERT INTO platform_proposals (proposal_id, proposed_change, change_type, status, created_at)
VALUES (:proposal_id, :task_text, :change_type, 'pending', now());
```
- `proposal_id`: agent-chosen unique id (UUID or `v5-<n>`). Becomes the cycle branch `soul/<proposal_id>` and commit `soul: proposal <proposal_id>`.
- `proposed_change`: the task statement soul ships (natural-language "what to change", same shape the self-improve council feeds to ship).
- `change_type`: free label (e.g. `code`), currently informational.
- Writeback the agent polls: `SELECT status, resolution_note FROM platform_proposals WHERE proposal_id=:id` → `status` flips `pending`→`reviewed`; `resolution_note` = PR url on success or `dry-run rejected at stage '<stage>': <detail>`.

### Option B — a thin submit endpoint
`POST /api/soul/proposals` that does the Option-A INSERT with validation (dedup proposal_id, cap task length) and returns `{proposal_id}`. More ergonomic for agents than raw SQL; ~30 LOC. Keeps `platform_improvement_proposals` (governance) untouched.

> Note: `/api/soul/generate` exists but is **dry-run only** (no PR, no queue). It is not the durable path; the queue INSERT (A or B) is.

## Minimal reconciliation (recommended · for cross-dialog decision — NOT built here)

In priority order, lowest cost first:
1. **Schedule the consumer** (unblocks everything else): a systemd timer running `consume_pending_proposals` against the clean origin-synced `~/nautilus-soul-workspace` (same workspace the L1 daemon uses), e.g. every 10–15 min. Mirror `nautilus-soul.timer`/`.service`. ~1 unit pair, no code.
2. **Pick a submit path** (A or B). Recommend **B** (thin endpoint) so agents don't couple to raw SQL / the un-migrated table; but **A** is zero-code if a single agent integration is all that's needed near-term.
3. **Add `platform_proposals` to migrations** to end the split-brain (the table only exists via raw SQL on cloud — it will not exist in a fresh DB). Low urgency but real tech-debt.

### Explicitly out of scope here (anchor #7)
- **Agent side**: wiring V5's darwin loop to emit a proposal is agent-dialog's work (their `HANDOFF_20260528_001`). Platform provides the queue/contract; agent-dialog owns V5 cognition.
- This dialog does **not** unilaterally build the endpoint/timer — they're cheap, but choosing A-vs-B and scheduling cadence is a shared decision, and shipping an un-consented integration is the anti-pattern we avoid.

## Cloud verification commands used (reproducible)
- `systemctl list-timers --all | grep -iE "soul|consumer"` → only `nautilus-soul.timer` + `ext-events-consumer`, no soul-consumer.
- repo grep: `platform_proposals` → only `soul_consumer.py` (+ unrelated `api.platform_proposals` import alias in `main.py`). No INSERT, no CREATE TABLE, no migration.
- `python3 -c "import psycopg2"` in soul env → OK (2.9.11), so the reflection-DB path (L2 item) is import-ready; it only lacks a `DATABASE_URL` (a separate, user-gated decision — granting a self-modifying daemon DB access).

---

## Closing addendum (2026-05-28) — SUPERSEDED by KEYSTONE

This doc's split-brain finding (`platform_proposals` orphan queue vs `platform_improvement_proposals` governance table) is **resolved by design** in the keystone redesign. Quick map:

- **Was**: agent → orphan `platform_proposals` → soul_consumer → DRAFT PR (off-chain, no vote, no measurement, no settlement). The "reconciliation" options A/B in §"Minimal reconciliation" above are now historical.
- **Now (KEYSTONE)**: agent → `POST /api/platform/proposals` (writes `platform_improvement_proposals` with `proposed_change.type='code'`) → reputation-weighted vote → on `accepted`, soul_executor polls and ships DRAFT PR → composite-delta hook → NAU settlement → reputation update. The route is the governance main artery (KEYSTONE §"diagram"); soul is a vote-routed executor terminal alongside the existing sandbox terminal.

**Inc 1 (this PR) status**: ships the `change_type='code'` route — refactors `soul_consumer` → `soul_executor` reading from `platform_improvement_proposals`, adds resolution writeback columns, patches `on_consensus_reached` to skip sandbox for `type='code'`, schedules a 10-min systemd timer. Binding-DONE = one accepted code-type proposal → DRAFT PR + writeback within ≤10 min on cloud.

**Inc 3 deferred**: the orphan `platform_proposals` table itself is **not yet dropped**. Inc 3 waits until Inc 1 produces real merged PRs proving the executor is stable, and Inc 2 (composite-delta + NAU) has shipped at least one full settlement cycle. Until then, both `soul_consumer.py` (reads `platform_proposals`) and `soul_executor.py` (reads `platform_improvement_proposals`) coexist; only the executor receives newly accepted proposals because there is no producer for the orphan queue.

**Pointers**:
- `docs/KEYSTONE_DESIGN_trinity_governance_main_artery_20260528.md` — architectural lock-in
- `docs/HANDOFF_20260528_003_increment1_governance_route.md` — Inc 1 fresh-session brief
- `docs/plans/2026-05-28-inc1-governance-route.md` — Inc 1 plan (this PR)
- `docs/L3_CONTRACT_SOUL_GOVERNANCE.md` — Inc 1's sole-source-of-truth contract for agent-dialog
