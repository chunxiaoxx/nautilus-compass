# Handoff → fresh session · Increment 1 (governance route + soul executor) · 2026-05-28 #003

> Platform-dialog. The session that locked KEYSTONE + closed cross-dialog ack
> + merged L2 (#57) is ending. This is the actionable starting point for
> Increment 1 of the trinity closed-loop redesign. ✅ = verified. ⏳ = next.

## State snapshot (verified 2026-05-28)

- **master `cdd2753a2`** (origin synced). Local clean.
- **L1 daemon LIVE** on cloud (timer active+enabled · 2h cycle · pause file absent). After L2 merge, next cycle (within ≤2h of merge time `2026-05-28T03:20:37Z`) will autonomously pick from the wider scope (soul + engine + soul_*services) — **first observable test of L2 in prod**.
- **L1 micro-loop output this session**: PRs #52/#54/#55/#56 MERGED (4 real micro-improvements now permanent). #53 has regression comment (lean-reject; user has not yet acted on close/keep).
- **L2 MERGED** as #57 squashed commit. Daemon now reads SELF_IMPROVE_SCOPE + has fixed dedup (pr_title↔goal_id match) + fixed LOC gate (real diff via `_diff_loc`, not whole-file proxy).
- **KEYSTONE design locked** (`docs/KEYSTONE_DESIGN_trinity_governance_main_artery_20260528.md`). NAU anti-reward-hacking clause baked in.
- **Cross-dialog ack closed**: agent-dialog ACKed all 3 contract items (`OUTBOUND_TO_PLATFORM_DIALOG_20260528_ack_increment1.md`). Item 2 = **(a) singleton seed** (platform commits to seeding + documenting stable id in Inc 1).
- Reality audit doc: `docs/SOUL_PROPOSAL_CONTRACT_20260528.md` (the split-brain finding · still accurate · will be closed by Inc 3).

## The trinity loop — three tiers (operating lens)

```
微闭环  · soul internal 2h cycle           ✅ ENHANCED by L2 (this session)
中闭环  · agent vote → soul executor       ⏳ INCREMENT 1 (this handoff)
大闭环  · composite-delta → NAU/reputation ⏳ INCREMENT 2 (queued · serial after 1)
```

Every Inc 1 sub-task should justify itself by: "does it open the 中闭环?" If no, parking lot.

## Increment 1 — actionable plan outline (write the proper plan first; this is the bones)

Goal: an `accepted` proposal in `platform_improvement_proposals` with `proposed_change.type='code'` flows through soul executor → DRAFT PR → writeback. Within ≤10 min of accept.

### Sub-tasks (recommend subagent-driven, TDD per task, one commit each)

1. **Singleton platform_meta task seed + L3 contract doc**
   - Alembic migration: INSERT one row into `academic_tasks` with a stable id (UUID or string per schema constraint), `task_type='platform_meta'`, title `'Soul code-improvement singleton'`, idempotent (skip if already present).
   - New doc `docs/L3_CONTRACT_SOUL_GOVERNANCE.md` documenting the stable id + the exact V5-facing contract (post body shape, polling shape) — single source of truth for agent-dialog.
   - **Why first**: agent-dialog is blocked on this id. Ship it early so they can wire V5 in parallel with the rest of Inc 1.

2. **Refactor `soul_consumer.py` → `soul_executor.py`**
   - Reads from `platform_improvement_proposals WHERE status='accepted' AND proposed_change->>'type'='code' ORDER BY created_at ASC LIMIT N`.
   - Extracts `proposed_change.task` (required NL task) + `proposed_change.target_module` (optional path hint).
   - Calls `soul_service.ship_to_draft_pr(task=…, base_dir=…, branch=f"soul/gov-{proposal_id}", commit_msg=…, cycle_id=f"gov-{proposal_id}")` (unchanged).
   - On result: UPDATE `resolution_note` (PR url or rejection reason) + `status` (`executed_ok` / `executed_failed`) + `resolved_at` + `resolved_by='soul'`. New enum values via migration if needed.
   - Keep tests behavioral (build a fake DB row, monkeypatch ship_to_draft_pr, assert writeback). Do NOT mock everything away.

3. **Systemd timer for `soul_executor`** on cloud, mirroring `nautilus-soul.timer` shape. Interval 10 min (config-driven). Service unit runs `python -m services.soul_executor` (or the entrypoint chosen). Runs as `User=ubuntu` from `~/nautilus-soul-workspace`.

4. **End-to-end verification on cloud**
   - Manually `POST /api/platform/proposals` (or direct INSERT for first test) with `type='code'`, status `pending`.
   - Mark `accepted` (manual UPDATE for first test · agent voting comes after V5 is wired).
   - Wait one timer interval.
   - Verify: a DRAFT PR is opened on GitHub · `resolution_note` in row contains the PR url · `status='executed_ok'`.
   - **Binding DONE = above sequence completes within ≤10 min on cloud, evidence captured via SQL + `gh pr view`.**

5. **`platform_proposals` deprecation note** (parking lot for Inc 3 — do NOT drop yet · wait until executor is stable on real proposals)
   - Add a closing addendum to `docs/SOUL_PROPOSAL_CONTRACT_20260528.md` pointing to KEYSTONE + this handoff.

### What is NOT in Inc 1 (parking lot)
- Composite-delta hook + NAU settlement (= Inc 2 · serial · only after Inc 1 produces real merged PRs).
- Dropping `platform_proposals` (= Inc 3 · only after Inc 2 is stable).
- Reflection DB wiring (user-gated security decision · separate track).
- Any agent-side V5 wiring (agent-dialog owns it · don't touch).
- L4 (soul改 agent code · still blocked on consent).

## What agent-dialog is owning (do NOT do · anchor #7)
- V5 wrapper that emits `POST /api/platform/proposals` with `type='code'` (LLM produces `task_spec`, wrapper fills 6 required fields with defaults).
- V5 `_soul_proposal_poll_loop` mirroring `_a2a_inbox_poll_loop`.
- Anything inside V5/Kairos/compass repos.

## Cloud workflow gotchas (saves hours · carry over from handoff #002)
- Build locally + push; cloud pulls via `git reset --hard origin/master`. Soul service runs as `User=ubuntu` from `~/nautilus-soul-workspace/phase3`.
- `.soul-env` has `DEEPSEEK_API_KEY/DEEPSEEK_BASE_URL/DEEPSEEK_MODEL`. `PYTHONPATH=phase3/backend`.
- Pause soul daemon during destabilizing changes: `touch ~/nautilus-soul-workspace/.soul-pause`. Resume: `rm` it.
- The executor runs in a separate process; verify isolation from L1 daemon (no shared state file collisions). Test before scheduling timer.
- `_siblings/` is the worktree convention.

## Discipline (mandatory · do NOT skip)
- writing-plans → worktree → subagent-driven (implementer + spec review + code-quality review + fix) → verification-before-completion → finishing-a-development-branch (draft PR · human merge gate).
- Same flow that produced L2 (#57). Two-stage review caught the LOC-gate cap bug; do not skip.
- **R3 watch**: this is a substantive change. Plan for two sessions if needed (Inc 1 seed/doc in one, executor + timer + e2e in next). Better to ship in two clean increments than one rushed.
- **R4**: any code change → `git status` first. Use worktree (`_siblings/inc1-governance-route` or similar).
- **anchor #7**: do NOT touch V5/Kairos/compass code. If something looks like it needs an agent-side change, write an inbound instead.
- **anchor #3**: every commit asks "does this open 中闭环 / 大闭环 / or is it motion?" Motion = parking lot.

## User to-dos carried over (not handoff-blocking)
- 🔴 revoke exposed GitHub PAT + rotate DeepSeek key (still pending from 5/27 action_token_revoke).
- Decision on PR #53 (close as won't-fix per the regression comment, or override and merge).
- Decision on reflection DB (`DATABASE_URL` into `.soul-env`) — user-gated.

## Key pointers
- Design: `KEYSTONE_DESIGN_trinity_governance_main_artery_20260528.md`
- Contracts: `OUTBOUND_TO_AGENT_DIALOG_20260528_inc1_unblock_item2_seed.md` (out) · `OUTBOUND_TO_PLATFORM_DIALOG_20260528_ack_increment1.md` (in from V5)
- Reality audit (to be closed by Inc 3): `SOUL_PROPOSAL_CONTRACT_20260528.md`
- Prior handoffs: `HANDOFF_20260528_002_soul_L2L3L4_fresh_session.md` (now superseded for L3/L4 by KEYSTONE)
- Memory: `[[design_keystone_trinity_governance_main_artery_20260528]]` · `[[session_20260528_soul_l2_scope_l3_split_brain]]` · `[[feedback_workflow_lock_goal_until_done_20260527]]`
