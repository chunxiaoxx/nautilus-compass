"""Soul executor · governance-route consumer (Increment 1 of KEYSTONE trinity loop).

Reads `status='accepted'` rows from the **governance main artery**
(`platform_improvement_proposals`) whose `proposed_change.type='code'` and
ships them through `soul_service.ship_to_draft_pr`, writing the outcome back
to the same row's new resolution columns (`resolution_note`, `resolved_at`,
`resolved_by`).

How this differs from `soul_consumer.py`
----------------------------------------
`soul_consumer.py` (pre-Inc 1) consumed the **orphan** `platform_proposals`
queue (cloud-only, never in alembic, anchor #5 split-brain table). It used
status `'pending' → 'reviewed'`.

`soul_executor.py` (Inc 1) consumes the **governance** queue
`platform_improvement_proposals` (the alembic-tracked table that backs
`/api/platform/proposals`). It reads `status='accepted'` and writes the
terminal states `'executed_ok'` / `'executed_failed'` (per
`docs/L3_CONTRACT_SOUL_GOVERNANCE.md` §5 state machine).

Both files coexist in Inc 1 (anchor #5: do not break what works). Inc 3
will delete `soul_consumer.py` and its orphan table after Inc 1 has
demonstrated stable real merged PRs.

NEVER auto-merges. Draft PR + human review is the gate. The downstream
`ship_to_draft_pr` is unchanged.

References
----------
- docs/KEYSTONE_DESIGN_trinity_governance_main_artery_20260528.md
- docs/plans/2026-05-28-inc1-governance-route.md (Sub-task 2)
- docs/L3_CONTRACT_SOUL_GOVERNANCE.md (§3 proposed_change schema, §4 polling, §5 status)
- phase3/backend/alembic/versions/b8c5d2e0a3f4_add_proposal_resolution_columns.py
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Callable, Optional

logger = logging.getLogger(__name__)


def execute_accepted_proposals(
    db,
    base_dir: str,
    limit: int = 5,
    _ship_fn: Optional[Callable] = None,
) -> list:
    """Process accepted code-improvement proposals in the governance table.

    Args:
        db: SQLAlchemy session-like object exposing `execute(stmt, params)`,
            `commit()`. No async; matches the consumer pattern.
        base_dir: filesystem path of the soul workspace (passed verbatim
            into `ship_to_draft_pr`).
        limit: max rows per invocation. Default 5 matches the 10-min timer
            cadence — keeps work bounded if a backlog ever appears.
        _ship_fn: dependency-injection hook for tests. Production code
            leaves this as None and falls back to `soul_service.ship_to_draft_pr`.

    Returns:
        list of per-proposal outcome dicts. One entry per row processed,
        regardless of success/failure. Empty list if the queue was empty.

    Guarantees:
        - Each row is committed independently (one bad row doesn't poison
          the batch).
        - SELECT WHERE clause filters on `resolved_by IS NULL`, so a re-poll
          cannot double-ship a row that already has a writeback.
        - `resolution_note` is truncated to 2000 chars before write.
        - Rows with missing/malformed `proposed_change.task` are marked
          `executed_failed` (NOT raised) so the executor keeps moving.
    """
    from sqlalchemy import text

    if _ship_fn is None:
        from services.soul_service import ship_to_draft_pr as _ship_fn

    rows = db.execute(
        text(
            "SELECT id, proposed_change FROM platform_improvement_proposals "
            "WHERE status = 'accepted' "
            "AND (proposed_change->>'type') = 'code' "
            # Inc 1.5 followup (2026-05-28) · include auto_stale-tagged rows.
            # Inc 1.5 stale-approve fail-safe sets resolved_by='auto_stale' at
            # status flip (Inc 2 NAU hook discriminator) · executor pickup must
            # not exclude them. Path B Phase 1c binding-done verify (session 3)
            # revealed the gap: stale-approved code proposals were invisible to
            # the executor because the original Inc 1 filter required
            # resolved_by IS NULL. The expanded predicate keeps the original
            # "soul has not touched it" semantics (NULL) AND adds the new
            # "stale-approve fail-safe touched it but ship is still owed"
            # state (auto_stale). After ship, soul_executor._writeback sets
            # resolved_by='soul' so the row exits this window.
            "AND (resolved_by IS NULL OR resolved_by = 'auto_stale') "
            "ORDER BY created_at ASC LIMIT :lim"
        ),
        {"lim": limit},
    ).fetchall()

    results: list = []
    for row in rows:
        proposal_id = row[0]
        proposed_change = row[1]

        # Defensive parse: JSONB rows usually arrive as dict, but in some
        # SQLAlchemy versions / dialects they may come back as str.
        if isinstance(proposed_change, str):
            try:
                proposed_change = json.loads(proposed_change)
            except (ValueError, TypeError):
                proposed_change = None

        task = None
        if isinstance(proposed_change, dict):
            task = proposed_change.get("task")

        # 裁决类任务路由(U34): action=final_review* 走 jury 路径(LLM 判决写回)
        # 而非 ship 代码——soul 终裁岗位的执行器形态(平台代管件)
        _action = proposed_change.get("action") if isinstance(proposed_change, dict) else None
        if _action and str(_action).startswith("final_review"):
            try:
                from services.soul_service import _llm_judge_rows as _judge
                _note = _judge(db, str(_action), str(proposed_change.get("instructions", "")))
                _writeback(db, proposal_id=proposal_id,
                           note=("jury: " + str(_note))[:200], status="executed_ok")
                results.append({"proposal_id": proposal_id, "shipped": False,
                                "pr_url": None, "status": "executed_ok",
                                "note": str(_note)[:150]})
            except Exception as _je:
                _writeback(db, proposal_id=proposal_id,
                           note=("jury err: " + str(_je))[:200], status="executed_failed")
                results.append({"proposal_id": proposal_id, "shipped": False,
                                "pr_url": None, "status": "executed_failed",
                                "note": str(_je)[:150]})
            continue

        # Missing-task guard: still writeback so the proposal terminates,
        # but DO NOT call ship. This is the L3 contract §3 enforcement.
        if not task:
            note = "proposed_change.task missing or empty"
            _writeback(
                db,
                proposal_id=proposal_id,
                note=note,
                status="executed_failed",
            )
            results.append({
                "proposal_id": proposal_id,
                "shipped": False,
                "pr_url": None,
                "status": "executed_failed",
                "note": note,
            })
            continue

        # W4.2 peek-and-claim · atomically take ownership before shipping so the
        # soul daemon's P1 governance path (active after W4.1) or a concurrent
        # executor cannot double-ship this same accepted row.
        if _claim_accepted(db, proposal_id, "soul-executor") is None:
            logger.info(
                "proposal %s already claimed by another consumer · skipping",
                proposal_id,
            )
            continue

        cycle_id = f"gov-{proposal_id}"
        branch = f"soul/gov-{proposal_id}"
        commit_msg = f"soul: gov proposal {proposal_id}"[:80]

        outcome = _ship_fn(
            task,
            base_dir,
            branch=branch,
            commit_msg=commit_msg,
            cycle_id=cycle_id,
        )

        if outcome.get("success"):
            status = "executed_ok"
            pr_url = outcome.get("pr_url")
            note = f"Soul shipped DRAFT PR (human review required): {pr_url}"
        else:
            status = "executed_failed"
            stage = outcome.get("stage") or "unknown"
            detail = outcome.get("detail") or ""
            note = f"Soul rejected at stage '{stage}': {detail}".rstrip(": ")

        _writeback(db, proposal_id=proposal_id, note=note, status=status)
        results.append({
            "proposal_id": proposal_id,
            "shipped": bool(outcome.get("success")),
            "pr_url": outcome.get("pr_url"),
            "status": status,
            "note": note,
        })

    return results


def _claim_accepted(db, proposal_id, claimer: str):
    """Atomically claim an accepted proposal (W4.2 peek-and-claim).

    Flips status 'accepted' → 'claiming' for exactly one caller. Returns the
    (id, proposed_change) row on success, or None if the row was already claimed
    / shipped by another consumer. The `WHERE status='accepted'` predicate is the
    serialization point — only one UPDATE matches a row, the rest get zero rows.
    """
    from sqlalchemy import text

    row = db.execute(
        text(
            "UPDATE platform_improvement_proposals "
            "SET status = 'claiming', resolved_by = :who "
            "WHERE id = :pid AND status = 'accepted' "
            "RETURNING id, proposed_change"
        ),
        {"who": claimer, "pid": proposal_id},
    ).fetchone()
    db.commit()
    return row


def _writeback(db, proposal_id, note: str, status: str) -> None:
    """Atomic single-row UPDATE + commit. Truncates note to 2000 chars."""
    from sqlalchemy import text

    db.execute(
        text(
            "UPDATE platform_improvement_proposals "
            "SET resolution_note = :note, status = :status, "
            "    resolved_at = :ts, resolved_by = 'soul' "
            "WHERE id = :pid"
        ),
        {
            "note": str(note)[:2000],
            "status": status,
            "ts": datetime.now(timezone.utc),
            "pid": proposal_id,
        },
    )
    db.commit()


# Systemd entrypoint ---------------------------------------------------------
# Invoked as `python -m services.soul_executor` by the timer's ExecStart.
# Reads SOUL_BASE_DIR from env (fail loud if missing); opens a session via
# utils.database.SessionLocal; runs one polling cycle; exits 0 even on
# partial failure so the timer keeps cadence.
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    base_dir = os.environ.get("SOUL_BASE_DIR")
    if not base_dir:
        logger.error("SOUL_BASE_DIR environment variable not set; aborting")
        sys.exit(2)

    try:
        from utils.database import SessionLocal
    except ImportError as exc:
        logger.error("Failed to import SessionLocal: %s", exc)
        sys.exit(2)

    db = SessionLocal()
    try:
        outcomes = execute_accepted_proposals(db, base_dir=base_dir, limit=5)
        logger.info(
            "soul_executor cycle complete: %d proposals processed",
            len(outcomes),
        )
        for o in outcomes:
            logger.info(
                "proposal=%s shipped=%s status=%s",
                o.get("proposal_id"), o.get("shipped"), o.get("status"),
            )
    except Exception as exc:  # noqa: BLE001 — timer must not crash
        logger.exception("soul_executor cycle failed: %s", exc)
    finally:
        try:
            db.close()
        except Exception:  # noqa: BLE001
            pass

    sys.exit(0)
