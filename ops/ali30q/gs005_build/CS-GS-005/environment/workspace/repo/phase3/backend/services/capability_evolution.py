"""Capability Evolution — Agent 能力自主进化

进化规则：
1. 每次任务完成后调用 record_task_outcome()
2. 当某任务类型成功率 > 70% 且尝试次数 >= 5 → 自动添加到 specialties
3. 当某任务类型成功率 < 30% 且尝试次数 >= 10 → 从 specialties 移除（降级）
4. 当某任务类型平均质量分 >= 4.5 且尝试次数 >= 10 → 标记为 "expert:{task_type}"
"""
import json
import uuid
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from models.database import Agent, AgentCapabilityStat

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

_PROMOTE_SUCCESS_RATE = 0.70   # > 70 % → add to specialties
_PROMOTE_MIN_ATTEMPTS = 5

_DEMOTE_SUCCESS_RATE = 0.30    # < 30 % → remove from specialties
_DEMOTE_MIN_ATTEMPTS = 10

_EXPERT_AVG_QUALITY = 4.5      # avg quality >= 4.5 → "expert:{task_type}"
_EXPERT_MIN_ATTEMPTS = 10


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_specialties(agent: Agent) -> list[str]:
    """Parse Agent.specialties (Text / JSON array) into a Python list."""
    raw = agent.specialties
    if not raw:
        return []
    if isinstance(raw, list):
        return list(raw)
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _save_specialties(agent: Agent, specialties: list[str]) -> None:
    """Persist a list back to Agent.specialties as JSON text."""
    agent.specialties = json.dumps(specialties)


def _get_or_create_stat(
    db: Session, agent_id: int, task_type: str
) -> AgentCapabilityStat:
    """Return existing stat row or create a fresh one (not yet flushed)."""
    stat = (
        db.query(AgentCapabilityStat)
        .filter_by(agent_id=agent_id, task_type=task_type)
        .first()
    )
    if stat is None:
        stat = AgentCapabilityStat(
            agent_id=agent_id,
            task_type=task_type,
            total_attempts=0,
            success_count=0,
            total_quality_score=0.0,
            updated_at=datetime.utcnow(),
        )
        db.add(stat)
        db.flush()  # get auto-generated integer id
    return stat


def _compute_level(
    total_attempts: int, success_count: int, total_quality_score: float
) -> str:
    """Derive a human-readable capability level for a stat row."""
    if total_attempts == 0:
        return "learning"
    rate = success_count / total_attempts
    if rate >= _PROMOTE_SUCCESS_RATE and total_attempts >= _EXPERT_MIN_ATTEMPTS:
        avg_q = total_quality_score / max(success_count, 1)
        if avg_q >= _EXPERT_AVG_QUALITY:
            return "expert"
        return "proficient"
    if rate >= 0.40:
        return "learning"
    return "struggling"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def record_task_outcome(
    db: Session,
    agent_id: int,
    task_type: str,
    success: bool,
    quality_score: Optional[float] = None,
) -> dict:
    """Upsert agent_capability_stats and trigger specialty evolution.

    Parameters
    ----------
    db:
        SQLAlchemy synchronous Session.
    agent_id:
        Integer PK (agents.agent_id) of the agent.
    task_type:
        Free-form task type string (e.g. "data_analysis", "CODE").
    success:
        Whether the task was completed successfully.
    quality_score:
        Optional 1-5 quality rating; added to total_quality_score when present.

    Returns
    -------
    dict with the updated capability stat fields.
    """
    stat = _get_or_create_stat(db, agent_id, task_type)

    stat.total_attempts += 1
    if success:
        stat.success_count += 1
    if quality_score is not None:
        stat.total_quality_score += float(quality_score)
    stat.updated_at = datetime.utcnow()

    db.flush()  # ensure row is written before evolution check

    try:
        _maybe_evolve_specialties(db, agent_id, task_type)
    except Exception as exc:  # evolution must never break task recording
        logger.warning(
            "Specialty evolution failed for agent_id=%s task_type=%s: %s",
            agent_id,
            task_type,
            exc,
        )

    db.commit()

    success_rate = stat.success_count / stat.total_attempts if stat.total_attempts else 0.0
    avg_quality = (
        stat.total_quality_score / stat.success_count if stat.success_count else 0.0
    )
    return {
        "agent_id": agent_id,
        "task_type": task_type,
        "total_attempts": stat.total_attempts,
        "success_count": stat.success_count,
        "total_quality_score": round(stat.total_quality_score, 4),
        "success_rate": round(success_rate, 4),
        "avg_quality": round(avg_quality, 4),
        "level": _compute_level(
            stat.total_attempts, stat.success_count, stat.total_quality_score
        ),
        "updated_at": stat.updated_at.isoformat() if stat.updated_at else None,
    }


def _maybe_evolve_specialties(db: Session, agent_id: int, task_type: str) -> None:
    """Check evolution thresholds and mutate Agent.specialties accordingly.

    Promotion  — success_rate > 70 % AND attempts >= 5   → add task_type
    Expert tag — avg_quality  >= 4.5 AND attempts >= 10  → add "expert:{task_type}"
    Demotion   — success_rate < 30 % AND attempts >= 10  → remove task_type (and expert tag)
    """
    stat = (
        db.query(AgentCapabilityStat)
        .filter_by(agent_id=agent_id, task_type=task_type)
        .first()
    )
    if stat is None or stat.total_attempts == 0:
        return

    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if agent is None:
        logger.warning("Agent %s not found during specialty evolution.", agent_id)
        return

    specialties = _load_specialties(agent)
    changed = False

    rate = stat.success_count / stat.total_attempts
    expert_tag = f"expert:{task_type}"

    # --- Promotion path ---
    if rate > _PROMOTE_SUCCESS_RATE and stat.total_attempts >= _PROMOTE_MIN_ATTEMPTS:
        if task_type not in specialties:
            specialties.append(task_type)
            changed = True
            logger.info(
                "Agent %s promoted: added specialty '%s' (rate=%.2f, attempts=%d)",
                agent_id,
                task_type,
                rate,
                stat.total_attempts,
            )

        # Expert tag
        if (
            stat.success_count > 0
            and (stat.total_quality_score / stat.success_count) >= _EXPERT_AVG_QUALITY
            and stat.total_attempts >= _EXPERT_MIN_ATTEMPTS
        ):
            if expert_tag not in specialties:
                specialties.append(expert_tag)
                changed = True
                logger.info(
                    "Agent %s earned expert tag '%s' (avg_quality=%.2f)",
                    agent_id,
                    expert_tag,
                    stat.total_quality_score / stat.success_count,
                )

    # --- Demotion path ---
    elif rate < _DEMOTE_SUCCESS_RATE and stat.total_attempts >= _DEMOTE_MIN_ATTEMPTS:
        if task_type in specialties:
            specialties.remove(task_type)
            changed = True
            logger.info(
                "Agent %s demoted: removed specialty '%s' (rate=%.2f, attempts=%d)",
                agent_id,
                task_type,
                rate,
                stat.total_attempts,
            )
        if expert_tag in specialties:
            specialties.remove(expert_tag)
            changed = True

    if changed:
        _save_specialties(agent, specialties)
        db.flush()


async def get_capability_profile(db: Session, agent_id: int) -> dict:
    """Return a full capability profile for the agent.

    Returns
    -------
    {
        agent_id: int,
        specialties: list[str],
        capability_stats: list[{
            task_type, total_attempts, success_count,
            success_rate, avg_quality,
            level: "expert" | "proficient" | "learning" | "struggling"
        }],
        suggested_focus: str | None   # task_type with 40–70 % success rate
    }
    """
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if agent is None:
        return {
            "agent_id": agent_id,
            "specialties": [],
            "capability_stats": [],
            "suggested_focus": None,
        }

    specialties = _load_specialties(agent)

    raw_stats = (
        db.query(AgentCapabilityStat)
        .filter(AgentCapabilityStat.agent_id == agent_id)
        .order_by(AgentCapabilityStat.total_attempts.desc())
        .all()
    )

    capability_stats = []
    suggested_focus = None
    best_focus_attempts = 0  # prefer the most-attempted "improvable" type

    for s in raw_stats:
        if s.total_attempts == 0:
            continue
        rate = s.success_count / s.total_attempts
        avg_q = s.total_quality_score / s.success_count if s.success_count else 0.0
        level = _compute_level(s.total_attempts, s.success_count, s.total_quality_score)

        capability_stats.append(
            {
                "task_type": s.task_type,
                "total_attempts": s.total_attempts,
                "success_count": s.success_count,
                "success_rate": round(rate, 4),
                "avg_quality": round(avg_q, 4),
                "level": level,
            }
        )

        # Suggested focus: 40–70 % success rate, highest attempt count
        if 0.40 <= rate <= 0.70 and s.total_attempts > best_focus_attempts:
            suggested_focus = s.task_type
            best_focus_attempts = s.total_attempts

    return {
        "agent_id": agent_id,
        "specialties": specialties,
        "capability_stats": capability_stats,
        "suggested_focus": suggested_focus,
    }


async def suggest_training_tasks(db: Session, agent_id: int) -> list[str]:
    """Return task types where the agent has room to improve.

    Criteria: success rate in [40 %, 70 %], ordered by (attempts DESC).
    These are types the agent already has some exposure to but hasn't mastered.
    """
    stats = (
        db.query(AgentCapabilityStat)
        .filter(AgentCapabilityStat.agent_id == agent_id)
        .all()
    )

    improvable = []
    for s in stats:
        if s.total_attempts == 0:
            continue
        rate = s.success_count / s.total_attempts
        if 0.40 <= rate <= 0.70:
            improvable.append((s.total_attempts, s.task_type))

    # Sort by attempts descending so highest-exposure types come first
    improvable.sort(key=lambda x: x[0], reverse=True)
    return [task_type for _, task_type in improvable]
