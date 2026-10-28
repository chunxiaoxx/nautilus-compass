# Handoff → fresh session · Governance vote revival (Inc 1.5 / pre-Inc-2) · 2026-05-28 #004

> Platform-dialog. The session that shipped Inc 1 + 3 follow-ups + verified
> agent-dialog's critical finding (governance vote layer dormant 1 month+) is
> ending. This is the actionable starting point for the next fresh session.
> ✅ = verified. ⏳ = next. 🔴 = critical.

## State snapshot (verified 2026-05-28 end-of-session)

- **master `aeca6e425`** (origin synced). Local clean.
- **Inc 1 MERGED** (master `d323b7779`) + 3 follow-up commits:
  - `cd9f4dbcb` V5 agents seed (id=9000002 · wallet later corrected to 0x1d5B)
  - `41e58539c` outbound V5 seeded
  - `806947780` outbound Inc 1 merged status sync
  - Latest `aeca6e425` batch (Kairos id=9000003 + V7 id=9000004 + V5 wallet fix)
- **Cloud `nautilus_production`** has 3 agent seeds + 1 task seed applied:
  - `academic_tasks.id=9000001` (Soul code-improvement singleton)
  - `agents.id=9000002` Nautilus Prime owner=`0x1d5B7714f12b9ef979a6c5D1F1a8cf860fbc89F6`
  - `agents.id=9000003` Kairos sentinel owner=`0x0...0003`
  - `agents.id=9000004` V7 sentinel owner=`0x0...0004`
- **agent-dialog (V5 dialog) ship**: V5+Kairos+V7 wiring all done (TDD 31/31 cloud pass). Daemons restarted 5/28 14:51-14:59 applying env config. V7_AGENTS_ID=9000004 verified in cloud systemd.
- **`nautilus-soul-executor.timer`** STILL `disabled` (user-gate on persistent DATABASE_URL).

## 🔴 The critical finding (verified end-of-session 2026-05-28)

Agent-dialog manually triggered a real V5 proposal `33b1c29a-60eb-43ff-b8bf-6bb54dccbe78` at 15:39. After 5min: still `pending`, vote_count=0. Investigation revealed:

| Block | State | Evidence |
|---|---|---|
| `platform_proposal_votes` | 28 rows · last vote `2026-04-19` (39 days ago) | SQL count + earliest/latest |
| Governance vote cron/timer/service | **ZERO** | `systemctl list-timers --all \| grep vote` empty |
| `auto_approve_stale_proposals` fn cron caller | **ZERO** | `grep -r auto_approve_stale /etc/systemd /etc/cron*` empty |
| Agent self-vote cycle logic | none in code | V5/Kairos/V7 don't vote in their cycles |

**Mainline 5 blocks:**

| # | Block | Status |
|---|---|---|
| 1 | POST submit | ✅ Inc 1 ship · cloud verified |
| 2 | pending → voting (any vote) | ❓ trigger condition = any vote · but no voter |
| 3 | voting → accepted | 🔴 **dormant 39+ days · zero votes · zero cron-approve** |
| 4 | accepted → executed_ok | ⏸️ executor.timer disabled (user-gate) |
| 5 | merged PR → composite-delta NAU | ⏸️ Inc 2 not shipped |

**Inc 1 binding-DONE was synthetic** (manual INSERT with status='accepted' bypassed vote layer). True end-to-end mainline cannot flow without block 3 working.

## ⏳ The next session's only job: governance vote revival design + ship

### Mandatory discipline (per workflow-lock + handoff #003 pattern)

writing-plans → worktree → subagent-driven (implementer + spec review + code-quality review + fix) → verification-before-completion → finishing-a-development-branch (draft PR · human merge gate).

### Candidate solutions (5 · fresh session decides)

| # | Solution | Ownership | Cost | Reward-hacking risk |
|---|---|---|---|---|
| (a) cron `auto_approve_stale_proposals` 24h auto-approve | platform | very low (1 systemd timer + 1 small entrypoint script) | high (any garbage proposal accepts in 24h · LLM cost waste) |
| (b) Lower consensus thresholds (e.g. score>=1 count>=1) | platform | very low (edit `_THRESHOLDS`) | medium (still need someone to vote · doesn't fix dormancy) |
| (c) Agent vote tool · each agent cycle votes on pending proposals | agent-dialog (anchor #7) | medium (each daemon needs vote logic + cycle hook) | low (proper consensus across 4 voters) |
| (d) Trusted oracle agent (e.g. V7 aggregator) auto-votes all proposals on cron | agent-dialog | low (1 daemon + cron) | medium (single point of trust) |
| (e) Combination: platform cron stale-approve as safety net + agent-dialog vote tool for proper consensus | cross-turf | medium | low |

**Platform-dialog preference: (e) combination**. Platform ships cron safety net (own turf · anchor #7 respected). Agent-dialog ships proper vote tool (their turf).

### Anti-reward-hacking (must bake in · per KEYSTONE Inc 2 NAU 5 条)

- submit proposal = 0 NAU · 0 reputation movement
- vote = 0 NAU immediate (reputation post-outcome only)
- All NAU flow = post-merge + post-N-cycle-settlement only
- Stale-approve path must also gate on human-merge + composite-delta · doesn't shortcut the settlement layer

### Open design questions (fresh session decides)

1. **(a) timeline**: 24h stale window the right value? Shorter (4h)? Longer (3 days)? Tradeoff cost-of-spam vs unblock-latency.
2. **(c) cycle hook**: each agent should vote on ALL pending proposals (high LLM cost) or only those matching their specialty? How to decide vote direction (read root_cause + proposed_change → LLM judges 1/-1)?
3. **Should `33b1c29a` style retries**: after revival, would agent-dialog re-trigger a manual proposal as binding-DONE proof?
4. **Inc 2 sequencing**: governance vote revival is Inc 1.5? Or fold into Inc 2 design (composite-delta + NAU + vote revival as one PR)?

## What this fresh session is NOT (parking lot)

- Inc 2 composite-delta + NAU settlement code (only AFTER vote revival proves out)
- Inc 3 platform_proposals orphan table drop
- L4 (soul modifies agent code)
- Persistent DATABASE_URL + timer enable (depends on whether vote revival picks (a) or relies on (c))
- Reward-hacking detection mechanics beyond the 5 NAU principles

## Cross-dialog state (carry over)

- **agent-dialog session 20260528 末** R3 收口. 已 written 3 outbounds: `inc1_green_light` · `kairos_v7_wiring_shipped_request_seeds` · `governance_vote_layer_dormant_finding`.
- **platform-dialog 已发 6 outbounds**: `inc1_unblock_item2_seed` · `inc1_l3_contract_ready` · `inc1_merged` · `inc1_v5_agents_seeded` · `inc1_kairos_v7_seeded_v5_wallet_fix` · `governance_vote_dormancy_ack` (this last one acknowledges + agrees fresh-session main agenda).
- **Cross-dialog handshake on governance vote revival**: confirmed in `governance_vote_dormancy_ack` outbound. Both dialogs aligned.

## Cloud workflow gotchas (carry over from prior handoffs)

- Build locally + push; cloud pulls via `git reset --hard origin/master`. Soul service runs as `User=ubuntu` from `~/nautilus-soul-workspace/phase3`.
- Cloud has NO `alembic_version` table (Base.metadata.create_all bootstrap). Migrations applied via raw SQL · same idempotent pattern.
- Cloud DB has its OWN multi-head alembic mess (pre-existing · documented). Don't chase chain cleanup in this fresh session.
- `.soul-env` lacks DATABASE_URL (user-gate). Adding it un-gates BOTH soul executor + L1 daemon reflection-DB.

## Discipline (mandatory · do NOT skip)

- writing-plans → worktree → subagent-driven (implementer + 2-stage review + fix) → verification-before-completion → finishing-a-development-branch
- Same flow that produced L2 (#57) + Inc 1 (#59). Two-stage review caught real bugs both times.
- **R3 watch**: governance vote revival is substantive. Plan for two sessions if needed (Inc 1.5 design doc in one · cron + thresholds + agent vote tool ship in next).
- **R4**: any code change → `git status` first. Use worktree (`_siblings/inc1.5-governance-revival` or similar).
- **anchor #7**: agent vote tool is agent-dialog turf. Platform ships cron + threshold changes only.

## User to-dos carried over (not handoff-blocking)

- 🔴 revoke exposed GitHub PAT + rotate DeepSeek key (pending since 5/27 `action_token_revoke`)
- Decision on PR #53 (close as won't-fix · or override merge)
- Persistent DATABASE_URL decision (couples to (a)/(c)/(e) governance revival choice)

## Key pointers

- KEYSTONE design: `docs/KEYSTONE_DESIGN_trinity_governance_main_artery_20260528.md`
- L3 contract (V5/Kairos/V7): `docs/L3_CONTRACT_SOUL_GOVERNANCE.md` (sections 1, 1.5, 1.6, 1.7, 2-7)
- Inc 1 plan: `docs/plans/2026-05-28-inc1-governance-route.md`
- Prior handoff: `docs/HANDOFF_20260528_003_increment1_governance_route.md`
- Most recent platform outbound: `docs/OUTBOUND_TO_AGENT_DIALOG_20260528_governance_vote_dormancy_ack.md`
- Most recent agent-dialog outbound: `nautilus-v5/docs/OUTBOUND_TO_PLATFORM_DIALOG_20260528_governance_vote_layer_dormant_finding.md`
- Memory: `[[session_20260528_inc1_governance_route_draft_pr]]` (covers full session)

## Fresh session opening line (suggested)

> Active anchor: #2 product loop / #3 反 D 维护 / #7 anchor turf.
> Inc 1 merged 5/28 + 3 follow-ups (V5/Kairos/V7 seeded). agent-dialog ship V5/Kairos/V7 wiring TDD 31/31. CRITICAL FINDING (verified 5/28): governance vote layer dormant 39+ days (zero votes since 4/19 · no auto-vote · no cron-approve). Fresh session main agenda = governance vote revival design. Candidate (e) = platform cron stale-approve + agent-dialog vote tool. writing-plans → worktree → subagent-driven discipline applies.
