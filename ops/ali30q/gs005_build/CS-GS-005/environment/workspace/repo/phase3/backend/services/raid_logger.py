"""
RAID Execution Logger — records config + outcome for Meta-Harness optimization.
"""
import hashlib
import json
import logging
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def log_raid_execution(
    db: Session,
    task_id: str,
    task_type: str,
    raid_level: int,
    config: Dict[str, Any],
    success: bool,
    quality_score: Optional[float] = None,
    consensus_score: Optional[float] = None,
    execution_time_ms: Optional[int] = None,
    cost_nau: Optional[float] = None,
) -> bool:
    """Log a RAID execution for later optimization."""
    try:
        config_str = json.dumps(config, sort_keys=True)
        config_hash = hashlib.sha256(config_str.encode()).hexdigest()[:16]

        db.execute(text(
            "INSERT INTO raid_execution_log "
            "(task_id, task_type, raid_level, agent_count, parallel, "
            "feedback_rounds, judge_enabled, consensus_threshold, model_tier, "
            "success, quality_score, consensus_score, execution_time_ms, cost_nau, config_hash) "
            "VALUES (:tid, :ttype, :level, :agents, :parallel, "
            ":rounds, :judge, :threshold, :model, "
            ":success, :quality, :consensus, :time_ms, :cost, :hash)"
        ), {
            "tid": task_id,
            "ttype": task_type,
            "level": raid_level,
            "agents": config.get("agent_count"),
            "parallel": config.get("parallel", True),
            "rounds": config.get("feedback_rounds", 0),
            "judge": config.get("judge_enabled", True),
            "threshold": config.get("consensus_threshold"),
            "model": config.get("model_tier"),
            "success": success,
            "quality": quality_score,
            "consensus": consensus_score,
            "time_ms": execution_time_ms,
            "cost": cost_nau,
            "hash": config_hash,
        })
        db.commit()
        logger.debug(
            "raid_logger: logged execution for %s (level=%d, success=%s)",
            task_id, raid_level, success,
        )
        return True
    except Exception as e:
        logger.warning("raid_logger: failed to log: %s", e)
        try:
            db.rollback()
        except Exception:
            pass
        return False
