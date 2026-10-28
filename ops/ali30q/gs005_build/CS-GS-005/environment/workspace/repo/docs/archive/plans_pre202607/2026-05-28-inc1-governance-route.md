# Plan · Increment 1 · governance route + soul executor (2026-05-28)

> Platform-dialog. Frozen-scope plan for Inc 1 of the KEYSTONE trinity loop.
> Companion to `docs/HANDOFF_20260528_003_increment1_governance_route.md` and
> `docs/KEYSTONE_DESIGN_trinity_governance_main_artery_20260528.md`.
> Discipline: writing-plans → worktree → subagent-driven → verification → draft PR.

## Goal (single sentence)

An `accepted` row in `platform_improvement_proposals` with
`proposed_change.type='code'` flows through a new `soul_executor` service →
DRAFT PR on GitHub → resolution writeback → within ≤10 min of accept on cloud.

Binding-DONE for Inc 1 (carried verbatim from KEYSTONE §"Increment 1"):

> an accepted `proposed_change.type='code'` row in `platform_improvement_proposals`
> (manually inserted is fine for the first proof) gets picked up by the executor
> on cloud within one timer interval, produces a real DRAFT PR, and writes the
> PR URL back to that row. Verified by SQL + `gh pr view`.

## Why this is anchor #2-aligned (recursive product loop)

- The orphan `platform_proposals` queue (soul-local) gave us a self-loop with no
  agent/platform fitness signal. Inc 1 plugs soul into the **governance main
  artery** so any agent-side proposal becomes a code-change candidate behind a
  reputation-weighted vote. That is **agent → vote → soul → PR → human merge**,
  the 中闭环 the handoff names as Inc 1's only justification gate.
- Anti-scope: composite-delta + NAU settlement is Inc 2. Drop `platform_proposals`
  is Inc 3. Both serial, both gated on Inc 1 producing real merged PRs.

## State snapshot (verified before this plan)

- `master` = `cdd2753a2` (origin synced). Local clean.
- Existing `soul_consumer.py` reads orphan `platform_proposals` table (NOT in
  alembic; cloud-only · anchor #5 split-brain confirmed by KEYSTONE audit doc).
- Existing alembic migration `add_improvement_proposals.py` creates
  `platform_improvement_proposals` with `id Integer autoincrement`, NO
  `resolution_*` columns, status varchar(20). **API at `/api/platform/proposals`
  inserts `str(uuid.uuid4())` into that Integer column — cloud reality is
  unknown** (cloud may have manually altered to text/uuid). Inc 1 must NOT
  assume; reads/writes go through SQLAlchemy + dict params, agnostic to
  declared column type.
- `vote_proposal()` on consensus calls `on_consensus_reached(proposal_id, pc, ...)`
  **unconditionally** → creates sandbox experiment. For `type='code'` rows this
  is wrong; sandbox doesn't run code patches.
- `soul_service.ship_to_draft_pr(task, base_dir, branch, commit_msg, cycle_id)`
  is production-ready and **not touched by Inc 1**.

## Frozen sub-tasks (5 · one commit each · serial)

### Sub-task 1 · Singleton `platform_meta` task seed + L3 contract doc

**Why first**: agent-dialog is blocked on the stable `task_id`. Ship early so
they can wire V5 in parallel with the rest of Inc 1. (Per `OUTBOUND` ack.)

**Deliverables**

1. `phase3/backend/alembic/versions/<rev>_seed_soul_meta_task.py`
   - Idempotent: `INSERT … WHERE NOT EXISTS …` (so re-run on cloud is safe).
   - Row: `task_type='platform_meta'`, `title='Soul code-improvement singleton'`,
     `description` referencing this plan + KEYSTONE.
   - **`id`**: stable Integer sentinel **`9_000_001`** (chosen for: well above any
     organic auto-incremented row, recognizable as platform_meta seed, easy to
     spot in SQL). Documented as constant. If cloud `academic_tasks.id` happens
     to be UUID/text, the migration falls back to a deterministic UUID
     (`uuid5(namespace=DNS, name='soul-code-improvement-singleton')`); document
     both values in the L3 contract so V5 can hard-code whichever cloud uses.
   - Down-migration: idempotent DELETE by id (no cascade surprises — votes/proposals
     have `ON DELETE SET NULL` for task_id per existing migration).
2. `docs/L3_CONTRACT_SOUL_GOVERNANCE.md`
   - Sole source of truth for the V5-facing contract.
   - Sections: stable `task_id` constant · `POST /api/platform/proposals` body
     shape (the 6 required fields with example) · the `proposed_change` JSON
     schema for `type='code'` (required keys `type`, `task`; optional
     `target_module`) · polling shape (`GET /api/platform/proposals/{id}` and
     the new `resolution_note/resolved_at/resolved_by/status` fields after Inc 1).
   - Note: agent-side wiring is **agent-dialog's job** (anchor #7); this doc
     only specifies the contract.

**Tests**: alembic migration upgrade/downgrade tested locally via in-memory
SQLite **only for syntax** (FK to academic_tasks not enforced in test). The
real seed verification happens on cloud at Sub-task 4.

**Binding check (sub-task)**: alembic upgrade applies cleanly + L3 doc committed
+ stable id constant present in doc.

---

### Sub-task 2 · Refactor `soul_consumer.py` → `soul_executor.py`

**File renames + new file**

1. Add `phase3/backend/services/soul_executor.py` (new, doesn't delete old yet).
2. Keep `soul_consumer.py` for now (deleted in Inc 3 per KEYSTONE).
3. Add `phase3/backend/alembic/versions/<rev>_proposal_resolution_columns.py`:
   - `ADD COLUMN resolution_note text` (nullable)
   - `ADD COLUMN resolved_at timestamptz` (nullable)
   - `ADD COLUMN resolved_by text` (nullable)
   - No status enum change (status is varchar(20) — `executed_ok` (11 chars),
     `executed_failed` (15 chars) **doesn't fit** in varchar(20)? — `executed_failed`
     is 15 chars, fits. `executed_ok` is 11 chars, fits. Verified at write time.).
   - Index on `(status, (proposed_change->>'type'))` for executor poll perf.
   - Down-migration drops the 3 columns + index.

**`soul_executor.execute_accepted_proposals(db, base_dir, limit=N, _ship_fn=None)`**

- Query (parameterized):
  ```sql
  SELECT id, proposed_change
  FROM platform_improvement_proposals
  WHERE status = 'accepted'
    AND proposed_change->>'type' = 'code'
    AND resolved_by IS NULL
  ORDER BY created_at ASC
  LIMIT :lim
  ```
- For each row:
  - Extract `task = proposed_change.get('task')` (required NL). If missing,
    write back `executed_failed` + note "`proposed_change.task` missing"; do
    NOT raise.
  - Optional `target_module = proposed_change.get('target_module')` (currently
    unused by `ship_to_draft_pr`, but plumbed in metadata; future hook).
  - `cycle_id = f"gov-{proposal_id}"`. `branch = f"soul/gov-{proposal_id}"`.
  - Call `ship_to_draft_pr(task, base_dir, branch, commit_msg, cycle_id)`.
  - Writeback (parameterized UPDATE):
    - `status = 'executed_ok'` (success) | `'executed_failed'` (any stage failure)
    - `resolution_note = pr_url` (success) | `f"{stage}: {detail}"` (failure)
      — truncated to 2000 chars
    - `resolved_at = now()`
    - `resolved_by = 'soul'`
  - `db.commit()` per row (matches existing consumer pattern; one bad row
    doesn't poison the batch).

**Type-route gating in `proposal_consensus.on_consensus_reached`**

- Patch: if `proposed_change.get('type') == 'code'`, **skip sandbox creation**.
  Soul executor will pick it up via its own poll.
- All other types (current default behavior) still trigger sandbox. This is the
  KEYSTONE diagram's `change_type` router materialized as a one-line guard.
- Migration safety: existing rows where `proposed_change` lacks `type` keep
  default behavior (sandbox). No data migration.

**Tests** (`phase3/backend/tests/test_soul_executor.py`)

1. `test_executor_ships_and_writes_back_ok` — fake DB row with `type='code'`,
   monkeypatched `ship_to_draft_pr` returns success. Assert UPDATE has
   `status='executed_ok'`, `resolution_note` contains the PR url,
   `resolved_by='soul'`, `commits == 1`.
2. `test_executor_writes_failed_on_check_stage_fail` — ship returns
   `{success: False, stage: 'check', ...}`. Assert `status='executed_failed'`
   and note contains the stage.
3. `test_executor_writes_failed_on_missing_task` — `proposed_change={'type':'code'}`
   (no `task`). Executor must NOT call ship; UPDATE writes a clear failure note.
4. `test_executor_skips_non_code_type` — SELECT filter excludes non-code rows;
   row with `type='experiment'` left untouched.
5. `test_executor_skips_already_resolved` — `resolved_by='soul'` present →
   filter excludes; no UPDATE fired.
6. `test_executor_empty_queue_noop` — 0 rows → no UPDATE, no commit.
7. `test_consensus_route_skips_sandbox_when_type_is_code` —
   `on_consensus_reached(pid, {'type':'code',...}, factory)` calls factory 0 times.
8. `test_consensus_route_creates_sandbox_when_type_is_not_code` — sanity reverse.

DB + ship are faked (same pattern as existing `test_soul_consumer.py`). No
real Postgres. No real git.

**Binding check (sub-task)**: all 8 unit tests green + existing
`test_soul_consumer.py` still green (consumer not yet deleted; coexist).

---

### Sub-task 3 · Systemd timer for `soul_executor` (10 min interval)

**Deliverables**

1. `phase3/backend/services/soul_executor.py` gains an `if __name__ == '__main__'`
   block (or a thin `__main__.py`) that:
   - Opens a DB session from `utils.database.SessionLocal`.
   - Calls `execute_accepted_proposals(db, base_dir=os.environ['SOUL_BASE_DIR'], limit=5)`.
   - Closes session. Logs results to stdout (systemd captures).
   - Exits 0 even on partial failure (one bad row doesn't kill the timer).
2. `phase3/soul/systemd/nautilus-soul-executor.service`:
   - `Type=oneshot`, `User=ubuntu`, `Group=ubuntu`
   - `WorkingDirectory=/home/ubuntu/nautilus-soul-workspace/phase3`
   - `EnvironmentFile=/home/ubuntu/nautilus-soul-workspace/.soul-env`
   - `ExecStart=/usr/bin/python3 -m services.soul_executor` (run from
     `backend/` cwd → `PYTHONPATH` already set in `.soul-env`)
3. `phase3/soul/systemd/nautilus-soul-executor.timer`:
   - `OnBootSec=2min` (faster than 10min daemon so we can verify quickly)
   - `OnUnitActiveSec=10min`
   - `Persistent=true`

**Isolation from `nautilus-soul.timer` (L1 daemon)**

- L1 daemon runs `python -m soul.daemon` (different module).
- Both touch the same workspace `~/nautilus-soul-workspace`. The L1 daemon's
  L2 scope filter excludes `services/soul_executor.py` (it's in `soul_*`
  service scope — verify by reading current `SELF_IMPROVE_SCOPE` config).
- **State file collision check**: L1 daemon uses `~/.soul-pause` and budget
  files in workspace. Executor must NOT reuse these names — uses
  `~/.soul-executor-pause` if a pause file is ever added (parking lot).
- **Branch collision check**: L1 daemon branches `soul/cycle-*`; executor
  branches `soul/gov-*`. No prefix collision.
- **Git lock collision**: L1 daemon checks out / commits; if executor fires
  during a daemon cycle, second `git checkout` blocks. Mitigation: 10 min
  cadence + 5-row LIMIT keeps work bounded; if collision proves real on cloud,
  Sub-task 4 will catch it and we add a file-lock guard.

**Binding check (sub-task)**: systemd unit files lint-validate locally
(`systemd-analyze verify` if available; otherwise visual review against
existing `nautilus-soul.service`). `python -m services.soul_executor --help`
or no-arg invocation against a faked DB does not crash (test as part of
Sub-task 4 cloud run).

---

### Sub-task 4 · End-to-end cloud verification (binding-DONE)

**Procedure (the binding test)**

1. Local: branch + commits ready · push to PR (still draft).
2. Cloud (manual op by user · platform-dialog has SSH):
   ```
   cd ~/nautilus-soul-workspace && git pull --rebase origin master
   cd phase3/backend && alembic upgrade head            # applies seed + columns
   sudo cp ../soul/systemd/nautilus-soul-executor.{service,timer} /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now nautilus-soul-executor.timer
   ```
3. Insert test proposal (SQL):
   ```sql
   INSERT INTO platform_improvement_proposals
     (task_id, agent_id, root_cause, proposed_change, expected_impact,
      rollback_plan, status, vote_score, vote_count)
   VALUES
     (9000001, <test-agent-id>, 'inc1 e2e proof',
      '{"type":"code","task":"Add a one-line comment to README.md noting Inc 1 e2e timestamp"}'::jsonb,
      'verify governance route', 'revert commit', 'accepted', 99, 99)
   RETURNING id;
   ```
4. Wait ≤10 min. Watch `journalctl -u nautilus-soul-executor.service -f`.
5. **Expected**:
   - A draft PR opens on `chunxiaox/nautilus-core` with branch `soul/gov-<id>`.
   - `SELECT id, status, resolution_note, resolved_by, resolved_at FROM platform_improvement_proposals WHERE id=<id>` returns:
     - `status='executed_ok'`
     - `resolution_note` contains the PR url
     - `resolved_by='soul'`
     - `resolved_at` within last 10 min
   - `gh pr view <pr#>` shows draft state and the branch.
6. Evidence to attach to PR body: the SQL row (text) + `gh pr view` output.

**Binding-DONE for Inc 1** = the above sequence completes within ≤10 min on
cloud, evidence captured.

**Rollback** if anything misbehaves: `sudo systemctl disable --now nautilus-soul-executor.timer` + `alembic downgrade -1` for the resolution columns migration.

---

### Sub-task 5 · Deprecation addendum on `SOUL_PROPOSAL_CONTRACT_20260528.md`

Append a "Closing addendum" section to the doc:

- Status: superseded by KEYSTONE.
- The `platform_proposals` orphan table is **not yet dropped** (parking lot
  for Inc 3 — only after Inc 1 produces real merged PRs proving the executor
  is stable).
- Links: KEYSTONE design + handoff #003 + this plan.

**Binding check**: doc committed in same PR.

---

## What is NOT in Inc 1 (parking lot — verbatim from handoff §"NOT in Inc 1")

- Composite-delta hook + NAU settlement (= Inc 2)
- Dropping `platform_proposals` table (= Inc 3)
- Reflection DB wiring (user-gated)
- V5/Kairos/compass-side wiring (agent-dialog owns it · anchor #7)
- L4 (soul改 agent code · blocked on consent)

If during sub-task work something tempts these, **stop and write it in this
section** rather than expand. Workflow-lock per
`feedback_workflow_lock_goal_until_done_20260527.md`.

## Sequencing & R3 watch

5 sub-tasks · estimated effort: writing-plans (this) + worktree + 5 commits +
two-stage review + verification + PR. Bias is **one clean increment in one
session** if review goes smooth.

R3 ejection plan: if at the 3.5h mark Sub-task 4 (cloud e2e) has not started,
**split**:
- Session A (this one): Sub-tasks 1+2+3+5 + tests + draft PR with NOT-ready
  binding-DONE note.
- Session B (fresh): Sub-task 4 cloud verify · then flip PR to ready-for-merge.

Better two clean sessions than one rushed (handoff §"R3 watch" verbatim).

## Risks & mitigations

| Risk | Mitigation |
|---|---|
| `academic_tasks.id` cloud type ≠ Integer (anchor #5) | Seed migration provides both Integer sentinel (`9000001`) and uuid5 fallback; L3 doc documents whichever applies |
| `platform_improvement_proposals.id` cloud type ≠ Integer (API inserts UUID strings — possible drift) | Executor reads `id` as opaque value via SQLAlchemy params; never coerces; UPDATE uses same value |
| `on_consensus_reached` patch breaks existing sandbox flow | Test 8 explicitly checks non-code path still triggers sandbox; patch is one `if … return` guard at function head |
| Executor + L1 daemon git lock collision in workspace | 10 min cadence + 5-row LIMIT; verify in Sub-task 4; if collision: file-lock guard (parking) |
| `varchar(20)` status field rejects `executed_failed` (15 chars — fits, double-checked) | If migration deploy ever changes column width, executor will surface DB error; not silent corruption |
| `soul_executor` reading **all** accepted rows including legacy where `proposed_change.type` is absent | WHERE clause uses `proposed_change->>'type' = 'code'` — strict equality; NULL is excluded |
| Sandbox migration history / multi-head conflicts (cross-dialog mess noted in [[session_20260525_stage1_day1_full_ship_dogfood_evidence]]) | Two new migrations: depend on each other linearly via `down_revision` chain; verify via `alembic heads` locally before push |

## Two-stage review checklist (mandatory per discipline)

### Stage 1 · spec-conformance review (subagent: general-purpose)
- [ ] Each deliverable in this plan has a matching file in the diff
- [ ] Each binding check passes locally before claiming done
- [ ] No file outside the 5 sub-tasks' declared scope is touched
- [ ] Anchor #7 respected: no V5/Kairos/compass code edits
- [ ] L3 contract doc's stable id matches the seed migration's id
- [ ] Migrations form a single linear chain from current head (no new branch)

### Stage 2 · code-quality review (subagent: general-purpose · "LOC-gate bug class")
- [ ] All UPDATE/INSERT statements use parameterized SQL (no f-string interpolation of values)
- [ ] `resolution_note` truncated before write to prevent unbounded growth
- [ ] No `proposed_change.get('task')` direct call without None-guard (sub-task 2 test 3 enforces)
- [ ] Status writeback is **atomic with the SELECT cursor** OR uses `resolved_by IS NULL` filter (the chosen approach) so a re-poll cannot double-fire ship_to_draft_pr
- [ ] Executor exit code is 0 on partial batch failure (one row crashes, others still tried/committed)
- [ ] `commit_msg` truncated to ≤80 chars (mirrors existing consumer)
- [ ] No assumptions about column type (Int vs UUID) anywhere in code
- [ ] Existing `soul_consumer.py` tests still green (anchor #5: do not break what works)

## Subagent-driven execution plan (per discipline)

For each of Sub-tasks 1, 2, 3, 5: launch a single **implementer subagent** with
this plan section as the prompt + the exact files to write. After it returns:

1. Stage-1 spec-conformance subagent runs against the diff
2. Stage-2 code-quality subagent runs against the diff
3. If either flags issues: a **fix subagent** addresses them
4. Mark TaskUpdate completed

Sub-task 4 is a manual cloud op (cannot be done by subagent); platform-dialog
runs it directly with SSH.

## Pointers (carry into worktree)

- Handoff: `docs/HANDOFF_20260528_003_increment1_governance_route.md`
- KEYSTONE: `docs/KEYSTONE_DESIGN_trinity_governance_main_artery_20260528.md`
- Outbound ack: `docs/OUTBOUND_TO_AGENT_DIALOG_20260528_inc1_unblock_item2_seed.md`
- Reality audit (to be closed by Inc 3): `docs/SOUL_PROPOSAL_CONTRACT_20260528.md`
- Existing soul code (DO NOT touch): `phase3/backend/services/soul_service.py`,
  `phase3/soul/{daemon,systemd}/*`
- Existing consumer (touched only to deprecate, not delete): `phase3/backend/services/soul_consumer.py`,
  `phase3/backend/tests/test_soul_consumer.py`

## Memory hooks (post-ship)

- New memory: `session_20260528_inc1_governance_route_shipped.md` (after Sub-task 4 binding pass)
- Update: `MEMORY.md` pointer entry
- Update: `[[design_keystone_trinity_governance_main_artery_20260528]]` — mark Inc 1 status
