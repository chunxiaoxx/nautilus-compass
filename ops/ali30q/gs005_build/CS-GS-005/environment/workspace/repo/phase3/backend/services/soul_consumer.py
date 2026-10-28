"""Soul consumer · closes the agent→soul loop (proposal 1).

Agents write code-change proposals to `platform_proposals` (status='pending').
Soul had no consumer → dead letter. This polls pending proposals, runs each
through Soul (dry-run → pr_gate → draft PR), and writes back resolution_note +
status so the proposing agent learns the outcome.

NEVER auto-merges. Draft PR + human review is the gate. Runs against a clean
origin-synced workspace (NOT the diverged ~/nautilus-mvp).
"""
from __future__ import annotations
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Callable, Optional

logger = logging.getLogger(__name__)


def consume_pending_proposals(
    db,
    base_dir: str,
    limit: int = 5,
    _ship_fn: Optional[Callable] = None,
) -> list:
    """Process pending platform_proposals. Returns list of per-proposal outcomes."""
    from sqlalchemy import text
    if _ship_fn is None:
        from services.soul_service import ship_to_draft_pr as _ship_fn

    rows = db.execute(text(
        "SELECT proposal_id, proposed_change, change_type FROM platform_proposals "
        "WHERE status = 'pending' ORDER BY created_at ASC LIMIT :lim"
    ), {"lim": limit}).fetchall()

    results = []
    for row in rows:
        proposal_id = row[0]
        task = row[1] or ""
        cycle_id = f"soul-{proposal_id}"
        outcome = _ship_fn(
            task, base_dir,
            branch=f"soul/{proposal_id}",
            commit_msg=f"soul: proposal {proposal_id}"[:80],
            cycle_id=cycle_id,
        )
        if outcome.get("success"):
            note = f"Soul shipped DRAFT PR (human review required): {outcome.get('pr_url')}"
        else:
            note = f"Soul dry-run rejected at stage '{outcome.get('stage')}': {outcome.get('detail')}"
        # Both cases = reviewed (proposal got a verdict); only success has a PR
        db.execute(text(
            "UPDATE platform_proposals SET resolution_note = :note, status = 'reviewed', "
            "resolved_at = :ts, resolved_by = 'soul' WHERE proposal_id = :pid"
        ), {"note": str(note)[:2000], "ts": datetime.now(timezone.utc), "pid": proposal_id})
        db.commit()
        results.append({
            "proposal_id": proposal_id,
            "shipped": bool(outcome.get("success")),
            "pr_url": outcome.get("pr_url"),
            "note": note,
        })
    return results


# Systemd entrypoint ---------------------------------------------------------
# Invoked as `python -m services.soul_consumer` by nautilus-soul-consumer.timer
# (2026-09-10 activation). Reads SOUL_BASE_DIR from env (fail loud if missing);
# opens a session via utils.database.SessionLocal; drains up to `limit` pending
# proposals; exits 0 even on partial failure so the timer keeps cadence.
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
        outcomes = consume_pending_proposals(db, base_dir=base_dir, limit=5)
        logger.info(
            "soul_consumer cycle complete: %d proposals processed",
            len(outcomes),
        )
        for o in outcomes:
            logger.info(
                "proposal=%s shipped=%s pr=%s",
                o.get("proposal_id"), o.get("shipped"), o.get("pr_url"),
            )
    except Exception as exc:  # noqa: BLE001 — timer must not crash
        logger.exception("soul_consumer cycle failed: %s", exc)
    finally:
        try:
            db.close()
        except Exception:  # noqa: BLE001
            pass

    sys.exit(0)
