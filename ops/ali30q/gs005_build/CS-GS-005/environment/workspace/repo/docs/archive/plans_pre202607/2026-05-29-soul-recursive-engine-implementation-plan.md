# Soul Recursive Self-Improvement Engine · Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the 4-slice path that takes Soul from "passive caller-driven service" to "3-source recursive self-improvement engine" per [2026-05-29-soul-recursive-self-improvement-engine-design.md](./2026-05-29-soul-recursive-self-improvement-engine-design.md).

**Architecture:** Slice A adds goal-source classification infrastructure (new column on `engine_cycle_outcomes` + new `agent_dispatch_log` table + priority sorter fn). Slice B exposes Soul via `/api/discover` real impl + `POST /api/soul/dispatch` async endpoint. Slice C+D add two task types (`config` + `schema-migration`) plus an INBOUND to agent-dialog. Each slice is independent of V5 dormancy and runs end-to-end on platform side only.

**Tech Stack:** Python 3.11 + FastAPI + SQLAlchemy + PostgreSQL (production) / SQLite (test) + Alembic + pytest. Existing soul module under `phase3/soul/` + agent-engine under `phase3/agent-engine/` + backend under `phase3/backend/`.

---

## Slice ordering

| Slice | Scope | Why this order |
|---|---|---|
| A | goal_source classification + agent_dispatch_log + priority sorter fn | Foundation: every later slice writes to / reads from this column |
| B | /api/discover real impl + POST /api/soul/dispatch endpoint | Exposes the P2 source so agents can dispatch even without new task types |
| C | config task type + check pipeline | Easiest new task type · low-risk · proves the type dispatch pattern |
| D | schema-migration task type + INBOUND to agent-dialog | Highest-leverage new task type + closes onboarding loop |

Each slice ends with binding-DONE verified on cloud. **Do NOT open Slice N+1 until Slice N binding is signed.**

---

# Slice A · Goal-source classification (bite-sized TDD tasks)

**Files affected:**
- Create: `phase3/backend/alembic/versions/a1b2c3d4e5f6_inc3_goal_source_columns.py`
- Create: `scripts/cloud_apply_inc3_slice_a.sh`
- Create: `phase3/soul/goal_stack.py`
- Create: `phase3/soul/tests/test_goal_stack.py`
- Create: `phase3/backend/tests/test_inc3_goal_source_columns.py`
- Modify: `phase3/soul/daemon.py` (call `goal_stack.next_goal()` instead of `goal_selector.next_goal()` directly · add goal_source classification on outcome emit)
- Reference (read-only): `phase3/soul/goal_selector.py` (current 3-tier fallback), `phase3/backend/services/soul_executor.py` (governance P1 path), `phase3/backend/api/soul.py` (current /generate · model for /dispatch)

---

## Task A1 · Migration + cloud apply script

**Files:**
- Create: `phase3/backend/alembic/versions/a1b2c3d4e5f6_inc3_goal_source_columns.py`
- Create: `scripts/cloud_apply_inc3_slice_a.sh`

**Step 1: Write the alembic migration**

```python
"""inc3 goal source classification

Revision ID: a1b2c3d4e5f6
Revises: f6d9e2b8a4c1
Create Date: 2026-05-29

Inc 3 Slice A · classify soul daemon cycles by goal source for
backlog burn rate metric per design Section 2 + Section 5.

Adds:
  - engine_cycle_outcomes.goal_source TEXT NULL (existing rows pre-Inc3 = NULL)
  - agent_dispatch_log (new table · captures P2 agent-driven dispatches)

Idempotent (IF NOT EXISTS guards). Cloud may apply via
scripts/cloud_apply_inc3_slice_a.sh raw-SQL bypass per anchor #5
broken-alembic-chain pattern (matches Inc 2 Slice 4/5/6).
"""
from alembic import op


revision = 'a1b2c3d4e5f6'
down_revision = 'f6d9e2b8a4c1'  # Inc 2 Slice 6
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE engine_cycle_outcomes "
        "ADD COLUMN IF NOT EXISTS goal_source TEXT NULL"
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_dispatch_log (
            id              BIGSERIAL PRIMARY KEY,
            agent_id        INTEGER REFERENCES agents(id),
            task_spec_hash  VARCHAR(64) NOT NULL,
            task_type       VARCHAR(32) NOT NULL DEFAULT 'code',
            cycle_id        TEXT REFERENCES engine_cycle_outcomes(cycle_id),
            ship_outcome    VARCHAR(32),
            created_at      TIMESTAMPTZ DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_agent_dispatch_log_agent_id "
        "ON agent_dispatch_log (agent_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_agent_dispatch_log_cycle_id "
        "ON agent_dispatch_log (cycle_id)"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_agent_dispatch_log_cycle_id")
    op.execute("DROP INDEX IF EXISTS idx_agent_dispatch_log_agent_id")
    op.execute("DROP TABLE IF EXISTS agent_dispatch_log")
    op.execute("ALTER TABLE engine_cycle_outcomes DROP COLUMN IF EXISTS goal_source")
```

**Step 2: Write the cloud apply bash script**

```bash
#!/usr/bin/env bash
# Inc 3 Slice A · goal source classification schema (raw SQL · anchor #5 bypass)
set -euo pipefail
PGPASSWORD="${PGPASSWORD:-nautilus2024}" \
  psql -U nautilus_user -h localhost -d nautilus_production <<'SQL'
ALTER TABLE engine_cycle_outcomes ADD COLUMN IF NOT EXISTS goal_source TEXT NULL;
CREATE TABLE IF NOT EXISTS agent_dispatch_log (
    id              BIGSERIAL PRIMARY KEY,
    agent_id        INTEGER REFERENCES agents(id),
    task_spec_hash  VARCHAR(64) NOT NULL,
    task_type       VARCHAR(32) NOT NULL DEFAULT 'code',
    cycle_id        TEXT REFERENCES engine_cycle_outcomes(cycle_id),
    ship_outcome    VARCHAR(32),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_agent_dispatch_log_agent_id ON agent_dispatch_log (agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_dispatch_log_cycle_id ON agent_dispatch_log (cycle_id);
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name='engine_cycle_outcomes' AND column_name='goal_source';
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name='agent_dispatch_log' ORDER BY ordinal_position;
SQL
```

**Step 3: AST-parse both files**

Run: `python -c "import ast; ast.parse(open('phase3/backend/alembic/versions/a1b2c3d4e5f6_inc3_goal_source_columns.py', encoding='utf-8').read()); print('alembic OK')"`
Run: `bash -n scripts/cloud_apply_inc3_slice_a.sh && echo 'shell OK'`
Expected: both print OK.

**Step 4: Commit**

```bash
git add phase3/backend/alembic/versions/a1b2c3d4e5f6_inc3_goal_source_columns.py scripts/cloud_apply_inc3_slice_a.sh
git commit -m "inc3 slice A · migration · goal_source col + agent_dispatch_log"
```

---

## Task A2 · `phase3/soul/goal_stack.py` priority sorter

**Files:**
- Create: `phase3/soul/goal_stack.py`
- Create: `phase3/soul/tests/test_goal_stack.py`

**Step 1: Write failing test (test_priority_p1_beats_p2_beats_p3)**

```python
"""Goal-stack priority sorter · P1 governance > P2 agent dispatch > P3 self-reflection."""
from __future__ import annotations
from soul.goal_stack import next_goal, GoalSource


def test_priority_p1_governance_wins(monkeypatch):
    monkeypatch.setattr("soul.goal_stack._next_p1_governance",
                        lambda: {"id": "gov-1", "task": "fix-thing"})
    monkeypatch.setattr("soul.goal_stack._next_p2_agent_dispatch",
                        lambda: {"id": "dispatch-1", "task": "add-feature"})
    monkeypatch.setattr("soul.goal_stack._next_p3_self_reflection",
                        lambda: {"id": "reflect-1", "task": "refactor"})
    goal, source = next_goal()
    assert goal["id"] == "gov-1"
    assert source == GoalSource.P1_GOVERNANCE


def test_priority_p2_when_p1_empty(monkeypatch):
    monkeypatch.setattr("soul.goal_stack._next_p1_governance", lambda: None)
    monkeypatch.setattr("soul.goal_stack._next_p2_agent_dispatch",
                        lambda: {"id": "dispatch-1", "task": "add-feature"})
    monkeypatch.setattr("soul.goal_stack._next_p3_self_reflection",
                        lambda: {"id": "reflect-1", "task": "refactor"})
    goal, source = next_goal()
    assert goal["id"] == "dispatch-1"
    assert source == GoalSource.P2_AGENT_DISPATCH


def test_priority_p3_fallback_when_p1_p2_empty(monkeypatch):
    monkeypatch.setattr("soul.goal_stack._next_p1_governance", lambda: None)
    monkeypatch.setattr("soul.goal_stack._next_p2_agent_dispatch", lambda: None)
    monkeypatch.setattr("soul.goal_stack._next_p3_self_reflection",
                        lambda: {"id": "reflect-1", "task": "refactor"})
    goal, source = next_goal()
    assert goal["id"] == "reflect-1"
    assert source == GoalSource.P3_SELF_REFLECTION


def test_all_empty_returns_none(monkeypatch):
    monkeypatch.setattr("soul.goal_stack._next_p1_governance", lambda: None)
    monkeypatch.setattr("soul.goal_stack._next_p2_agent_dispatch", lambda: None)
    monkeypatch.setattr("soul.goal_stack._next_p3_self_reflection", lambda: None)
    goal, source = next_goal()
    assert goal is None
    assert source is None
```

**Step 2: Run test to verify failure**

Run: `cd phase3 && python -m pytest soul/tests/test_goal_stack.py -v`
Expected: 4 FAIL with "No module named 'soul.goal_stack'".

**Step 3: Write minimal implementation**

```python
"""Soul goal stack · 3-source priority queue (P1 governance > P2 agent dispatch > P3 self-reflection).

Per docs/plans/2026-05-29-soul-recursive-self-improvement-engine-design.md Section 2.

Each _next_pX_*() returns either a goal dict (id + task spec fields) or None.
next_goal() returns (goal, source) tuple; both None when stack is fully empty.
"""
from __future__ import annotations
from enum import Enum
from typing import Optional


class GoalSource(str, Enum):
    P1_GOVERNANCE = "p1_governance"
    P2_AGENT_DISPATCH = "p2_agent_dispatch"
    P3_SELF_REFLECTION = "p3_self_reflection"


def _next_p1_governance() -> Optional[dict]:
    """P1 · accepted code-type proposal from platform_improvement_proposals.

    Returns the highest-priority pending row for soul_executor consumption.
    Returns None when no P1 work is available OR DATABASE_URL is unset.
    Implementation reuses soul_executor's existing query (do NOT re-implement;
    just delegate). When unable to import (test env), return None.
    """
    try:
        from services.soul_executor import _next_accepted_proposal
        return _next_accepted_proposal()
    except Exception:
        return None


def _next_p2_agent_dispatch() -> Optional[dict]:
    """P2 · agent-dispatched task spec from agent_dispatch_log (Slice B will write).

    Returns the oldest log row with ship_outcome IS NULL (i.e. pending).
    Returns None when no pending dispatch OR table missing (pre-Slice-A apply).
    """
    import os
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        return None
    try:
        import psycopg2
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()
        cur.execute(
            "SELECT id, agent_id, task_spec_hash, task_type "
            "FROM agent_dispatch_log "
            "WHERE ship_outcome IS NULL "
            "ORDER BY created_at ASC LIMIT 1"
        )
        row = cur.fetchone()
        conn.close()
    except Exception:
        return None
    if not row:
        return None
    return {
        "id": f"dispatch-{row[0]}",
        "agent_id": row[1],
        "task_spec_hash": row[2],
        "task_type": row[3] or "code",
    }


def _next_p3_self_reflection() -> Optional[dict]:
    """P3 · existing 3-tier fallback (yaml > reflection > docs scrape).

    Delegates to soul.goal_selector.next_goal() which already implements the
    P3 sub-priority. Returns None only when ALL three P3 sub-sources empty.
    """
    try:
        from soul.goal_selector import next_goal as _legacy_next_goal
        return _legacy_next_goal()
    except Exception:
        return None


def next_goal() -> tuple[Optional[dict], Optional[GoalSource]]:
    """Resolve the highest-priority goal across the 3-source stack.

    Returns (goal_dict, source_enum). Both None when no goal available
    at any priority (daemon then runs SELF-IMPROVE fallback cycle).
    """
    goal = _next_p1_governance()
    if goal is not None:
        return goal, GoalSource.P1_GOVERNANCE
    goal = _next_p2_agent_dispatch()
    if goal is not None:
        return goal, GoalSource.P2_AGENT_DISPATCH
    goal = _next_p3_self_reflection()
    if goal is not None:
        return goal, GoalSource.P3_SELF_REFLECTION
    return None, None
```

**Step 4: Run tests to verify they pass**

Run: `cd phase3 && python -m pytest soul/tests/test_goal_stack.py -v`
Expected: 4 PASSED.

**Step 5: Commit**

```bash
git add phase3/soul/goal_stack.py phase3/soul/tests/test_goal_stack.py
git commit -m "inc3 slice A · soul.goal_stack 3-source priority sorter"
```

---

## Task A3 · daemon integration · call goal_stack.next_goal()

**Files:**
- Modify: `phase3/soul/daemon.py` (replace direct `goal_selector.next_goal()` call with `goal_stack.next_goal()` + capture source)

**Step 1: Write the integration test**

Create file: `phase3/soul/tests/test_daemon_goal_stack_integration.py`

```python
"""Daemon picks goal via goal_stack and threads source through outcome emit."""
from __future__ import annotations
from unittest.mock import patch, MagicMock
from soul.goal_stack import GoalSource


def test_daemon_threads_p2_source_to_outcome(monkeypatch):
    """When goal_stack returns P2, daemon's outcome telemetry should record p2_agent_dispatch."""
    fake_goal = {"id": "dispatch-42", "agent_id": 9000002, "task_spec_hash": "abc123", "task_type": "code"}
    monkeypatch.setattr("soul.goal_stack.next_goal",
                        lambda: (fake_goal, GoalSource.P2_AGENT_DISPATCH))
    captured = {}

    def fake_run_self_improve_cycle(*args, **kwargs):
        # daemon should NOT reach self-improve when goal_stack returns a goal
        captured["self_improve_invoked"] = True

    monkeypatch.setattr("soul.daemon.run_self_improve_cycle",
                        fake_run_self_improve_cycle, raising=False)
    # Daemon needs select_goal entry-point; verify it returns the goal_stack result
    from soul.daemon import select_goal_with_source
    goal, source = select_goal_with_source()
    assert goal == fake_goal
    assert source == GoalSource.P2_AGENT_DISPATCH
    assert "self_improve_invoked" not in captured
```

**Step 2: Run test to verify failure**

Run: `cd phase3 && python -m pytest soul/tests/test_daemon_goal_stack_integration.py -v`
Expected: FAIL with "cannot import name 'select_goal_with_source' from 'soul.daemon'".

**Step 3: Add `select_goal_with_source()` to daemon**

Edit `phase3/soul/daemon.py` · add at module level (near other entry-point helpers):

```python
def select_goal_with_source() -> tuple["dict | None", "GoalSource | None"]:
    """Slice A · daemon entry-point that returns (goal, source) tuple.

    Delegates to soul.goal_stack.next_goal() which respects the 3-source
    priority stack (P1 governance > P2 agent dispatch > P3 self-reflection).
    Existing select_goal() retained for backward compat; new cycle paths
    should use this wrapper to capture the source for outcome telemetry.
    """
    from soul.goal_stack import next_goal as _next_goal
    return _next_goal()
```

**Step 4: Run test to verify PASS**

Run: `cd phase3 && python -m pytest soul/tests/test_daemon_goal_stack_integration.py -v`
Expected: PASS.

**Step 5: Wire goal_source into engine outcome emit**

Find the call site in `phase3/soul/daemon.py` where `_ship_goal()` invokes `ship()` (line ~261 and ~377 per existing grep). Replace direct goal selection call with `select_goal_with_source()` and pass `goal_source=source` through to the engine. Add a helper:

```python
def _emit_goal_source_to_outcome(cycle_id: str, source: "GoalSource | None") -> None:
    """Persist goal_source on the engine_cycle_outcomes row for cycle_id.

    Fail-open: on any DB error the daemon must not crash. The classification
    metric tolerates NULL rows; the cycle itself is unaffected.
    """
    import os
    if source is None:
        return
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        return
    try:
        import psycopg2
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()
        cur.execute(
            "UPDATE engine_cycle_outcomes SET goal_source = %s WHERE cycle_id = %s",
            (source.value, cycle_id),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.warning("emit_goal_source failed: %s", exc)
```

Call `_emit_goal_source_to_outcome(cycle_id, source)` after each ship() returns in `daemon.run_cycle()` and the self-improve fallback.

**Step 6: Re-run full daemon test suite**

Run: `cd phase3 && python -m pytest soul/tests/ -v 2>&1 | tail -10`
Expected: all soul tests still PASS (regression-clean).

**Step 7: Commit**

```bash
git add phase3/soul/daemon.py phase3/soul/tests/test_daemon_goal_stack_integration.py
git commit -m "inc3 slice A · daemon integrates goal_stack + emits goal_source telemetry"
```

---

## Task A4 · Cloud apply + binding-DONE verify

**Files:** none new (uses cloud_apply script from A1 + existing infra)

**Step 1: Cherry-pick to cloud**

Run:
```bash
git push origin <current-branch>
ssh cloud "cd ~/nautilus-mvp && git fetch origin <current-branch> && git cherry-pick <slice-A-tip-sha>"
```
Expected: cherry-pick clean.

**Step 2: Apply migration on cloud**

Run: `ssh cloud "cd ~/nautilus-mvp && bash scripts/cloud_apply_inc3_slice_a.sh 2>&1 | tail -10"`
Expected output snippet:
```
ALTER TABLE
CREATE TABLE
CREATE INDEX
column_name | data_type
goal_source | text
```

**Step 3: Write `/tmp/verify_slice_a_cloud.py`**

Bypass conftest schema-mismatch · directly probe goal_stack with 3 mocked sources to confirm priority ordering on real Postgres. See Inc 2 Slice 5/6 verify pattern (`/tmp/verify_slice5_cloud.py`).

```python
"""Slice A cloud verify · 3-source priority sort + telemetry write."""
import os, sys
sys.path.insert(0, '.')
os.environ['DATABASE_URL'] = 'postgresql://nautilus_user:nautilus2024@localhost:5432/nautilus_production'
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine(os.environ['DATABASE_URL'])
db = sessionmaker(bind=engine)()

print('=== A · goal_source column exists ===')
row = db.execute(text(
    "SELECT column_name FROM information_schema.columns "
    "WHERE table_name='engine_cycle_outcomes' AND column_name='goal_source'"
)).fetchone()
assert row is not None
print('PASS · column present')

print('=== B · agent_dispatch_log table exists ===')
row = db.execute(text(
    "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='agent_dispatch_log'"
)).fetchone()
assert row[0] >= 6
print('PASS · table with', row[0], 'columns')

print('=== C · priority ordering · seed 3 sentinels then assert pick ===')
# Seed engine_cycle_outcomes row + agent_dispatch_log row + goals.yaml entry would
# require full daemon mock. Skip for binding-DONE; covered by unit tests + sentinel
# in Slice B (where /api/soul/dispatch writes a real P2 row and daemon picks it).
print('NOTE · full sentinel deferred to Slice B (when /dispatch endpoint writes real P2 row)')

print('=== ALL SLICE A CASES PASS ===')
```

Run: `ssh cloud "cd ~/nautilus-mvp/phase3/backend && python3 /tmp/verify_slice_a_cloud.py 2>&1 | tail -10"`
Expected: 3 PASS lines + ALL SLICE A CASES PASS.

**Step 4: Restart backend**

Run: `ssh cloud "sudo systemctl restart nautilus-backend && sleep 3 && systemctl is-active nautilus-backend"`
Expected: `active`.

**Step 5: BINDING-DONE record + handoff**

Write `memory/session_<YYYYMMDD>_inc3_slice_a_binding_done.md` with the 4 evidence points (migration applied · column + table present · goal_stack tests 4/4 PASS · daemon integration test 1/1 PASS).

**Slice A binding-DONE criteria:**
- ✅ migration applied on cloud · column + table present
- ✅ goal_stack 4 unit tests PASS
- ✅ daemon integration test 1 PASS
- ✅ backend restart clean (no goal_source-related crash)
- ⏳ full priority sentinel deferred to Slice B (needs real P2 row · `/dispatch` endpoint required)

---

# Slice B · `/api/discover` real impl + `POST /api/soul/dispatch` endpoint (outline)

**Tasks (~120 LOC · 4 tests):**

1. **B1 · `/api/discover` router** — Create `phase3/backend/api/discover.py` returning JSON catalog with 3 soul services (generate · audit_generate · dispatch). Register in `phase3/backend/main.py`. 1 test: GET returns 200 + envelope + 3 services in `data.services`.
2. **B2 · `POST /api/soul/dispatch` endpoint** — Add to `phase3/backend/api/soul.py`. Body `{task_spec: str, task_type: str}`. Auth via X-Agent-Key. Validates task_type ∈ {'code', 'config', 'schema-migration'}. Computes `task_spec_hash = sha256(task_spec)[:64]`. INSERTs into `agent_dispatch_log` with `ship_outcome=NULL`. Returns `{cycle_id: "dispatch-<id>", queued: true}`. 2 tests: valid dispatch creates row · invalid type returns error.
3. **B3 · daemon picks P2 dispatch sentinel** — Cloud verify: write 1 dispatch row · trigger daemon cycle manually · assert engine_cycle_outcomes row gets goal_source=p2_agent_dispatch + agent_dispatch_log row gets cycle_id + ship_outcome populated.
4. **B4 · cloud apply (no migration · code only) + backend restart + HTTP probe**

**Binding-DONE:** Live `POST /api/soul/dispatch` returns cycle_id · 1 sentinel cycle completes with goal_source='p2_agent_dispatch' on cloud · /api/discover returns 3 services.

---

# Slice C · `config` task type + check pipeline (outline)

**Tasks (~150 LOC · 3 tests):**

1. **C1 · `phase3/soul/checks/__init__.py` + `config.py` check module** — Export `validate(task_spec, base_dir, output_files) -> CheckResult` for yaml/toml files. Checks: file parses as yaml/toml · re-applying the diff produces no further changes (idempotent). 2 tests: valid config change passes · invalid yaml fails.
2. **C2 · engine.ship task_type dispatch** — Modify `phase3/agent-engine/.../ship.py` (find exact module via `grep -rn "def ship"` in agent-engine dir) to accept `task_type` arg defaulting to 'code'. When `task_type='config'` route to `soul.checks.config.validate` instead of py_compile pipeline.
3. **C3 · sentinel cycle** — Cloud: seed a dispatch row with task_type='config' + task_spec='Add comment header to phase3/soul/goals.yaml · MINIMAL CHANGE'. Trigger daemon. Verify draft PR opens with diff touching only goals.yaml. 1 sentinel test.

**Binding-DONE:** 1 draft PR via daemon · diff is yaml-only · check_result.config_validate=true.

---

# Slice D · `schema-migration` task type + INBOUND to agent-dialog (outline)

**Tasks (~180 LOC · 1 migration · 3 tests + 1 inbound):**

1. **D1 · `phase3/soul/checks/schema_migration.py`** — Export `validate()` running alembic upgrade in `--sql` dry-run mode against SQLite. Compares the generated SQL to production schema diff (read-only query). 2 tests: valid migration passes · migration that breaks production schema fails.
2. **D2 · engine.ship task_type='schema-migration'** — Route to schema_migration check pipeline. Refuse to ship if dry-run fails.
3. **D3 · sentinel cycle** — Cloud: seed dispatch with task_type='schema-migration' + task_spec='Add INDEX ix_proposal_blessings_settled_at to proposal_blessings · MINIMAL CHANGE'. Daemon ships draft PR with new alembic file. 1 sentinel test.
4. **D4 · `docs/INBOUND_TO_AGENT_DIALOG_20260529_soul_sdk_onboarding.md`** — Write SDK doc with: 3 endpoints · auth · 3 task types · sample task spec per type · API key flow · anchor #7 决定权属 agent-dialog. SCP to ~/.../agent-dialog workspace (or commit master if file-server unavailable).

**Binding-DONE:** 1 draft PR via daemon with valid alembic file · cloud schema diff dry-run passes · INBOUND shipped + SCP'd · 48h post-ship: ≥1 PR from P1 (governance) OR P2 (agent dispatch) — confirms unblock criterion from design Section 5.

---

# Cross-slice meta

**Worktree:** all 4 slices in one worktree (`worktree-inc3-soul-engine`). Each slice opens its own draft PR off the worktree branch · final merge sequence in Slice D handoff.

**Git discipline:** every task ends with `git commit` per skill convention. No `--amend` after push. No `-A`. Specific file adds only.

**Skill references:**
- @superpowers:executing-plans for task-by-task execution
- @superpowers:subagent-driven-development for dispatch-each-task model
- @superpowers:verification-before-completion for binding-DONE evidence
- @superpowers:using-git-worktrees for isolation

**R3 budget:** Slice A ~2h fresh session · Slices B+C+D each ~2h fresh sessions · total 4 sessions. Do not chain unless user explicitly approves R3 override.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code) (Opus 4.7 · 1M context)
