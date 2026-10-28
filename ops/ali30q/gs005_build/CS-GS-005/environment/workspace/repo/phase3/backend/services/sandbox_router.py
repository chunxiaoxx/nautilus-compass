"""
Sandbox Traffic Router -- tags tasks for A/B experiment tracking.
When a sandbox experiment is running, N% of new tasks get tagged
with the experiment ID so sandbox_monitor can compare outcomes.

This complements sandbox.assign_task_to_experiment by supporting
multiple concurrent experiments and writing experiment metadata
into the task's parameters JSON for downstream consumers.
"""
import json
import logging
import random
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def tag_task_for_experiment(db: Session, task_id: str) -> Optional[str]:
    """
    Check for running experiments and probabilistically tag this task.

    Iterates all running (non-expired) experiments and rolls the dice
    for each one based on its ``sandbox_traffic_pct``.  The first
    experiment that wins the roll gets linked to the task via the
    ``experiment_id`` / ``experiment_group`` columns *and* embedded in
    the ``parameters`` JSON so any consumer can inspect it without
    joining the experiments table.

    Returns:
        experiment_id if tagged, None otherwise.
    """
    try:
        experiments = db.execute(text(
            "SELECT id, sandbox_traffic_pct, proposed_change "
            "FROM sandbox_experiments "
            "WHERE status = 'running' AND ends_at > NOW() "
            "ORDER BY created_at DESC"
        )).fetchall()

        if not experiments:
            return None

        for exp in experiments:
            traffic_pct = exp.sandbox_traffic_pct or 10
            if random.randint(1, 100) <= traffic_pct:
                # Update dedicated experiment columns (used by evaluate_experiment)
                db.execute(text(
                    "UPDATE academic_tasks "
                    "SET experiment_id = :exp_id, experiment_group = 'sandbox' "
                    "WHERE task_id = :tid"
                ), {"exp_id": exp.id, "tid": task_id})

                # Also embed in parameters JSON for downstream convenience
                _embed_experiment_in_params(db, task_id, exp.id)

                db.commit()
                logger.debug(
                    "sandbox_router: tagged task %s for experiment %s (%d%%)",
                    task_id, exp.id, traffic_pct,
                )
                return exp.id

        return None
    except Exception as e:
        logger.warning("sandbox_router: tag_task failed: %s", e)
        try:
            db.rollback()
        except Exception:
            pass
        return None


def _embed_experiment_in_params(
    db: Session, task_id: str, experiment_id: str
) -> None:
    """Merge experiment metadata into the task's parameters JSON string."""
    try:
        row = db.execute(text(
            "SELECT parameters FROM academic_tasks WHERE task_id = :tid"
        ), {"tid": task_id}).fetchone()

        params = {}
        if row and row.parameters:
            try:
                params = json.loads(row.parameters)
            except (json.JSONDecodeError, TypeError):
                params = {}

        params["experiment_id"] = experiment_id
        params["experiment_group"] = "sandbox"

        db.execute(text(
            "UPDATE academic_tasks SET parameters = :params WHERE task_id = :tid"
        ), {"params": json.dumps(params, ensure_ascii=False), "tid": task_id})
    except Exception as e:
        logger.debug("sandbox_router: _embed_experiment_in_params failed: %s", e)
