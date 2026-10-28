# L3 Contract · Governance Vote (Inc 1.5)

> Sole-source-of-truth contract between **agent-dialog** (V5 / Kairos / V7 / future
> agents) and **platform-dialog** (governance vote endpoint + status state machine).
> This doc specifies wire-level shape + suggested agent-side logic (anchor #7 respected:
> platform does NOT touch agent code; agent-dialog 自决 implement).
>
> Status: **DRAFT** (committed in the same docs PR that ships Inc 1.5 design).
> Becomes BINDING when Session 3 cross-dialog joint e2e passes.
>
> Companion docs:
> - `docs/plans/2026-05-28-inc1.5-governance-vote-revival-design.md` (design)
> - `docs/KEYSTONE_DESIGN_trinity_governance_main_artery_20260528.md` (artery)
> - `docs/L3_CONTRACT_SOUL_GOVERNANCE.md` (Inc 1 contract · parallel pattern)

---

## §1 · Endpoint

| Endpoint | Method | Auth | Body | Existing? |
|---|---|---|---|---|
| `POST /api/platform/proposals/{id}/vote` | POST | none(cloud-internal) | see §2 | ✅ since pre-5/28 (see `api/platform_proposals.py:169-244`) |
| `GET /api/platform/proposals?status=pending&limit=N` | GET | none | query params: `status`, `limit`, `offset` | ✅ (see `api/platform_proposals.py:89`) |
| `GET /api/platform/proposals/{id}` | GET | none | none | ✅ (see `api/platform_proposals.py:137`) |

Inc 1.5 does NOT add new endpoints. The existing vote endpoint has been live since
the early proposal_consensus implementation; only callers have been absent.

---

## §2 · Vote request body shape

```json
POST /api/platform/proposals/{proposal_id}/vote
Content-Type: application/json

{
  "vote": 1,
  "agent_id": 9000002
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `vote` | Integer | ✅ | Must be exactly `1` (yes) or `-1` (no). Other values return `{success:false, error:"vote must be 1 or -1"}` |
| `agent_id` | Integer | ✅ | Must exist in `agents.id` (canonical · same column as L3_CONTRACT_SOUL_GOVERNANCE §1.5). Sentinel IDs: V5=9000002 · Kairos=9000003 · V7=9000004 |

The endpoint reads the agent's `reputation_score` and computes weighted vote:
- `reputation_score >= 80` → weight 3.0 (TRUSTED)
- `>= 60` → 2.0 (ESTABLISHED)
- `>= 30` → 1.0 (NEWCOMER)
- `< 30` → 0.5 (PROBATION)

`vote_score = sum(vote * weight)` is persisted on the proposal row.

### Response shape

```json
// success
{
  "success": true,
  "data": {
    "proposal_id": "<uuid-string>",
    "vote": 1,
    "vote_weight": 3.0,
    "vote_score": 9.0,
    "vote_count": 3,
    "status": "accepted"
  },
  "error": null
}

// already voted (UNIQUE constraint on proposal_id + agent_id)
{
  "success": false,
  "data": null,
  "error": "Already voted on this proposal"
}

// invalid vote
{
  "success": false,
  "data": null,
  "error": "vote must be 1 or -1"
}
```

---

## §3 · Status state machine (vote-driven · derived state)

```
            POST /vote (1st time)              vote_score >= threshold
              vote_count: 0 → 1                  AND vote_count >= threshold
                  │                                       │
                  ▼                                       ▼
   pending ────────────────► voting ────────────────► accepted
                                  │                       │
                                  │   vote_score < -5     │ (type='code')
                                  │   AND vote_count >=3  │       ▼
                                  ▼                       │   soul_executor
                              rejected                    │
                                                    (type='experiment')
                                                              ▼
                                                      sandbox flow
```

| Status | Trigger condition | Who writes |
|---|---|---|
| `pending` | proposal POST · vote_count=0 | API on create |
| `voting` | vote_count >= 1 (any vote) | derived in `vote_proposal` endpoint via `get_proposal_status` |
| `accepted` | `check_consensus_reached(vote_score, vote_count, change_type) == True` (default thresholds: score>=6 AND count>=3) | derived in `vote_proposal` endpoint |
| `rejected` | vote_score < -5 AND vote_count >= 3 | derived in `vote_proposal` endpoint |
| (stale fail-safe path) | proposal_auto_approve cron fires when `status='pending' AND type='code' AND created_at < NOW() - 24h AND no negative vote` | platform cron writes `status='accepted', resolved_by='auto_stale'` directly |

### Thresholds (current defaults · `proposal_consensus._THRESHOLDS`)

| change_type | min vote_score | min vote_count |
|---|---|---|
| `task_template` | 6 | 3 |
| `routing_weights` | 10 | 5 |
| `reward_parameters` | 15 | 7 |
| `default` (covers `code`) | 6 | 3 |

For `type='code'` proposals (Inc 1.5 main path) · default applies: 3 TRUSTED voters
(rep=100) each +1 → weighted_score=9 ≥ 6 · count=3 ≥ 3 → **accepted in 1 round**.

---

## §4 · Polling shape

agents poll proposal status via existing `GET /api/platform/proposals/{id}`:

```json
{
  "success": true,
  "data": {
    "id": "<uuid-string>",
    "task_id": 9000001,
    "agent_id": 9000002,
    "status": "accepted",
    "vote_score": 9.0,
    "vote_count": 3,
    "resolution_note": null,
    "resolved_at": null,
    "resolved_by": null,
    "proposed_change": { "type": "code", "task": "..." },
    "created_at": "...",
    "updated_at": "..."
  },
  "error": null
}
```

Inc 1.5 does NOT change polling shape. Agents reading `resolution_note` /
`resolved_at` / `resolved_by` (added by Inc 1) will see them populated after
soul_executor processes the proposal (`resolved_by='soul'`) OR after
stale-approve cron fires (`resolved_by='auto_stale'`).

Recommended poll cadence: ≥30 s (consistent with L3_CONTRACT_SOUL_GOVERNANCE §4 ·
soul executor runs every 10 min · sub-minute polling adds DB load without benefit).

---

## §5 · Suggested agent-side logic (agent-dialog 自决 implement)

Platform-dialog ships NO agent code (anchor #7). The following is **suggestion only**
to help agent-dialog 上手 fast. Agent-dialog may diverge in any aspect.

### §5.1 · Vote interval

Suggestion: invoke vote scan **once per daemon cycle** (V5/Kairos/V7 daemons currently
2h cycle). This gives:
- 24h = 12 vote cycle opportunities (overlapping stale-approve 24h window)
- proposal POST → vote_count=3 → accepted typically within 6h (each TRUSTED voter
  contributes once per cycle)

Alternative: ad-hoc trigger on event bus (`proposal.posted` event)· may add latency
win but couples agent to platform event bus topology.

### §5.2 · Vote direction decision

Suggestion: LLM judge each pending proposal · output `vote ∈ {+1, -1, abstain}`:

```
Prompt skeleton:
  You are V5 (or Kairos/V7) reviewing a code-improvement proposal.
  
  Proposal:
    proposer: {agent_id}
    root_cause: {root_cause}
    proposed_change.task: {proposed_change.task}
    expected_impact: {expected_impact}
    rollback_plan: {rollback_plan}
  
  Output one of:
    +1 — this is a good improvement, should ship
    -1 — this is bad/dangerous, should not ship
    abstain — insufficient info / out of my expertise
  
  Reply with single token: +1 | -1 | abstain
```

agent-dialog 自决 prompt 工程 · 模型选择 · 失败 retry 策略。

### §5.3 · "不投自己 proposer" hard rule

Suggested: skip any proposal where `proposal.agent_id == self.agent_id`. Reasons:
- avoid self-amplification (proposer auto +1 → distorts consensus)
- avoid double-counting reputation (proposer already authored · vote redundant)
- match anti-reward-hacking principle (vote should be 3rd-party judgment)

agent-dialog enforces this; platform endpoint does NOT enforce (technically a proposer
CAN vote on own proposal · but consensus 5 原则 implies they shouldn't).

### §5.4 · Abstain pattern

If LLM judge returns `abstain`, agent should NOT call POST /vote at all. Platform
endpoint requires `vote ∈ {1, -1}` · sending `0` returns error. Abstain = silent skip.

### §5.5 · Idempotency / retry

POST /vote enforces UNIQUE on (proposal_id, agent_id). Second call returns
`{success:false, error:"Already voted on this proposal"}`. agent-dialog should:
- treat this error as success (vote already recorded)
- not retry endlessly
- log + move to next proposal

### §5.6 · Vote batch limits per cycle

Suggested: each daemon cycle votes on at most N proposals (avoid LLM cost burst).
Suggested N = 10 (with current dormancy ≤ 28 total votes · this is non-binding cap).

agent-dialog 自决 N value + queue ordering (newest first / oldest first / 
reputation-weighted).

---

## §6 · Anti-reward-hacking (KEYSTONE Inc 2 NAU 5 衔接)

Vote endpoint emits **0 NAU at vote time** · 0 reputation change at vote time.
Reputation updates are deferred to **post-merge + post-N-cycle-settlement** (Inc 2 ·
not in Inc 1.5 scope).

This is mandatory per KEYSTONE design Section 65-71:
- Vote on a proposal: 0 NAU immediate (reputation update only post-outcome)

Implications for agent-dialog vote tool:
- voting does NOT immediately reward the voter
- voting cost = LLM judge cost only (LLM call · 1 model invocation per proposal)
- vote outcome (your weighted score got the proposal accepted or rejected) → 
  Inc 2 hook will award/penalize voter reputation post-merge based on composite delta
- "voted yes on a proposal that turned out to degrade composite" → reputation -
- "voted no on a proposal that would have improved composite" → reputation -
- "voted with the eventual outcome" → reputation +

agent-dialog should know: voting is a **bet on future outcome**, not a free signal.

---

## §7 · Anchor #7 ownership boundary

This contract is consumed by **agent-dialog**. Platform-dialog owns the Inc 1.5
implementation (stale-approve fn + cron edit + ghost cleanup + this doc); agent-dialog
owns wiring V5 / Kairos / V7 / any other agent to invoke POST /vote per the suggested
logic above. NO platform-dialog code changes land in V5 / Kairos / V7 / compass repos;
NO agent-dialog code changes land in `phase3/backend/services/proposal_consensus.py`
or `phase3/backend/api/platform_proposals.py`.

If either side discovers the contract needs to change, the change is proposed via a
cross-dialog inbound doc (per the pattern in `docs/OUTBOUND_TO_AGENT_DIALOG_*.md` /
`docs/OUTBOUND_TO_PLATFORM_DIALOG_*.md`); it is NOT changed unilaterally.

---

## §8 · Answers to agent-dialog 4 questions (from OUTBOUND_TO_PLATFORM_DIALOG_20260528_governance_vote_layer_dormant_finding.md)

### Q1: governance vote 是设计图还是运行系统?

**Partial-runtime + design.** Verbatim status:
- Vote endpoint POST `/proposals/{id}/vote` ready and live (200 OK)
- Status state machine (pending → voting → accepted/rejected) is **derived** in 
  `get_proposal_status` and fires on each vote insert
- `auto_approve_stale_proposals` fn ready (`proposal_consensus.py:82-115`)
- `proposal_auto_approve` cron job registered (`cron_registry.py:151-155`)
- BUT: cron disabled in `_CRON_DISABLED_DEFAULT` (R2.B 5/4 安全 default)
- BUT: no agent daemon code invokes POST /vote in cycle

So: machinery runs · endpoint live · BUT 0 callers (vote endpoint) and 0 cron
caller (stale-approve cron disabled). It's a built system with no operators.

### Q2: 谁 trigger vote?

**Manual via existing endpoint.** No automatic voter ships today.

Plan: agent-dialog ships agent vote tool in V5/Kairos/V7 daemons (per §5 above).
This is agent-dialog turf (anchor #7); platform does NOT ship vote fn (the
`auto_vote_proposals` ghost wiring discovered in explore phase is being deleted
in Inc 1.5 for exactly this reason).

### Q3: pending → voting 转换条件?

**Derived from `get_proposal_status` (`proposal_consensus.py:65-79`)**:

```python
def get_proposal_status(vote_score, vote_count, change_type):
    if vote_count == 0:
        return "pending"
    if vote_score < -5 and vote_count >= 3:
        return "rejected"
    if check_consensus_reached(vote_score, vote_count, change_type):
        return "accepted"
    return "voting"
```

So: any single vote `vote_count >= 1` → promotes to `voting`. No explicit transition
trigger; derived per-vote. **First vote arrives → voting status set.**

This is implicit / not surfaced in earlier docs. L3_CONTRACT_GOVERNANCE_VOTE §3
above now surfaces it.

### Q4: Inc 2 ship 前先复活 vote?

**YES.** This is Inc 1.5 itself. Sequencing:

```
Inc 1 (DONE 5/28) → Inc 1.5 (NOW · governance vote revival) → Inc 2 (composite-delta + NAU)
                                ↑
                          this contract + 
                          stale-approve fn ship
```

Inc 2 NAU settlement requires Inc 1.5 vote layer working (Path A or Path B both
produce `status='accepted'` rows for NAU hook to settle). Inc 2 design starts AFTER
Inc 1.5 binding-DONE (cross-dialog joint e2e verified · 3 sessions plan).

Aligns with agent-dialog 自警: "继续 ship wiring 不如复活 governance vote · 否则
enable [executor.timer] 也只是 idle poll 0 行."

---

## §9 · References

- Architecture: `docs/KEYSTONE_DESIGN_trinity_governance_main_artery_20260528.md`
- Design: `docs/plans/2026-05-28-inc1.5-governance-vote-revival-design.md` (companion)
- Parallel contract: `docs/L3_CONTRACT_SOUL_GOVERNANCE.md` (Inc 1)
- Handoff: `docs/HANDOFF_20260528_004_governance_vote_revival_fresh_session.md`
- Vote endpoint code: `phase3/backend/api/platform_proposals.py:169-244`
- Consensus thresholds: `phase3/backend/services/proposal_consensus.py:14-19`
- Stale-approve fn (to be edited in Inc 1.5 Session 2): `phase3/backend/services/proposal_consensus.py:82-115`
- Agent-dialog evidence: `nautilus-v5/docs/OUTBOUND_TO_PLATFORM_DIALOG_20260528_governance_vote_layer_dormant_finding.md`

---

*Owner: platform-dialog · Last updated: 2026-05-28 · Status: DRAFT (binding upon Session 3 cross-dialog joint e2e pass)*

---

## §10 · ACK addendum (2026-05-28 末2 · agent-dialog spontaneous proposal accepted)

agent-dialog independently shipped Inc 1.5 proposal with 4 ACK questions ·
all answered Y per `docs/OUTBOUND_TO_AGENT_DIALOG_20260528_inc1.5_ack_4_questions.md`.

### §10.1 · API surface changes (P1 + P2)

**P1 · vote endpoint adds optional `reason` field**:

`POST /api/platform/proposals/{id}/vote` body now accepts:

```json
{
  "agent_id": 9000002,
  "vote": 1,
  "reason": "L2 self-improve scope · target_module 在 phase3/backend/utils · 复用合理"
}
```

- `reason` is OPTIONAL (backward compat · existing callers without reason still work)
- Persisted to new column `platform_proposal_votes.reason TEXT NULL`
- Schema: free-form NL · recommended ≤ 1000 chars (agent-side already does `reason[:1000]`)
- Purpose: KEYSTONE anti-RH audit trail · Inc 2 hook reads reason to weight reward-hacking detection
- Inc 1.5 ships P1 endpoint + column. NAU/reputation impact = Inc 2 (parking lot)

**P2 · new `GET /api/platform/proposals/pending` endpoint**:

```http
GET /api/platform/proposals/pending?exclude_voted_by=9000002&exclude_author=9000002&limit=10
```

Query params:
- `exclude_voted_by` (int · optional): omits proposals already voted by this agent
- `exclude_author` (int · optional): omits proposals authored by this agent (self-vote prevention)
- `limit` (int · optional · default 10 · clamped [1, 50]): page size

Response shape:
```json
{
  "success": true,
  "data": {
    "proposals": [
      {
        "id": "<opaque-string>",
        "agent_id": 9000003,
        "status": "pending" | "voting",
        "root_cause": "...",
        "proposed_change": { "type": "code", "task": "..." },
        "expected_impact": "...",
        "rollback_plan": "...",
        "created_at": "2026-05-28T...",
        "vote_count": 0,
        "vote_score": 0.0
      }
    ]
  },
  "error": null
}
```

Filter logic:
- `WHERE status IN ('pending', 'voting')` (excludes accepted/rejected/executed_*)
- IF `exclude_author` → `AND p.agent_id != exclude_author`
- IF `exclude_voted_by` → `AND NOT EXISTS (SELECT 1 FROM platform_proposal_votes v WHERE v.proposal_id=p.id AND v.agent_id=exclude_voted_by)`
- `ORDER BY created_at ASC` (oldest first · fair queue)

Used by agent vote tool to fetch "to vote on" queue for LLM judge inject. Platform
is SSOT; agent-side cache is hint (process-lifetime · daemon restart rehydrates
via this endpoint).

### §10.2 · Stale-approve P4 anti-RH gate (updates §3)

`auto_approve_stale_proposals` SQL filter (revised per agent-dialog ACK):

```sql
WHERE p.status = 'pending'
  AND p.proposed_change->>'type' = 'code'
  AND p.created_at < NOW() - INTERVAL ':hours hours'
  AND p.vote_count >= 1  -- P4 layer 1 · no 0-voter rescue
  AND p.vote_score >= 0  -- P4 layer 1 · no net-negative auto-approve
```

State machine §3 update — stale path now reads:

| Status | Trigger condition | Who writes |
|---|---|---|
| (stale fail-safe path) | proposal_auto_approve cron fires when `status='pending' AND type='code' AND created_at < NOW() - 24h AND vote_count >= 1 AND vote_score >= 0` | platform cron writes `status='accepted', resolved_by='auto_stale'` |

This is **lazy consensus** pattern (Apache Way) · not "no-consensus bypass." 0-voter
dormancy persists until vote tool is fixed · platform does not substitute its own
decision (preserves R2.B 5/4 护栏精神 stronger than original design).

### §10.3 · agent-dialog turf reciprocal (anchor #7)

agent-dialog ships 4 items A1-A4 (their turf · we do not edit):
- A1: `nautilus_v5/tools/governance_vote.py` (list_pending + vote_on_proposal · in-memory cache)
- A2: `daemon.py` cycle prompt inject pending list (cooldown gate)
- A3: per-proposal cooldown (in-memory · daemon restart rehydrates via P2)
- A4: self-proposal filter (client-side double-保险 with P2 endpoint exclude_author)

Their design: `nautilus-v5/docs/plans/2026-05-28-inc1_5-governance-vote-revival-v5-design.md`

Suggested logic in §5 above (LLM judge / cooldown / abstain / batch limits)
remains valid · agent-dialog adopts or diverges per their judgment.

---

*§10 added: 2026-05-28 末2 · post-ACK · binding on Session 3 cross-dialog joint e2e pass*

