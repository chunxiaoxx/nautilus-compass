"""
Execution Checkpoint Service -- LangGraph-style durable execution.

Saves execution state at each step so interrupted workflows can resume
from the last checkpoint instead of starting over.

Usage:
    from services.checkpoint import save_checkpoint, load_checkpoint, clear_checkpoint

    # At start -- check for existing checkpoint
    cp = load_checkpoint(db, f"proposal-{task_id}")
    if cp:
        # Resume from cp["step"], using cp["state"]

    # After each major step
    save_checkpoint(db, f"proposal-{task_id}", "analysis_complete", {
        "proposal_data": {...},
    })

    # On success -- remove checkpoint
    clear_checkpoint(db, f"proposal-{task_id}")
"""
import json
import logging
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def save_checkpoint(
    db: Session,
    execution_id: str,
    step: str,
    state: Dict[str, Any],
    execution_type: str = "raid",
) -> bool:
    """Save a checkpoint for a running execution.

    Uses upsert semantics: inserts on first call, updates on subsequent calls
    for the same execution_id.

    Args:
        db: SQLAlchemy session.
        execution_id: Unique key for this execution (e.g. "proposal-42").
        step: Name of the completed step (e.g. "context_gathered").
        state: Serialisable dict of intermediate results needed to resume.
        execution_type: Category tag ("raid", "proposal", etc.).

    Returns:
        True on success, False on failure (logged, never raises).
    """
    try:
        existing = db.execute(
            text("SELECT id FROM execution_checkpoints WHERE execution_id = :eid"),
            {"eid": execution_id},
        ).fetchone()

        if existing:
            db.execute(
                text(
                    "UPDATE execution_checkpoints SET "
                    "current_step = :step, state = CAST(:state AS jsonb), "
                    "updated_at = NOW() "
                    "WHERE execution_id = :eid"
                ),
                {"step": step, "state": json.dumps(state), "eid": execution_id},
            )
        else:
            db.execute(
                text(
                    "INSERT INTO execution_checkpoints "
                    "(execution_id, execution_type, current_step, state) "
                    "VALUES (:eid, :etype, :step, CAST(:state AS jsonb))"
                ),
                {
                    "eid": execution_id,
                    "etype": execution_type,
                    "step": step,
                    "state": json.dumps(state),
                },
            )
        db.commit()
        logger.debug("checkpoint saved: %s step=%s", execution_id, step)
        return True
    except Exception as e:
        logger.warning("checkpoint save failed for %s: %s", execution_id, e)
        try:
            db.rollback()
        except Exception:
            pass
        return False


def load_checkpoint(db: Session, execution_id: str) -> Optional[Dict[str, Any]]:
    """Load the latest checkpoint for an execution.

    Args:
        db: SQLAlchemy session.
        execution_id: The execution key to look up.

    Returns:
        Dict with keys (step, state, execution_type, updated_at) or None.
    """
    try:
        row = db.execute(
            text(
                "SELECT current_step, state, execution_type, updated_at "
                "FROM execution_checkpoints WHERE execution_id = :eid"
            ),
            {"eid": execution_id},
        ).fetchone()
        if not row:
            return None

        state = row.state
        if isinstance(state, str):
            state = json.loads(state)

        return {
            "step": row.current_step,
            "state": state,
            "execution_type": row.execution_type,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }
    except Exception as e:
        logger.warning("checkpoint load failed for %s: %s", execution_id, e)
        return None


def clear_checkpoint(db: Session, execution_id: str) -> bool:
    """Remove checkpoint after successful completion.

    Args:
        db: SQLAlchemy session.
        execution_id: The execution key to remove.

    Returns:
        True on success, False on failure (logged, never raises).
    """
    try:
        db.execute(
            text("DELETE FROM execution_checkpoints WHERE execution_id = :eid"),
            {"eid": execution_id},
        )
        db.commit()
        return True
    except Exception as e:
        logger.warning("checkpoint clear failed for %s: %s", execution_id, e)
        try:
            db.rollback()
        except Exception:
            pass
        return False
