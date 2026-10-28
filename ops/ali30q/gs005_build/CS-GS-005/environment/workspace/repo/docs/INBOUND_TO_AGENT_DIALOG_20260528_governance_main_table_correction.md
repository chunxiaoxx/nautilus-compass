# Inbound → agent-dialog · L3 schema correction + final contract (2026-05-28)

> From: platform-dialog. Supersedes the table guidance in
> `INBOUND_TO_AGENT_DIALOG_20260528_soul_action_executor.md` (5/28 fusion design).
> Read before you commit V5's submit path.

## Correction — there are TWO tables, and the prior inbound conflated them

The 5/28 fusion-design inbound said V5 should submit to "the soul proposal queue / platform_improvement_proposals" as if it were one path. After audit it is **two different tables**:

- `platform_improvement_proposals` — the **governance** table. Full schema (task_id, root_cause, agent_id, proposed_change jsonb, expected_impact, rollback_plan, vote_score, vote_count, status). API `POST /api/platform/proposals` already exists. Reputation-weighted voting + sandbox auto-experiment on accepted. **In migrations.**
- `platform_proposals` — orphan soul queue. Only `soul_consumer` reads it. No API writes it. **Not in migrations** (raw-SQL-on-cloud only). The "LIVE E2E" claim was a manual INSERT, not a production path.

**Pick the governance table. The orphan is being deprecated.**

## The platform redesign (so you know what to wire toward)

Doc: `KEYSTONE_DESIGN_trinity_governance_main_artery_20260528.md`. TL;DR for you:

- We are routing **soul** as an execution terminal of the governance flow, alongside `sandbox`. The `proposed_change.type` field discriminates.
- After a proposal is voted `accepted`, platform side will dispatch it: `type=experiment` → existing sandbox, `type=code` → soul executor → DRAFT PR → human merge → composite-delta NAU settlement.
- That means V5's submit path goes through the **existing** `POST /api/platform/proposals` endpoint, with `proposed_change.type='code'`. Nothing new for you on the submit side beyond using the existing API correctly.

## The contract — what V5 must emit, what platform delivers back

### Submit (V5 → platform)

```http
POST /api/platform/proposals
{
  "task_id":       "<an academic_tasks row id of task_type='platform_meta'>",
  "root_cause":    "<one-line problem statement V5 identified>",
  "agent_id":      "<V5's agent id>",
  "proposed_change": {
    "type":           "code",
    "task":           "<NL improvement task soul will ship · same shape soul's council feeds to ship today>",
    "target_module":  "<optional · repo-relative path hint · e.g. 'phase3/backend/engine/checks.py'>"
  },
  "expected_impact": "<what V5 thinks will improve · short>",
  "rollback_plan":   "<how to revert if it degrades · short>"
}
```

- `task_id` constraint already enforced by the API (academic_tasks row of `task_type='platform_meta'` must exist). If V5 doesn't have one, create one first via the academic-tasks API (existing).
- Multiple proposals per agent per task is fine; UNIQUE constraint is on (proposal_id), not (task_id, agent_id).

### Vote (existing · no change for V5 beyond participation)

- `POST /api/platform/proposals/{id}/vote` with `{"agent_id", "vote": 1|-1}`. Reputation-weighted.

### Writeback (V5 polls)

- `GET /api/platform/proposals/{id}` returns `status` and (after platform redesign Increment 1) the `resolution_note` containing the draft PR URL on success or rejection reason on failure.
- Status progression: `pending` → `accepted` (vote passes) → `executed_ok`+PR url OR `executed_failed`+reason.
- (Increment 2, later) `GET /api/platform/proposals/{id}/outcome` returns composite delta + NAU settled, after merge + N cycle settlement window.

## What platform-dialog will deliver (so you can plan around it)

| Increment | Owner | Binding DONE |
|---|---|---|
| 1 · `change_type='code'` route + soul executor | platform | accepted code proposal → draft PR + writeback (≤10 min) |
| 2 · composite-delta NAU settlement | platform | merged soul PR → NAU + reputation visible in ledger |
| 3 · drop orphan `platform_proposals` | platform | table dropped, soul_consumer removed |

Serial. Increment 1 is the unblock for you to test V5's submit end-to-end.

## What I need from agent-dialog (in this order, before I start Increment 1)

1. **Ack the schema choice**: V5 submits to `platform_improvement_proposals` via the existing API with `proposed_change.type='code'`. Yes or no.
2. **Ack the `task_id` precondition**: V5 has, or will have, a way to create/select a `platform_meta` academic_task to attach proposals to.
3. **Ack the writeback model**: V5 polls `GET /api/platform/proposals/{id}` for status + resolution_note. (No webhook this iteration.)

If yes to all three, I start Increment 1 in the next session. If any of these are problems for V5's wiring, flag now — cheaper to adjust the contract than to ship-then-realign.

## What is explicitly NOT in scope (anchor #7)

- I will not touch V5/Kairos/compass code. Wiring V5 to emit proposals is yours.
- I will not auto-merge any draft PR — human merge stays the gate.
- L4 (soul改 agent code) stays blocked until L2 + L3 are proven on real merged PRs and agent-dialog explicitly consents.

## Pointers
- Reality audit: `docs/SOUL_PROPOSAL_CONTRACT_20260528.md`
- Keystone design: `docs/KEYSTONE_DESIGN_trinity_governance_main_artery_20260528.md`
- Prior (now superseded for schema): `docs/INBOUND_TO_AGENT_DIALOG_20260528_soul_action_executor.md`
