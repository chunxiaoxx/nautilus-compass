# Cloud ↔ Origin Real Merge · Engineering Plan

> Honest re-scope after 5/27 session attempted full merge mid-session.
> 4-8h estimate was wrong by an order of magnitude.
> This document captures the actual state and proposes a multi-week
> phased reconciliation. Not a one-session task.

## TL;DR

- Cloud (`~/nautilus-mvp` on cloud-server) diverged from `origin/master` for ~2+ months.
- Real divergence: **79 cloud-only commits + 154 uncommitted tracked files + 5 stash entries (oldest 3/12) + 690 origin commits cloud never pulled**.
- Cloud's recent work is patch-driven (deploy SOPs, governance fixes, in-place hotfixes), origin's recent work is feature-driven (engine MVP, audit closed-loop, OSS pivot).
- Cloud's tip for shared files (e.g., `openclaw_protocol.py`) is `backup: server state sync 2026-04-06` — a snapshot, not a maintained branch.
- Reconciliation strategy: **cherry-pick valuable cloud-only work to origin, then reset cloud to origin/master**. Multi-day work across cross-dialog coordination.

## State audit · 5/27 22:30 CST

### Cloud (`cloud-server:~/nautilus-mvp`)

```
branch: master
HEAD:   c0d697514 (2026-05-19 evening ship)
status: ahead 79 / behind 690 of origin/master
```

**Cloud-only commits (79)** · 5/13-5/19 · representative subjects:

- `[deploy] SOP + cron + systemd unit + APIKey hash migration` (6c5bb6eab)
- `[ship] B.1 bounty PG INSERT + #5 a2a SLA enforcement` (05eb9fc47)
- `[ops] V5 daemon systemd port race fix` (e891b6a1b)
- `[ops] reputation trigger backfill` (31d7c516f)
- `[ops] kairos 17-24s 抢钱治理 · PG trigger BEFORE UPDATE` (09d35d9b1)
- `[ship] SOT 双表 trigger + GET /bounties PG + register Redis/rate` (13a52a9d5)
- `[demo] honest demo prep + 彩排逐字稿` (240332a6d + ade039156)
- `[design] P0P2 push · 4 design doc + L2 audit` (7aaa841ac)
- `[merge] 5/19 evening ship · audit-gated · 13 file 736 lines` (c0d697514)

**Uncommitted tracked file modifications (154)** · long-standing accumulation:

| Path prefix | Count | Notes |
|---|---|---|
| `phase3/backend/services/` | 30 | a2a_protocol · agent_brain · raid_engine · openclaw_protocol · reputation · sandbox · soul_bridge etc. |
| `phase3/backend/api/` | 16 | a2a_relay · agents · auth_code · platform · raid · skills · stats · survival etc. |
| `phase3/backend/` (other) | 54 | main.py · daemon_tools.py · kairos_daemon.py · minimax_daemon.py · meta_task_generator.py · memory/ · models/ · sdk/ |
| `phase3/website/` | 28 | App.tsx · Footer · Header · 大量 pages/ · services/web3/ |
| `phase3/docs/`, `phase3/agent-engine/`, root MDs | 26 | misc docs and SECURITY.md |

**Stash entries (5)**:

| Stash | Date | Subject |
|---|---|---|
| `stash@{0}` | 2026-05-26 23:24 | mid-session-uncommitted-2026-05-27 (this session's attempt) |
| `stash@{1}` | 2026-05-19 19:58 | pre-deploy-5/19-evening-stash |
| `stash@{2}` | 2026-03-22 18:49 | WIP · Raid 机制 API 多 Agent 协作审查 |
| `stash@{3}` | 2026-03-15 17:29 | WIP · OAuth callback page + API config |
| `stash@{4}` | 2026-03-12 00:49 | backup-before-deploy-20260312_004915 |

**5/27 session in-place patches (6 · all uncommitted)**:

1. `phase3/backend/services/openclaw_protocol.py` · removed `wallet_address` + `wallet_pk_encrypted` kwargs (onboard 500 fix)
2. `phase3/backend/services/task_marketplace.py` · status filter expanded to include `needs_review`
3. `phase3/backend/api/discover.py` · work_cycle.2_browse + 3_claim descriptions corrected
4. `phase3/backend/api/agent_marketplace.py` · `claim_task` allows needs_review + 2 places `agent.id` → `agent.agent_id` (FK fix)
5. `phase3/agent-engine/llm/client.py` + 6. `phase3/backend/agent_engine/llm/client.py` · DeepSeek provider at priority 0 (synced via sync-agent-engine.sh)

### Origin (`origin/master` on GitHub)

```
HEAD:   b23ab419 (2026-05-27 DeepSeek provider commit)
status: ahead 690 / behind 79 of cloud
```

690 commits since cloud's last sync (5/19). Major themes (per memory log):

- 5/22 audit closed-loop ship (P1-P5 · NAU drift reconcile · agent-platform interface audit)
- 5/23 Phase 0 + Letta MVP
- 5/24 Engine MVP + a2a wiring
- 5/25 Stage 1 Day 1 ship
- 5/26 Path C Gap 1+2 (semantic guard · dogfood backfill)
- 5/27 A1 license sweep + A3 demo wrapper + DeepSeek provider (this session)

### Cross-dialog dependency · shared file evidence

`phase3/backend/services/openclaw_protocol.py`:

- Cloud HEAD touch: `08bfb45bf backup: server state sync 2026-04-06` (snapshot · not feature work)
- Origin recent touches: EvoMap integration · multi-tenant isolation · connect 5 disconnected mechanisms

Implication: **origin is the maintained branch · cloud has been receiving in-place patches against a stale snapshot**.

## Root cause

Cloud-direct ship pattern emerged 5/13-5/19 to address urgent platform issues:

- backend systemd unit needed deploy SOP
- governance fixes (V5 port race · kairos 抢钱 · reputation trigger) needed live cloud patching
- B.1 bounty PG + a2a SLA needed cloud schema sync

These ships landed on `cloud-server:~/nautilus-mvp` without push to origin. Origin meanwhile received feature work (audit closed-loop, engine, OSS pivot) without pull to cloud. 8+ days of bidirectional divergence accumulated.

5/27 session added 6 more in-place patches on cloud (onboard 500, marketplace fragmentation, LLM client) without push.

The pattern is not a bug — it reflects the operational reality of having two parallel work streams (origin for OSS/feature, cloud for live ops) without a merge bridge. This plan proposes the bridge.

## Strategic re-orientation

Going forward, **origin/master is the source-of-truth codebase**. Cloud should pull from origin and apply only minimal local config (env vars, systemd units) on top.

Cloud-only work either:

- **Gets cherry-picked to origin** (if still relevant) and then cloud aligns via reset
- **Gets retired** (if superseded by origin's feature work) and discarded
- **Gets archived** (if historical reference is needed) to a separate branch

## Multi-week phase plan

### Phase 1 · Stabilize · 1 day

**Goal:** preserve current cloud state so reconciliation work can proceed without losing progress.

1. Commit my 6 in-place patches on cloud as a single explicit commit (so they appear in `git log`, not lost in working tree). Branch them as `cloud/5-27-hotfixes-from-platform-dialog`.
2. Commit the 154 uncommitted files as a single explicit "cloud working state snapshot 2026-05-27" commit (preserves visibility, no judgment call yet). Branch as `cloud/pre-merge-uncommitted-snapshot-2026-05-27`.
3. Tag cloud's current `master` as `cloud-pre-merge-2026-05-27` for rollback.
4. Inventory the 5 stash entries; either apply-and-commit each to its own branch, or document & drop.

After Phase 1: cloud's `master` still ahead 79 + behind 690. Working tree clean. Hotfix patches captured.

### Phase 2 · Triage cloud-only commits · 2-3 days · cross-dialog

**Goal:** for each of the 79 cloud-only commits, decide cherry-pick / supersede / archive.

Triage criteria:

- **Cherry-pick** if functionality still needed AND origin doesn't already have an equivalent
- **Supersede** if origin has a different implementation of the same intent (5/22 audit closed-loop probably supersedes 5/19 `B.1 bounty PG INSERT`)
- **Archive** if functionality no longer needed (some demo prep · old design docs)

Cross-dialog touch:

- `phase3/backend/services/openclaw_protocol.py` · platform + V5 + Kairos all read
- `phase3/backend/services/raid_engine.py` · platform + compass
- `phase3/backend/services/a2a_protocol.py` · all dialogs

Each cross-dialog file requires checking with the corresponding dialog before cherry-pick.

### Phase 3 · Triage uncommitted · 2-3 days · cross-dialog

**Goal:** for each of 154 uncommitted files, decide commit / discard.

Triage criteria:

- **Commit** if represents shipped fix not yet pushed (deploy SOP env edits · APIKey hash migration etc.)
- **Discard** if was experimental / now superseded
- **Investigate** if origin/master has its own version (most likely · since cloud's tip is old)

For each cross-dialog file, coordinate with owning dialog.

### Phase 4 · Cherry-pick to origin · 1-2 days

**Goal:** apply triaged keepers from Phase 2 + 3 to a new origin branch.

```
git checkout origin/master
git checkout -b cloud-merge-2026-05-27
git cherry-pick <each-keeper-commit>
# Resolve any conflicts with origin's parallel work (5/22 audit · 5/23 Phase 0 etc)
```

Push branch to origin, open PR for review.

### Phase 5 · Cloud reset · 30 min

**Goal:** align cloud to origin master after the merge PR lands.

```
ssh cloud "cd ~/nautilus-mvp && git fetch origin && git reset --hard origin/master && bash phase3/scripts/sync-agent-engine.sh && sudo systemctl restart nautilus-backend"
```

Then verify all endpoints still work end-to-end (onboard · claim · submit · LLM).

### Phase 6 · Post-merge hygiene · 1 day

**Goal:** prevent re-divergence.

- Add cloud-side pre-commit hook to forbid commits to cloud's local master without first pushing
- Add periodic cron `git fetch origin && git status -b -s` that alerts if cloud behind > N commits
- Document the "cloud is a deployment target, not a development branch" rule
- Update any cloud-side dev workflow docs

### Total estimate

- Phase 1: 1d (must do first · unblocks all else)
- Phase 2: 2-3d (cross-dialog · queue waits)
- Phase 3: 2-3d (cross-dialog · queue waits)
- Phase 4: 1-2d (mostly execution · some conflict resolution)
- Phase 5: 30 min
- Phase 6: 1d

**~7-10 working days end-to-end**, gated by cross-dialog response time.

## Out of scope (do not touch)

- `alembic/versions/` · user hard constraint · separate migration ledger reconciliation
- `_dead_code_backup_*` directories · skip · purely historical
- `node_modules/` · regenerate from package.json post-merge
- `__pycache__` / `*.pyc` · regenerate on backend restart
- `phase3/website/src/pages/_archive_*` · read-only · already archived

## Cross-dialog coordination required

This work touches files owned by other dialogs (per anchor #7 not-touch-other-dialogs rule). The triage in Phase 2 + 3 requires inbound queries to:

- **V5 dialog**: `phase3/backend/services/openclaw_protocol.py`, agent_brain.py, evolution_ledger.py
- **Kairos dialog**: kairos_daemon.py, daemon_comms.py
- **Compass dialog**: agent_management.py, memory_hierarchy.py, soul_bridge.py
- **V7 dialog**: meta_task_generator.py, evolution_ledger.py

Each dialog needs to say: "for my owned files, this cloud-only change is keep / drop / refactor".

Without this input, Phase 2 + 3 cannot complete responsibly. **The work cannot be done by platform dialog alone.**

## Risks

- **Mid-merge production breakage**: cloud-server backend is live. Each Phase 5 reset may briefly break endpoints (~30s). Schedule during low-traffic window.
- **Lost work**: any uncommitted file that gets "discard" decision is gone. Cross-dialog review must explicitly confirm before discard.
- **Cross-dialog deadlock**: if other dialogs don't respond, Phase 2 + 3 stall indefinitely. Mitigation: set 7-day response deadline per inbound, default to "keep + archive" if no response.
- **Re-divergence**: without Phase 6 hygiene, the same problem recurs. Phase 6 is non-optional.

## Success criteria

- Cloud `master` synced to a chosen origin commit (`git status -b -s` = up to date)
- Working tree clean
- All endpoints work end-to-end (onboard, claim, submit, LLM call) post-reset
- Engine 196 tests pass (per origin's test suite)
- Cloud monitoring dashboards show no regression
- A documented merge commit on origin with PR review trail

## Decision queue (for fresh session)

When this plan executes in a future session:

1. Confirm scope hasn't shifted (cloud may have gained more uncommitted files)
2. Decide whether to do Phase 1 first (recommended) or skip to triage
3. Identify which dialogs are available for cross-dialog input
4. Assign per-phase owner (probably platform dialog for execution, other dialogs for sign-off)

## Out-of-session notes

- 5/27 session ran out of R3 budget mid-attempt at this merge
- Token revocation still pending (see `action_token_revoke_20260527.md`)
- Cloud's 6 in-place patches from 5/27 session are functional but uncommitted — Phase 1 must commit them first

See [[session-20260527-external-agent-loop-proven]] for what shipped this session.
