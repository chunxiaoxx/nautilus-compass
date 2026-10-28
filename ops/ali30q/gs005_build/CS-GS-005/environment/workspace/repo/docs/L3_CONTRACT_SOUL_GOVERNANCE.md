# L3 Contract · Soul Governance Route (Increment 1)

> Sole-source-of-truth contract between **agent-dialog** (V5 / Kairos / future
> agents) and **platform-dialog** (governance + soul executor). This doc
> specifies the wire-level shape only. Agent-side wiring (the V5 wrapper,
> `_soul_proposal_poll_loop`, LLM scaffolding) is agent-dialog's job per
> anchor #7; platform-dialog will not touch agent code.
>
> Status: **DRAFT** (committed in the same PR that ships Inc 1 Sub-tasks 1-3).
> Becomes BINDING when Sub-task 4 (cloud e2e) passes.
>
> Companion docs:
> - `docs/KEYSTONE_DESIGN_trinity_governance_main_artery_20260528.md` (architecture)
> - `docs/HANDOFF_20260528_003_increment1_governance_route.md` (handoff)
> - `docs/plans/2026-05-28-inc1-governance-route.md` (implementation plan)

---

## 1. Stable `task_id` constant

All soul-routed code-improvement proposals reference a single, well-known
sentinel row in `academic_tasks`. The API at `POST /api/platform/proposals`
validates `task_id` exists and has `task_type='platform_meta'`
(`api/platform_proposals.py:50-55`); using the singleton lets agents emit
proposals without inventing per-call task rows.

| Field | Value | Type |
|---|---|---|
| `task_id` (canonical) | **`9000001`** | Integer |
| `academic_tasks.task_id` (string column) | `'platform-meta-soul-singleton'` | String(50) |
| `task_type` | `'platform_meta'` | String(30) |
| `title` | `'Soul code-improvement singleton'` | String(200) |

**Agents MUST emit the Integer `9000001`** as the `task_id` field of the
proposal body. The API resolves the FK on `academic_tasks.id` (Integer);
the String `task_id` column is internal to `academic_tasks` and is NOT the
value that goes into proposal bodies.

### Schema drift safety

`academic_tasks.id` is declared Integer autoincrement in the SQLAlchemy
model and the FK from `platform_improvement_proposals.task_id` is Integer.
If cloud schema has drifted (anchor #5 split-brain risk), the seed
migration `a7b4c1d9e2f3_seed_soul_meta_task.py` will surface a clear
type / FK error on upgrade rather than silently corrupt data. In that
case agent-dialog will be notified before V5 is wired.

A uuid5 fallback (`uuid5(NAMESPACE_DNS, 'soul-code-improvement-singleton')`)
was considered in the plan but **not adopted**: the cloud type is Integer
and the seed inserts an Integer. The canonical value above is the only
value to consume.

If cloud upgrade ever surfaces an Integer-vs-UUID type error (anchor #5 drift scenario), agent-dialog will be notified via an inbound and a uuid5 fallback variant (`uuid5(namespace=DNS, name='soul-code-improvement-singleton')`) will ship as a follow-up migration. The canonical contract value above stays Integer until then.

---

## 1.5. Stable `agent_id` seed (V5 · added 2026-05-28 follow-up)

Sub-task 1 of Inc 1 only seeded `academic_tasks.id=9000001`. The L3 contract
also requires the proposing agent's id to exist in `agents.id` (§2 + API
validation at `api/platform_proposals.py:58-60`). V5 (`nautilus-prime-001`)
has zero rows in `agents` though it exists in `platform_agents` (anchor #5
schema split-brain · two parallel agent tables). The Inc 1 follow-up
migration `c9e8f3a1d2b5_seed_v5_agent_row` plugs this gap.

| Field | Value | Type |
|---|---|---|
| `agents.id` (canonical · use this in proposal body) | **`9000002`** | Integer |
| `agents.agent_id` (internal · NOT used by API validation) | `9000002` | Integer |
| `agents.owner` (V5 wallet · audited cloud reality) | `0x1d5B7714f12b9ef979a6c5D1F1a8cf860fbc89F6` | String(42) |
| `agents.name` | `'Nautilus Prime'` | String(100) |
| `agents.reputation` (seed) | `100` | Integer (TRUSTED tier per `proposal_consensus.get_vote_weight`) |

**Agents MUST emit the Integer `9000002`** as the `agent_id` field of the
proposal body — `agents.id` (PK), NOT `agents.agent_id` (the legacy
agent-internal column). The API validation at line 58 joins on `agents.id`
specifically (see §2 note below).

Migration applied to cloud `nautilus_production` via idempotent raw SQL
(same chain-mess sidestep as the academic_tasks seed). Migration file is
linear successor of `b8c5d2e0a3f4_add_proposal_resolution_columns`.

**Audit note (2026-05-28 batch followup)**: the initial seed migration used
`0x9C17F3f1e34739c776c041364Cf9F94Ac71612F9` based on the agent-dialog outbound
report. Cloud audit of `platform_agents` showed the actual Nautilus Prime
wallet is `0x1d5B...`; followup migration `d4a2e1b6f8c9` corrects the owner
in-place (idempotent UPDATE conditioned on the legacy value).

---

## 1.6. Stable `agent_id` seed (Kairos · added 2026-05-28 batch followup)

Kairos shares the `nautilus-v5` repo with V5 (lives at `nautilus-v5/kairos/`).
Cloud `platform_agents` row name='Kairos' has empty `wallet_address` (Kairos
has no EOA wallet). The seed uses a sentinel owner extending the ETH dead-address
convention.

| Field | Value | Type |
|---|---|---|
| `agents.id` (canonical) | **`9000003`** | Integer |
| `agents.agent_id` | `9000003` | Integer |
| `agents.owner` (sentinel) | `0x0000000000000000000000000000000000000003` | String(42) |
| `agents.name` | `'Kairos'` | String(100) |
| `agents.reputation` (seed) | `100` | Integer |

V5 dialog (who maintains Kairos code) decides whether to wire Kairos with a
`submit_soul_proposal` tool similar to V5's pattern. Until then, this row sits
ready for use without affecting other paths.

---

## 1.7. Stable `agent_id` seed (V7 · added 2026-05-28 batch followup)

V7 daemon lives at `/usr/local/bin/v7-telegram-daemon.py` (system path).
Cloud `platform_agents` has 2 entries (`V7` and `v7-souls-fusion`) both with
empty `wallet_address`. Same sentinel pattern.

| Field | Value | Type |
|---|---|---|
| `agents.id` (canonical) | **`9000004`** | Integer |
| `agents.agent_id` | `9000004` | Integer |
| `agents.owner` (sentinel) | `0x0000000000000000000000000000000000000004` | String(42) |
| `agents.name` | `'V7'` | String(100) |
| `agents.reputation` (seed) | `100` | Integer |

Same wiring authority note as §1.6. V7 ownership is split between V5 dialog
(if they maintain telegram daemon code) and possibly platform; this doc only
publishes the identity contract.

---

## 2. `POST /api/platform/proposals` body shape

Endpoint: `POST /api/platform/proposals` (existing · no Inc 1 changes).

Required fields (validated at `api/platform_proposals.py:44-47`):

| Field | Type | Example | Notes |
|---|---|---|---|
| `task_id` | Integer | `9000001` | The singleton sentinel. Validated as `task_type='platform_meta'`. |
| `agent_id` | Integer | `9000002` (canonical V5 · see §1.5) | Must exist in `agents.id` (note: NOT `agents.agent_id` — the API joins on `agents.id`; agent-dialog must pass the internal numeric id, not the wallet-derived agent_id). |
| `root_cause` | string | `"V5 reflection cycle 42 found duplicated string trim logic in 3 utility modules"` | Free-form natural language; persisted as `text`. |
| `proposed_change` | JSON object | see §3 below | Stored as `jsonb`. Schema is type-tagged for routing. |
| `expected_impact` | string | `"Reduce 60 LOC duplication; one canonical helper for downstream consumers"` | Free-form. |
| `rollback_plan` | string | `"Revert the draft PR; existing duplicated implementations remain in place"` | Free-form. |

**Success response** (`200 OK`):

```json
{
  "success": true,
  "data": { "id": "<uuid-string>" },
  "error": null
}
```

The returned `id` is the proposal id (cloud reality: API inserts
`str(uuid.uuid4())` into a column declared Integer; SQLAlchemy params
accept the opaque value. Treat the id as opaque — pass back verbatim
when polling. Both platform-dialog Sub-task 2 executor and V5 poll loop
treat this as a string parameter, never coerce to int.).

> **FIXME** (platform-dialog backlog): `platform_improvement_proposals.id` is declared `sa.Integer` but the API at `phase3/backend/api/platform_proposals.py:62` inserts `str(uuid.uuid4())`. The column appears to accept the string value on cloud (silently coerced or schema-drifted to text). V5 must treat `id` as opaque; platform-dialog will reconcile in a separate cleanup PR.

**Error response** (`200 OK` with `success=false`):

```json
{ "success": false, "data": null, "error": "<reason>" }
```

Common errors: `Missing required field: <name>`, `task_id not found or
task_type is not 'platform_meta'`, `agent_id not found`.

---

## 3. `proposed_change` JSON schema for `type='code'`

The `proposed_change` JSON object carries a `type` discriminator that the
post-vote router uses to decide between sandbox experiment (`type='experiment'`)
and soul executor (`type='code'`). Inc 1 introduces the `'code'` branch.

### Required keys

| Key | Type | Description |
|---|---|---|
| `type` | string | Discriminator. **Must be exact string `"code"`.** Other values route to existing sandbox flow (unchanged by Inc 1). |
| `task` | string | Natural-language description of the improvement. Passed verbatim into `soul_service.ship_to_draft_pr(task=…)`. Should be self-contained: an LLM with repo access must be able to act on it without further context. |

### Optional keys

| Key | Type | Description |
|---|---|---|
| `target_module` | string | Repo-relative path hint (e.g., `phase3/backend/utils/text.py`). Plumbed into executor metadata; currently informational only. Reserved for future use. |

### Example payload

```json
{
  "task_id": 9000001,
  "agent_id": 59,
  "root_cause": "Repeated `s.strip().replace(...)` blocks across 3 modules suggest a missing utility helper.",
  "proposed_change": {
    "type": "code",
    "task": "Extract the repeated `s.strip().replace('\\u00a0', ' ').replace('\\t', ' ')` pattern from phase3/backend/utils/text.py, phase3/backend/services/audit.py, and phase3/backend/services/reputation.py into a single helper `normalize_whitespace(s: str) -> str` in phase3/backend/utils/text.py. Update all 3 call sites to import and use it.",
    "target_module": "phase3/backend/utils/text.py"
  },
  "expected_impact": "Remove ~12 LOC duplication; single source of truth for whitespace normalization.",
  "rollback_plan": "Close the draft PR without merging; existing inline blocks remain valid."
}
```

### Schema enforcement note

The platform API does NOT validate `proposed_change` shape beyond
requiring the field to be present. Soul executor (Sub-task 2) enforces
`type='code' AND task IS NOT NULL` at the SQL `WHERE` clause and at row
processing time; rows with `type='code'` but missing `task` will be
marked `executed_failed` with a clear note (does NOT crash the executor;
does NOT block the batch).

---

## 4. Polling shape

Endpoint: `GET /api/platform/proposals/{id}` (existing).

After Inc 1 Sub-task 2 ships the `_proposal_resolution_columns` migration,
the response will include three NEW fields (`resolution_note`,
`resolved_at`, `resolved_by`) in addition to the existing `status`,
`vote_score`, `vote_count`. **These three new fields depend on Sub-task 2
landing** — V5 should defensively treat them as optional until Sub-task 2
is merged.

Response shape (after Sub-task 2):

```json
{
  "success": true,
  "data": {
    "id": "<proposal id>",
    "task_id": 9000001,
    "agent_id": 59,
    "status": "executed_ok",
    "vote_score": 99,
    "vote_count": 99,
    "resolution_note": "https://github.com/chunxiaox/nautilus-core/pull/1234",
    "resolved_at": "2026-05-28T12:34:56Z",
    "resolved_by": "soul",
    "proposed_change": { "type": "code", "task": "..." },
    "created_at": "2026-05-28T12:00:00Z",
    "updated_at": "2026-05-28T12:34:56Z"
  },
  "error": null
}
```

Poll cadence guidance: agent-dialog `_soul_proposal_poll_loop` should
poll at ≥30 s intervals (soul executor cadence is 10 min; sub-minute
polling adds DB load without latency benefit).

---

## 5. Status state machine

```
pending ──────► voting ──────► accepted ───┬─► (type='code')   executed_ok
                                           │                    executed_failed
                                           └─► (type='experiment') [unchanged sandbox flow]
                              voting ──────► rejected
```

| Status | Meaning | Who writes | Terminal? |
|---|---|---|---|
| `pending` | Just inserted via `POST /api/platform/proposals`. Awaiting governance vote opening. | API on create | no |
| `voting` | Vote period open. | Governance service | no |
| `accepted` | Vote passed (reputation-weighted). Sub-task 2 executor reads from here. | Governance vote tally | no (for `type='code'`) |
| `rejected` | Vote failed. | Governance vote tally | yes |
| `executed_ok` | Soul executor shipped a draft PR. `resolution_note` contains the PR URL. | Soul executor (Inc 1) | yes |
| `executed_failed` | Soul executor encountered a stage failure (lint/check/git/PR-open/etc.). `resolution_note` contains `"<stage>: <detail>"`. | Soul executor (Inc 1) | yes (no retry in Inc 1) |

Notes:
- For `proposed_change.type='experiment'` rows, the existing sandbox flow
  is unchanged by Inc 1; their state machine is owned by `proposal_consensus.py`
  and is out of scope for this contract.
- Inc 2 will add a post-merge `composite_delta` hook with NAU settlement;
  that adds a separate `proposal_outcomes` row keyed off the proposal id
  but does NOT add new status values to `platform_improvement_proposals`.

---

## 6. Anchor #7 note (ownership boundary)

This contract is consumed by **agent-dialog**. Platform-dialog owns the
Inc 1 implementation (alembic migrations, soul executor, systemd timer,
this doc); agent-dialog owns wiring V5 / Kairos / any other agent to
emit `POST /api/platform/proposals` with `proposed_change.type='code'`
and to consume the polling shape above. No platform-dialog code changes
land in V5 / Kairos / compass repos; no agent-dialog code changes land
in `phase3/backend/services/soul_*` or `phase3/backend/alembic/*`.

If either side discovers the contract needs to change, the change is
proposed via a cross-dialog inbound doc (per the pattern in
`docs/OUTBOUND_TO_AGENT_DIALOG_*.md` /
`docs/OUTBOUND_TO_PLATFORM_DIALOG_*.md`); it is NOT changed unilaterally.

---

## 7. References

- Architecture: `docs/KEYSTONE_DESIGN_trinity_governance_main_artery_20260528.md`
- Handoff: `docs/HANDOFF_20260528_003_increment1_governance_route.md`
- Implementation plan: `docs/plans/2026-05-28-inc1-governance-route.md`
- Cross-dialog acks:
  - `docs/OUTBOUND_TO_AGENT_DIALOG_20260528_inc1_unblock_item2_seed.md` (out)
  - `docs/OUTBOUND_TO_PLATFORM_DIALOG_20260528_ack_increment1.md` (in from V5)
- Seed migration: `phase3/backend/alembic/versions/a7b4c1d9e2f3_seed_soul_meta_task.py`
- Existing API: `phase3/backend/api/platform_proposals.py`
- Existing migration that creates the table: `phase3/backend/alembic/versions/add_improvement_proposals.py`

---

*Owner: platform-dialog · Last updated: 2026-05-28 · Status: DRAFT (binding upon Inc 1 Sub-task 4 cloud e2e pass)*
