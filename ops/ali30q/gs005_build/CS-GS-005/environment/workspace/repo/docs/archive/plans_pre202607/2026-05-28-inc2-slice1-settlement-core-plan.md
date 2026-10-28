# Inc 2 Slice 1 · Settlement Core Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** When a soul-shipped governance code-proposal is human-merged, a `proposal_outcomes` row is INSERTed (capturing pre-merge `engine_cycle_outcomes` snapshot) and a `pending_nau_rewards` row is INSERTed with `status='pending'`. This is the on-ramp for the 7-day-delayed settlement that Slice 2-3 complete.

**Architecture:** One new SQL table (`proposal_outcomes`) · two new columns on `agents` (`rep_proposing`, `rep_voting`) · one new service module (`services/inc2_settlement.py`) with a single hook function · one new FastAPI endpoint (`POST /api/platform/proposals/{id}/merge-callback`). Hook is idempotent so multiple callbacks for the same proposal do not duplicate rows. No reputation update at merge time (single-source-of-truth at 7d release · per design D1).

**Tech Stack:** Python 3.10+, FastAPI, SQLAlchemy 2.x sync session (matches existing `proposal_consensus.py` pattern), PostgreSQL 15 (cloud production), pytest with raw psycopg cursor (Postgres-only tests · matches `test_auto_stale_approve.py` precedent).

---

## Reference

- **Design doc:** [2026-05-28-inc2-nau-settlement-design.md](./2026-05-28-inc2-nau-settlement-design.md) — Section 2 D1+D5, Section 4 Slice 1, Section 6 Slice 1 tests
- **Inc 1 keystone:** `phase3/backend/services/soul_executor.py` (terminal state writer · sets `resolved_by='soul'` + `status='executed_ok'`)
- **Inc 1.5 binding-done:** [HANDOFF_20260528_006](../HANDOFF_20260528_006_inc1.5_binding_done.md) (executor live · stale-approve live · resolved_by discriminator empirical)
- **Live schemas:** `platform_improvement_proposals` (Inc 1+1.5) · `engine_cycle_outcomes` (cycle telemetry · already production) · `pending_nau_rewards` (LIVE · 3 rows · `status` + `fulfilled_at` columns ready to reuse)
- **Anchor #5 cheat sheet:** [feedback_schema_split_brain_audit_cheatsheet](../../../.claude/projects/.../memory/feedback_schema_split_brain_audit_cheatsheet.md) — `agent_id` is `int` in proposals/pending, `varchar` in ledger. Slice 1 never writes ledger (deferred to Slice 3), so no cast needed here.

---

## Tasks

### Task 1: Migration · `proposal_outcomes` table

**Files:**
- Create: `phase3/backend/alembic/versions/c1b8d4f7e2a3_inc2_proposal_outcomes.py`
- Create: `phase3/backend/tests/test_inc2_migration_proposal_outcomes.py`

**Step 1: Write the failing test**

```python
# phase3/backend/tests/test_inc2_migration_proposal_outcomes.py
"""Inc 2 Slice 1 · verify proposal_outcomes table created by migration."""
import os
import pytest
import psycopg

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="Postgres-only · matches test_auto_stale_approve.py precedent",
)


def _conn():
    return psycopg.connect(os.environ["DATABASE_URL"])


def test_proposal_outcomes_table_exists():
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            "SELECT column_name, data_type "
            "FROM information_schema.columns "
            "WHERE table_name = 'proposal_outcomes' "
            "ORDER BY ordinal_position"
        )
        cols = {r[0]: r[1] for r in cur.fetchall()}
    expected = {
        "proposal_id": "character varying",
        "pre_snapshot": "jsonb",
        "post_snapshot": "jsonb",
        "composite_delta": "real",
        "no_revert": "boolean",
        "graded_at": "timestamp with time zone",
        "graded_by": "character varying",
    }
    assert expected.items() <= cols.items(), (
        f"missing columns: {set(expected) - set(cols)}"
    )


def test_proposal_outcomes_primary_key():
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            "SELECT a.attname "
            "FROM pg_index i JOIN pg_attribute a "
            "  ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey) "
            "WHERE i.indrelid = 'proposal_outcomes'::regclass AND i.indisprimary"
        )
        pk = [r[0] for r in cur.fetchall()]
    assert pk == ["proposal_id"], f"expected proposal_id PK, got {pk}"
```

**Step 2: Run the test to verify it fails**

```bash
cd phase3/backend
PYTHONPATH=. DATABASE_URL=postgresql://test:test@localhost:5432/nautilus_test \
  pytest tests/test_inc2_migration_proposal_outcomes.py -v
```

Expected: FAIL with `UndefinedTable: relation "proposal_outcomes" does not exist`.

**Step 3: Write the migration**

```python
# phase3/backend/alembic/versions/c1b8d4f7e2a3_inc2_proposal_outcomes.py
"""inc2 proposal_outcomes table

Revision ID: c1b8d4f7e2a3
Revises: a3e9c5d1b7f2
Create Date: 2026-05-28

Inc 2 Slice 1: settlement outcomes table. Each row records a single
governance code-proposal's pre-merge snapshot, post-merge snapshot,
composite_delta, and grading metadata. The non-null composite_delta on
this row is the Inc 2 binding-DONE artifact (per design doc Section 7).

Safe to apply multiple times (IF NOT EXISTS guards).
Cloud may apply via raw SQL bypass per handoff #004 line 96-97.
"""
from alembic import op


revision = 'c1b8d4f7e2a3'
down_revision = 'a3e9c5d1b7f2'  # tip of Inc 1.5 migrations
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS proposal_outcomes (
            proposal_id      VARCHAR PRIMARY KEY
                             REFERENCES platform_improvement_proposals(id),
            pre_snapshot     JSONB NOT NULL,
            post_snapshot    JSONB,
            composite_delta  REAL,
            no_revert        BOOLEAN,
            graded_at        TIMESTAMPTZ,
            graded_by        VARCHAR DEFAULT 'soul-settlement-review'
        )
        """
    )


def downgrade():
    op.execute("DROP TABLE IF EXISTS proposal_outcomes")
```

**Step 4: Apply migration (locally) and run test**

```bash
cd phase3/backend
alembic upgrade head
PYTHONPATH=. DATABASE_URL=postgresql://test:test@localhost:5432/nautilus_test \
  pytest tests/test_inc2_migration_proposal_outcomes.py -v
```

Expected: PASS — both `test_proposal_outcomes_table_exists` and `test_proposal_outcomes_primary_key` green.

**Step 5: Commit**

```bash
git add phase3/backend/alembic/versions/c1b8d4f7e2a3_inc2_proposal_outcomes.py \
        phase3/backend/tests/test_inc2_migration_proposal_outcomes.py
git commit -m "feat(inc2 slice1): proposal_outcomes table migration + test

Inc 2 Slice 1 · binding-DONE artifact carrier.
References docs/plans/2026-05-28-inc2-nau-settlement-design.md §4 Slice 1."
```

---

### Task 2: Migration · agents two-dimensional reputation

**Files:**
- Create: `phase3/backend/alembic/versions/d2e9f8c3b4a5_inc2_agents_two_dim_rep.py`
- Create: `phase3/backend/tests/test_inc2_migration_agents_rep.py`

**Step 1: Write the failing test**

```python
# phase3/backend/tests/test_inc2_migration_agents_rep.py
"""Inc 2 Slice 1 · verify agents rep_proposing + rep_voting columns."""
import os
import pytest
import psycopg

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"), reason="Postgres-only"
)


def _conn():
    return psycopg.connect(os.environ["DATABASE_URL"])


def test_agents_has_rep_proposing_and_voting():
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            "SELECT column_name, data_type, column_default "
            "FROM information_schema.columns "
            "WHERE table_name = 'agents' "
            "  AND column_name IN ('rep_proposing', 'rep_voting')"
        )
        rows = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
    assert "rep_proposing" in rows, "missing rep_proposing"
    assert "rep_voting" in rows, "missing rep_voting"
    for name, (dtype, default) in rows.items():
        assert dtype == "real", f"{name} expected real, got {dtype}"
        assert "50" in (default or ""), f"{name} default must be 50.0, got {default!r}"
```

**Step 2: Run test to verify it fails**

```bash
cd phase3/backend
PYTHONPATH=. DATABASE_URL=postgresql://test:test@localhost:5432/nautilus_test \
  pytest tests/test_inc2_migration_agents_rep.py -v
```

Expected: FAIL — missing columns.

**Step 3: Write migration**

```python
# phase3/backend/alembic/versions/d2e9f8c3b4a5_inc2_agents_two_dim_rep.py
"""inc2 agents two-dimensional reputation

Revision ID: d2e9f8c3b4a5
Revises: c1b8d4f7e2a3
Create Date: 2026-05-28

Inc 2 Slice 1: split single reputation_score into two-dim vector per
design doc D4 (prediction-market accuracy across propose vs vote roles).
Existing reputation_score column retained for Inc 1.5 backward compat;
sync trigger deferred to Slice 3 (when first writes happen).

Idempotent. Default 50.0 (NEW tier · per Inc 1.5 weights).
"""
from alembic import op


revision = 'd2e9f8c3b4a5'
down_revision = 'c1b8d4f7e2a3'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE agents "
        "ADD COLUMN IF NOT EXISTS rep_proposing REAL NOT NULL DEFAULT 50.0"
    )
    op.execute(
        "ALTER TABLE agents "
        "ADD COLUMN IF NOT EXISTS rep_voting REAL NOT NULL DEFAULT 50.0"
    )


def downgrade():
    op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS rep_voting")
    op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS rep_proposing")
```

**Step 4: Apply and verify**

```bash
cd phase3/backend
alembic upgrade head
PYTHONPATH=. DATABASE_URL=postgresql://test:test@localhost:5432/nautilus_test \
  pytest tests/test_inc2_migration_agents_rep.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add phase3/backend/alembic/versions/d2e9f8c3b4a5_inc2_agents_two_dim_rep.py \
        phase3/backend/tests/test_inc2_migration_agents_rep.py
git commit -m "feat(inc2 slice1): agents rep_proposing + rep_voting columns

Default 50.0 (NEW tier baseline). reputation_score retained for Inc 1.5
backward compat. Slice 3 writes both columns at settle event."
```

---

### Task 3: Helper · `_snapshot_engine_cycle_outcomes`

**Files:**
- Create: `phase3/backend/services/inc2_settlement.py`
- Create: `phase3/backend/tests/test_inc2_snapshot_helper.py`

**Step 1: Write failing test**

```python
# phase3/backend/tests/test_inc2_snapshot_helper.py
"""Inc 2 Slice 1 · _snapshot_engine_cycle_outcomes helper."""
from unittest.mock import MagicMock

import pytest

from services.inc2_settlement import _snapshot_engine_cycle_outcomes


def test_snapshot_aggregates_basic_metrics():
    db = MagicMock()
    db.execute.return_value.fetchone.return_value = (
        100,   # total_cycles
        85,    # successful_cycles
        0.85,  # success_rate
    )
    result = _snapshot_engine_cycle_outcomes(db)
    assert result == {
        "total_cycles": 100,
        "successful_cycles": 85,
        "success_rate": 0.85,
    }
    assert db.execute.called


def test_snapshot_handles_no_data():
    db = MagicMock()
    db.execute.return_value.fetchone.return_value = (0, 0, None)
    result = _snapshot_engine_cycle_outcomes(db)
    assert result == {
        "total_cycles": 0,
        "successful_cycles": 0,
        "success_rate": None,
    }
```

**Step 2: Run to fail**

```bash
cd phase3/backend
PYTHONPATH=. pytest tests/test_inc2_snapshot_helper.py -v
```

Expected: FAIL — `ImportError: cannot import name '_snapshot_engine_cycle_outcomes'`.

**Step 3: Write helper**

```python
# phase3/backend/services/inc2_settlement.py
"""Inc 2 settlement core.

Slice 1 scope: on_pr_merge_hook + _snapshot_engine_cycle_outcomes.
Slice 2 will extend with grade_pending_settlements.
Slice 3 will extend with process_graded_pending + D4 rep updates.

References docs/plans/2026-05-28-inc2-nau-settlement-design.md.
"""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _snapshot_engine_cycle_outcomes(db) -> dict[str, Any]:
    """Capture current engine_cycle_outcomes aggregate as Inc 2 pre/post snapshot.

    Returns a dict suitable for INSERT into proposal_outcomes.{pre,post}_snapshot
    (JSONB column). Sliced thin so Slice 2 can reuse for post_snapshot.
    """
    from sqlalchemy import text

    row = db.execute(
        text(
            "SELECT "
            "  COUNT(*) AS total_cycles, "
            "  COALESCE(SUM(CASE WHEN passed THEN 1 ELSE 0 END), 0) AS successful_cycles, "
            "  CASE WHEN COUNT(*) > 0 "
            "    THEN AVG(CASE WHEN passed THEN 1.0 ELSE 0.0 END) "
            "    ELSE NULL END AS success_rate "
            "FROM engine_cycle_outcomes"
        )
    ).fetchone()
    return {
        "total_cycles": int(row[0]),
        "successful_cycles": int(row[1]),
        "success_rate": float(row[2]) if row[2] is not None else None,
    }
```

**Step 4: Run to pass**

```bash
cd phase3/backend
PYTHONPATH=. pytest tests/test_inc2_snapshot_helper.py -v
```

Expected: PASS (both tests).

**Step 5: Commit**

```bash
git add phase3/backend/services/inc2_settlement.py \
        phase3/backend/tests/test_inc2_snapshot_helper.py
git commit -m "feat(inc2 slice1): _snapshot_engine_cycle_outcomes helper

Captures total_cycles + successful_cycles + success_rate from production
telemetry. Sliced thin for reuse by Slice 2 post_snapshot."
```

---

### Task 4: `on_pr_merge_hook` function (idempotent)

**Files:**
- Modify: `phase3/backend/services/inc2_settlement.py` (append hook function)
- Create: `phase3/backend/tests/test_inc2_on_pr_merge_hook.py`

**Step 1: Write failing test (idempotent + happy path)**

```python
# phase3/backend/tests/test_inc2_on_pr_merge_hook.py
"""Inc 2 Slice 1 · on_pr_merge_hook · happy + idempotent paths."""
import os
import pytest
import psycopg
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from services.inc2_settlement import on_pr_merge_hook

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"), reason="Postgres-only"
)


@pytest.fixture
def db():
    engine = create_engine(os.environ["DATABASE_URL"])
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.rollback()
    s.close()


def _seed_proposal(db, pid: str, agent_id: int = 9000002) -> None:
    db.execute(text(
        "INSERT INTO platform_improvement_proposals "
        "(id, task_id, agent_id, root_cause, proposed_change, "
        " expected_impact, rollback_plan, status, vote_score, vote_count, "
        " created_at, tenant_id, resolved_by) "
        "VALUES (:id, 9000001, :aid, 'test', "
        "        '{\"type\":\"code\",\"task\":\"noop\"}'::jsonb, "
        "        'test', 'noop', 'executed_ok', 7, 3, NOW(), 'default', 'soul')"
    ), {"id": pid, "aid": agent_id})
    db.commit()


def _cleanup(db, pid: str) -> None:
    db.execute(text("DELETE FROM pending_nau_rewards WHERE source_id = :sid"), {"sid": pid})
    db.execute(text("DELETE FROM proposal_outcomes WHERE proposal_id = :id"), {"id": pid})
    db.execute(text("DELETE FROM platform_improvement_proposals WHERE id = :id"), {"id": pid})
    db.commit()


def test_hook_creates_outcomes_and_pending(db):
    pid = "inc2-slice1-test-happy-1"
    _seed_proposal(db, pid)
    try:
        result = on_pr_merge_hook(
            db,
            proposal_id=pid,
            merged_pr_url="https://github.com/x/y/pull/999",
            nau_amount=10,
        )
        # Verify proposal_outcomes
        row = db.execute(text(
            "SELECT pre_snapshot, composite_delta, no_revert FROM proposal_outcomes WHERE proposal_id = :id"
        ), {"id": pid}).fetchone()
        assert row is not None, "proposal_outcomes row missing"
        assert row[0] is not None, "pre_snapshot must be non-null"
        assert row[1] is None, "composite_delta must be null until Slice 2 grades it"
        assert row[2] is None, "no_revert must be null until Slice 2 grades it"
        # Verify pending_nau_rewards
        pending = db.execute(text(
            "SELECT amount, status, source_id FROM pending_nau_rewards WHERE source_id = :sid"
        ), {"sid": pid}).fetchone()
        assert pending is not None, "pending_nau_rewards row missing"
        assert pending[0] == 10, f"amount expected 10 got {pending[0]}"
        assert pending[1] == "pending", f"status expected pending got {pending[1]}"
        # Verify result
        assert result["proposal_id"] == pid
        assert result["pending_created"] is True
        assert result["outcomes_created"] is True
    finally:
        _cleanup(db, pid)


def test_hook_is_idempotent(db):
    pid = "inc2-slice1-test-idempotent-1"
    _seed_proposal(db, pid)
    try:
        on_pr_merge_hook(db, proposal_id=pid, merged_pr_url="https://x/y/pr/1", nau_amount=10)
        # Second call MUST NOT create duplicate rows
        result = on_pr_merge_hook(db, proposal_id=pid, merged_pr_url="https://x/y/pr/1", nau_amount=10)
        # Verify counts unchanged
        outcomes_count = db.execute(text(
            "SELECT COUNT(*) FROM proposal_outcomes WHERE proposal_id = :id"
        ), {"id": pid}).scalar()
        pending_count = db.execute(text(
            "SELECT COUNT(*) FROM pending_nau_rewards WHERE source_id = :sid"
        ), {"sid": pid}).scalar()
        assert outcomes_count == 1
        assert pending_count == 1
        # Second call result must signal duplicate
        assert result["pending_created"] is False
        assert result["outcomes_created"] is False
    finally:
        _cleanup(db, pid)
```

**Step 2: Run · expect FAIL on `on_pr_merge_hook` ImportError**

```bash
cd phase3/backend
PYTHONPATH=. DATABASE_URL=postgresql://test:test@localhost:5432/nautilus_test \
  pytest tests/test_inc2_on_pr_merge_hook.py -v
```

Expected: FAIL — `ImportError: cannot import name 'on_pr_merge_hook'`.

**Step 3: Write the hook (append to inc2_settlement.py)**

```python
# Append to phase3/backend/services/inc2_settlement.py


def on_pr_merge_hook(
    db,
    proposal_id: str,
    merged_pr_url: str,
    nau_amount: int,
) -> dict[str, Any]:
    """Inc 2 Slice 1 settlement on-ramp · called when human merges soul PR.

    Idempotent: if proposal_outcomes row or pending_nau_rewards row for this
    proposal already exists, the corresponding INSERT is skipped (no duplicate).
    Returns a dict for observability and the callback endpoint response.

    Path A vs B handling deferred to Slice 3 (this hook runs the same regardless).
    For Path B (resolved_by trace contains 'auto_stale'), Slice 3 will write
    nau_amount=0 at release; here we still record pending so audit is complete.
    """
    from sqlalchemy import text

    # 1. Fetch proposal · also ensures it exists
    proposal = db.execute(text(
        "SELECT id, agent_id, status, resolved_by FROM platform_improvement_proposals "
        "WHERE id = :id"
    ), {"id": proposal_id}).fetchone()
    if proposal is None:
        return {
            "proposal_id": proposal_id,
            "pending_created": False,
            "outcomes_created": False,
            "error": "proposal not found",
        }

    # 2. Idempotency · check existing rows
    existing_outcomes = db.execute(text(
        "SELECT 1 FROM proposal_outcomes WHERE proposal_id = :id"
    ), {"id": proposal_id}).fetchone()
    existing_pending = db.execute(text(
        "SELECT 1 FROM pending_nau_rewards WHERE source_id = :sid"
    ), {"sid": proposal_id}).fetchone()

    outcomes_created = False
    pending_created = False

    # 3. INSERT proposal_outcomes (skip if exists)
    if not existing_outcomes:
        pre = _snapshot_engine_cycle_outcomes(db)
        db.execute(text(
            "INSERT INTO proposal_outcomes (proposal_id, pre_snapshot, graded_by) "
            "VALUES (:id, CAST(:snap AS JSONB), 'soul-settlement-review')"
        ), {"id": proposal_id, "snap": json.dumps(pre)})
        outcomes_created = True

    # 4. INSERT pending_nau_rewards (skip if exists)
    if not existing_pending:
        reason = (
            f"Inc 2 Slice 1 · pending settle for {proposal_id} · "
            f"merged: {merged_pr_url}"
        )
        db.execute(text(
            "INSERT INTO pending_nau_rewards "
            "(agent_id, amount, reason, source_id, status) "
            "VALUES (:aid, :amt, :reason, :sid, 'pending')"
        ), {
            "aid": proposal[1],
            "amt": nau_amount,
            "reason": reason,
            "sid": proposal_id,
        })
        pending_created = True

    db.commit()
    logger.info(
        "on_pr_merge_hook: proposal=%s outcomes_created=%s pending_created=%s",
        proposal_id, outcomes_created, pending_created,
    )
    return {
        "proposal_id": proposal_id,
        "pending_created": pending_created,
        "outcomes_created": outcomes_created,
    }
```

**Step 4: Run · expect PASS**

```bash
cd phase3/backend
PYTHONPATH=. DATABASE_URL=postgresql://test:test@localhost:5432/nautilus_test \
  pytest tests/test_inc2_on_pr_merge_hook.py -v
```

Expected: PASS (both `test_hook_creates_outcomes_and_pending` and `test_hook_is_idempotent`).

**Step 5: Commit**

```bash
git add phase3/backend/services/inc2_settlement.py \
        phase3/backend/tests/test_inc2_on_pr_merge_hook.py
git commit -m "feat(inc2 slice1): on_pr_merge_hook idempotent settlement on-ramp

Inserts proposal_outcomes (with pre_snapshot) + pending_nau_rewards
(status='pending'). Idempotent on both rows. Path A/B equal handling
at merge · Slice 3 differentiates at release."
```

---

### Task 5: `POST /api/platform/proposals/{id}/merge-callback` endpoint

**Files:**
- Modify: `phase3/backend/api/platform_proposals.py` (append endpoint)
- Create: `phase3/backend/tests/test_inc2_merge_callback_endpoint.py`

**Step 1: Write failing endpoint test**

```python
# phase3/backend/tests/test_inc2_merge_callback_endpoint.py
"""Inc 2 Slice 1 · merge-callback endpoint smoke test."""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"), reason="Postgres-only"
)


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


def test_merge_callback_endpoint_creates_pending(client):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(os.environ["DATABASE_URL"])
    Session = sessionmaker(bind=engine)
    db = Session()
    pid = "inc2-slice1-endpoint-test-1"
    # Seed
    db.execute(text(
        "INSERT INTO platform_improvement_proposals "
        "(id, task_id, agent_id, root_cause, proposed_change, "
        " expected_impact, rollback_plan, status, vote_score, vote_count, "
        " created_at, tenant_id, resolved_by) "
        "VALUES (:id, 9000001, 9000002, 'test', "
        "        '{\"type\":\"code\",\"task\":\"noop\"}'::jsonb, "
        "        'test', 'noop', 'executed_ok', 7, 3, NOW(), 'default', 'soul')"
    ), {"id": pid})
    db.commit()
    try:
        resp = client.post(
            f"/api/platform/proposals/{pid}/merge-callback",
            json={"merged_pr_url": "https://x/y/pr/1", "nau_amount": 10},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["pending_created"] is True
        assert body["data"]["outcomes_created"] is True
    finally:
        db.execute(text("DELETE FROM pending_nau_rewards WHERE source_id = :s"), {"s": pid})
        db.execute(text("DELETE FROM proposal_outcomes WHERE proposal_id = :p"), {"p": pid})
        db.execute(text("DELETE FROM platform_improvement_proposals WHERE id = :p"), {"p": pid})
        db.commit()
        db.close()
```

**Step 2: Run · expect FAIL (404 because endpoint doesn't exist yet)**

```bash
cd phase3/backend
PYTHONPATH=. DATABASE_URL=postgresql://test:test@localhost:5432/nautilus_test \
  pytest tests/test_inc2_merge_callback_endpoint.py -v
```

Expected: FAIL — 404 Not Found.

**Step 3: Append endpoint to platform_proposals.py**

Insert before the final closing of the file (after `vote_proposal` definition):

```python
# Append to phase3/backend/api/platform_proposals.py


# ---------------------------------------------------------------------------
# POST /api/platform/proposals/{id}/merge-callback (Inc 2 Slice 1)
# ---------------------------------------------------------------------------
@router.post("/{proposal_id}/merge-callback")
def merge_callback(proposal_id: str, body: dict, db=Depends(get_db)):
    """Inc 2 Slice 1 · settlement on-ramp.

    Called by whichever caller detects a soul-shipped PR has been human-merged
    (initially manual / Slice 2 timer-callable / Inc 3+ GitHub webhook). Inserts
    a pending_nau_rewards (status='pending') and a proposal_outcomes
    (pre_snapshot only) row. Idempotent.

    Body:
      - merged_pr_url (str · required): the GitHub PR URL that was merged
      - nau_amount (int · required · >= 0): pending NAU amount to lock

    Returns standard envelope. data = on_pr_merge_hook result dict.
    """
    try:
        merged_pr_url = body.get("merged_pr_url")
        nau_amount = body.get("nau_amount")
        if not merged_pr_url:
            return _err("Missing merged_pr_url")
        if nau_amount is None or not isinstance(nau_amount, int) or nau_amount < 0:
            return _err("nau_amount must be non-negative int")
        from services.inc2_settlement import on_pr_merge_hook
        result = on_pr_merge_hook(
            db,
            proposal_id=proposal_id,
            merged_pr_url=merged_pr_url,
            nau_amount=nau_amount,
        )
        if "error" in result:
            return _err(result["error"])
        return _ok(result)
    except Exception as e:
        logger.error(f"merge_callback error: {e}")
        return _err(str(e))
```

**Step 4: Restart test / run · expect PASS**

```bash
cd phase3/backend
PYTHONPATH=. DATABASE_URL=postgresql://test:test@localhost:5432/nautilus_test \
  pytest tests/test_inc2_merge_callback_endpoint.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add phase3/backend/api/platform_proposals.py \
        phase3/backend/tests/test_inc2_merge_callback_endpoint.py
git commit -m "feat(inc2 slice1): POST /api/platform/proposals/{id}/merge-callback

Thin FastAPI wrapper over on_pr_merge_hook. Body: merged_pr_url + nau_amount.
Idempotent. Returns standard envelope. Caller TBD (Slice 2 polling / Inc 3
GitHub webhook); endpoint exists so anyone can call."
```

---

### Task 6: Cloud raw SQL migration application (anchor #5 alembic bypass)

**Files:**
- Create: `scripts/cloud_apply_inc2_slice1.sh`

**Step 1: Write the script**

```bash
#!/usr/bin/env bash
# Inc 2 Slice 1 · cloud raw-SQL migration application (anchor #5 bypass).
# Per handoff #006 §4 line 3: cloud's alembic chain is divergent · raw SQL
# applied directly to nautilus_production is the canonical path.

set -euo pipefail

PGPASSWORD="${PGPASSWORD:-nautilus2024}" \
  psql -U nautilus_user -h localhost -d nautilus_production <<'SQL'
-- Inc 2 Slice 1 migrations · idempotent · safe to re-run

-- proposal_outcomes table
CREATE TABLE IF NOT EXISTS proposal_outcomes (
    proposal_id      VARCHAR PRIMARY KEY REFERENCES platform_improvement_proposals(id),
    pre_snapshot     JSONB NOT NULL,
    post_snapshot    JSONB,
    composite_delta  REAL,
    no_revert        BOOLEAN,
    graded_at        TIMESTAMPTZ,
    graded_by        VARCHAR DEFAULT 'soul-settlement-review'
);

-- agents two-dim rep
ALTER TABLE agents ADD COLUMN IF NOT EXISTS rep_proposing REAL NOT NULL DEFAULT 50.0;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS rep_voting    REAL NOT NULL DEFAULT 50.0;

-- Verify
SELECT 'proposal_outcomes' AS t, COUNT(*) AS rowcount FROM proposal_outcomes;
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'agents' AND column_name IN ('rep_proposing', 'rep_voting');
SQL
```

**Step 2: Test locally first (against test DB)**

```bash
chmod +x scripts/cloud_apply_inc2_slice1.sh
PGPASSWORD=test bash scripts/cloud_apply_inc2_slice1.sh \
  | tee /tmp/inc2_slice1_apply.log
```

Expected: `CREATE TABLE` then `ALTER TABLE` x2 then verify shows `rowcount=0` + two rep columns listed.

**Step 3: Apply to cloud**

```bash
ssh cloud "bash -s" < scripts/cloud_apply_inc2_slice1.sh \
  | tee /tmp/cloud_inc2_slice1.log
```

Expected: same output pattern. Verify lines confirm both schema changes are present.

**Step 4: Smoke test endpoint on cloud**

```bash
ssh cloud "curl -s -X POST -H 'Content-Type: application/json' \
  -d '{\"merged_pr_url\":\"https://x/y/0\",\"nau_amount\":0}' \
  http://localhost:8000/api/platform/proposals/inc1-e2e-test-20260528-b/merge-callback" \
  | head -10
```

Expected: HTTP 200 envelope. `data.outcomes_created=true` first run, `=false` on re-run (idempotency proof against the executed_ok sentinel row from Inc 1 keystone).

**Step 5: Commit + push**

```bash
git add scripts/cloud_apply_inc2_slice1.sh
git commit -m "ops(inc2 slice1): cloud raw-SQL migration script · anchor #5 bypass"
git push origin master
```

---

### Task 7: Slice 1 BINDING-DONE verification on cloud

**No new files** — pure verification + handoff.

**Step 1: End-to-end test against a real Inc 1.5 ship target**

Find a recent Inc 1.5 sentinel (per handoff #006 Section 1.3 they were left in production):
- `inc1.5-pathb-1c-20260528` (executed_ok · should accept merge-callback)
- `inc1.5-patha-target-20260528` (executed_ok · should accept merge-callback)

Fire the endpoint for one of these:

```bash
ssh cloud "curl -s -X POST -H 'Content-Type: application/json' \
  -d '{\"merged_pr_url\":\"https://github.com/chunxiaoxx/nautilus-core/pull/65\",\"nau_amount\":10}' \
  http://localhost:8000/api/platform/proposals/inc1.5-pathb-1c-20260528/merge-callback"
```

**Step 2: Verify rows landed**

```bash
ssh cloud "PGPASSWORD=nautilus2024 psql -U nautilus_user -h localhost -d nautilus_production -c \"
SELECT po.proposal_id, po.pre_snapshot, pn.amount, pn.status
FROM proposal_outcomes po
LEFT JOIN pending_nau_rewards pn ON pn.source_id = po.proposal_id
WHERE po.proposal_id = 'inc1.5-pathb-1c-20260528';
\""
```

Expected: 1 row with non-null `pre_snapshot`, `amount=10`, `status='pending'`.

**Step 3: Re-fire to confirm idempotency on cloud**

Re-run the curl command. Expected response body: `data.outcomes_created=false` and `data.pending_created=false`.

**Step 4: Update handoff**

Append a Section to `docs/HANDOFF_20260528_006_inc1.5_binding_done.md` (or write `HANDOFF_<date>_007_inc2_slice1.md` depending on session timing) capturing:
- Slice 1 BINDING-DONE achieved
- proposal_outcomes row count after smoke test
- Cloud commits (master tip)
- Next slice (Slice 2 · soul cycle review) preconditions

**Step 5: Commit handoff + push**

```bash
git add docs/HANDOFF_*_007_inc2_slice1.md
git commit -m "docs(soul): handoff inc2 slice1 BINDING-DONE · close brainstorm transition"
git push origin master
```

---

## Slice 1 BINDING-DONE summary

After all 7 tasks: cloud has `proposal_outcomes` table + `agents.rep_proposing` + `agents.rep_voting` columns + `services/inc2_settlement.py:on_pr_merge_hook` + `POST /api/platform/proposals/{id}/merge-callback` endpoint live + verified via real Inc 1.5 sentinel row · idempotency proven by repeat-fire. **Total: ~6 commits · ~80 LOC code + 30 LOC SQL + 200 LOC tests.**

---

## Out of scope (deferred to Slice 2-6)

- Soul cycle settlement_review_due branch (Slice 2)
- post_snapshot / composite_delta / no_revert population (Slice 2)
- platform_nau_ledger writes (Slice 3)
- D4 prediction-market reputation update (Slice 3)
- Path A vs Path B differential at release (Slice 3 · structural emergent)
- Onboarding capital / progression gates (Slice 4)
- Blessing mechanism (Slice 5)
- Collaborative authorship (Slice 6)

Each is its own writing-plans session.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code) (Opus 4.7 · 1M context)
