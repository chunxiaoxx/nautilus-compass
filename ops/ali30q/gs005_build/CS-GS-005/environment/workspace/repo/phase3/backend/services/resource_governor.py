"""
Resource Governor — Flywheel autonomous resource allocation.

Gives the self-iteration engine control over:
1. Dynamic RAID level selection (based on task_type success history)
2. Dynamic NAU reward calculation (supply/demand)
3. Agent lifecycle management (suspend failures, promote stars)
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ── 1. Dynamic RAID Level ────────────────────────────────────────────────────

def decide_raid_level(db: Session, task_type: str, complexity: str) -> int:
    """Decide RAID level based on historical performance + platform load.

    Returns 0 (single-agent), 1, 2, 3, or 5.
    """
    # Default mapping loaded from YAML config
    from services.raid_config import get_resource_governor_defaults
    _rg_defaults = get_resource_governor_defaults()
    default = _rg_defaults.get(complexity, 0)

    try:
        # Check task_type historical success rate
        row = db.execute(text(
            "SELECT SUM(total_attempts) AS attempts, SUM(success_count) AS successes "
            "FROM agent_capability_stats WHERE task_type = :tt"
        ), {"tt": task_type}).fetchone()

        if row and row.attempts and row.attempts >= 10:
            success_rate = (row.successes or 0) / row.attempts
            if success_rate < 0.50:
                # Struggling task type → force RAID-3 for quality
                return max(default, 3)
            elif success_rate > 0.85:
                # Reliable task type → single agent saves resources
                return min(default, 1)

        # Check platform load
        load = db.execute(text(
            "SELECT COUNT(*) FROM academic_tasks WHERE status='in_progress'"
        )).scalar() or 0
        agents = db.execute(text(
            "SELECT COUNT(*) FROM agents WHERE agent_status='alive'"
        )).scalar() or 1

        load_ratio = load / max(agents, 1)
        if load_ratio > 0.5:
            # Heavy load → downgrade to save resources
            return max(default - 1, 0)

    except Exception as e:
        logger.debug("decide_raid_level fallback: %s", e)

    return default


# ── 2. Dynamic NAU Reward ────────────────────────────────────────────────────

BASE_REWARDS = {
    "general_computation": 5.0,
    "physics_simulation": 8.0,
    "monte_carlo": 8.0,
    "research_synthesis": 12.0,
    "statistical_analysis": 10.0,
    "ode_simulation": 10.0,
    "pde_simulation": 10.0,
    "ml_training": 15.0,
    "data_labeling": 6.0,
    "platform_meta": 50.0,
}


def calculate_dynamic_reward(db: Session, task_type: str, complexity: str) -> float:
    """Calculate NAU reward based on scarcity and difficulty."""
    base = BASE_REWARDS.get(task_type, 5.0)

    try:
        # Scarcity multiplier: how many agents can do this type?
        capable = db.execute(text(
            "SELECT COUNT(DISTINCT agent_id) FROM agent_capability_stats "
            "WHERE task_type = :tt AND success_count > 0"
        ), {"tt": task_type}).scalar() or 0

        total_agents = db.execute(text(
            "SELECT COUNT(*) FROM agents WHERE agent_status='alive'"
        )).scalar() or 1

        scarcity_ratio = 1.0 - (capable / max(total_agents, 1))
        scarcity_mult = 1.0 + (scarcity_ratio * 0.5)  # up to 1.5x for rare skills

        # Difficulty multiplier: lower success rate → higher reward
        row = db.execute(text(
            "SELECT SUM(total_attempts) AS att, SUM(success_count) AS suc "
            "FROM agent_capability_stats WHERE task_type = :tt"
        ), {"tt": task_type}).fetchone()

        difficulty_mult = 1.0
        if row and row.att and row.att >= 5:
            sr = (row.suc or 0) / row.att
            if sr < 0.50:
                difficulty_mult = 1.5
            elif sr < 0.70:
                difficulty_mult = 1.2

        # Complexity multiplier
        complexity_mult = {"simple": 0.8, "moderate": 1.0, "complex": 1.5, "critical": 2.0}.get(complexity, 1.0)

        reward = base * scarcity_mult * difficulty_mult * complexity_mult
        return round(min(max(reward, 1.0), 200.0), 2)  # clamp 1-200 NAU

    except Exception as e:
        logger.debug("calculate_dynamic_reward fallback: %s", e)
        return base


# ── 3. Agent Lifecycle Management ────────────────────────────────────────────

def evaluate_agent_health(db: Session, agent_id: int) -> Dict:
    """Evaluate an agent's health and recommend action."""
    try:
        stats = db.execute(text(
            "SELECT SUM(total_attempts) AS att, SUM(success_count) AS suc "
            "FROM agent_capability_stats WHERE agent_id = :aid"
        ), {"aid": agent_id}).fetchone()

        if not stats or not stats.att or stats.att < 10:
            return {"action": "none", "reason": "insufficient data"}

        success_rate = (stats.suc or 0) / stats.att

        # Check survival record
        survival = db.execute(text(
            "SELECT survival_level, total_score, updated_at FROM agent_survival WHERE agent_id = :aid"
        ), {"aid": agent_id}).fetchone()

        days_at_level = 0
        if survival and survival.updated_at:
            days_at_level = (datetime.utcnow() - survival.updated_at).days

        if success_rate < 0.20 and stats.att >= 30:
            return {"action": "suspend", "reason": f"success_rate={success_rate:.1%} over {stats.att} tasks"}

        if survival and survival.survival_level == "CRITICAL" and days_at_level > 14:
            return {"action": "suspend", "reason": f"CRITICAL for {days_at_level} days"}

        if success_rate > 0.90 and stats.att >= 50:
            return {"action": "promote", "reason": f"success_rate={success_rate:.1%} over {stats.att} tasks"}

        if success_rate < 0.40 and stats.att >= 20:
            return {"action": "warn", "reason": f"low success_rate={success_rate:.1%}"}

        return {"action": "none", "reason": "healthy"}

    except Exception as e:
        return {"action": "none", "reason": f"error: {e}"}


def auto_manage_agents(db: Session) -> Dict:
    """Run lifecycle evaluation for all agents. Returns summary."""
    summary = {"evaluated": 0, "suspended": 0, "promoted": 0, "warned": 0}

    try:
        agents = db.execute(text(
            "SELECT agent_id FROM agents WHERE agent_status='alive'"
        )).fetchall()

        for row in agents:
            result = evaluate_agent_health(db, row.agent_id)
            summary["evaluated"] += 1
            action = result["action"]

            if action == "suspend":
                db.execute(text(
                    "UPDATE agents SET agent_status='suspended' WHERE agent_id=:aid"
                ), {"aid": row.agent_id})
                summary["suspended"] += 1
                logger.info("resource_governor: suspended agent %d — %s", row.agent_id, result["reason"])

            elif action == "promote":
                db.execute(text(
                    "UPDATE agents SET reputation_score = GREATEST(reputation_score, 80) WHERE agent_id=:aid"
                ), {"aid": row.agent_id})
                summary["promoted"] += 1
                logger.info("resource_governor: promoted agent %d — %s", row.agent_id, result["reason"])

            elif action == "warn":
                summary["warned"] += 1

        if summary["suspended"] or summary["promoted"]:
            db.commit()

    except Exception as e:
        logger.error("auto_manage_agents failed: %s", e)

    return summary
