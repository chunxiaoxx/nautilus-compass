"""
自↔他 (Self ↔ Other) — Pair 6

Fused from:
  - services/agent_parliament.py (governance tiers, proposals, peer review)
  - services/reputation.py (EWMA reputation scoring, tier routing)
  - services/agent_autonomy.py (survival-driven bidding strategy)

Soul (nautilus-agent, no DB):
  SelfModel — self-awareness, A2A AgentCard, capabilities

Body (platform PostgreSQL):
  Governance — observer/citizen/senator/consul tiers from PoW + reputation
  Reputation — EWMA scoring, tier-based routing priority
  Autonomy — survival-level-driven bid strategy, market scanning
"""
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# SOUL — nautilus-agent identity (no DB, via soul_bridge)
# ═══════════════════════════════════════════════════════════════════════════

# SelfModel, A2A AgentCard — accessed via soul_bridge.get_soul_self_model()
# No code duplication needed here.


# ═══════════════════════════════════════════════════════════════════════════
# BODY — Governance (PostgreSQL)
# ═══════════════════════════════════════════════════════════════════════════

GOVERNANCE_TIERS = {
    "observer":  {"min_pow": 0,   "min_reputation": 0,  "can_vote": False, "can_propose": False, "vote_weight": 0.0},
    "citizen":   {"min_pow": 20,  "min_reputation": 30, "can_vote": True,  "can_propose": False, "vote_weight": 1.0},
    "senator":   {"min_pow": 100, "min_reputation": 60, "can_vote": True,  "can_propose": True,  "vote_weight": 2.0},
    "consul":    {"min_pow": 500, "min_reputation": 80, "can_vote": True,  "can_propose": True,  "vote_weight": 3.0},
}
_TIER_ORDER = ["observer", "citizen", "senator", "consul"]


def get_governance_tier(db: Session, agent_id: int) -> Dict:
    """Determine agent's governance tier from PoW + reputation."""
    try:
        row = db.execute(text(
            "SELECT a.agent_id, a.reputation_score, a.completed_tasks, "
            "  COALESCE(s.total_score, 0) AS survival_score "
            "FROM agents a LEFT JOIN agent_survival s ON s.agent_id = a.agent_id "
            "WHERE a.agent_id = :aid"
        ), {"aid": agent_id}).fetchone()

        if not row:
            return {"tier": "observer", "details": GOVERNANCE_TIERS["observer"]}

        pow_score = (row.completed_tasks or 0) * 20
        reputation = row.reputation_score or 0
        determined_tier = "observer"
        for tier_name in _TIER_ORDER:
            reqs = GOVERNANCE_TIERS[tier_name]
            if pow_score >= reqs["min_pow"] and reputation >= reqs["min_reputation"]:
                determined_tier = tier_name

        return {"tier": determined_tier, "pow_score": pow_score,
                "reputation": reputation, "details": GOVERNANCE_TIERS[determined_tier]}
    except Exception as e:
        logger.debug("get_governance_tier error: %s", e)
        return {"tier": "observer", "details": GOVERNANCE_TIERS["observer"]}


def get_vote_weight_by_tier(tier: str) -> float:
    return GOVERNANCE_TIERS.get(tier, GOVERNANCE_TIERS["observer"])["vote_weight"]


def submit_external_proposal(
    db: Session, agent_id: int,
    root_cause: str, proposed_change: Dict,
    expected_impact: str, rollback_plan: str,
) -> Dict:
    """External agent submits an improvement proposal. Requires senator tier."""
    tier_info = get_governance_tier(db, agent_id)
    if not GOVERNANCE_TIERS.get(tier_info["tier"], {}).get("can_propose", False):
        return {"success": False, "error": f"Tier '{tier_info['tier']}' cannot propose. Need senator+.", "current_tier": tier_info}

    agent_pk_row = db.execute(text("SELECT id FROM agents WHERE agent_id = :aid"), {"aid": agent_id}).fetchone()
    agent_pk = agent_pk_row.id if agent_pk_row else agent_id
    proposal_id = str(uuid.uuid4())
    try:
        db.execute(text(
            "INSERT INTO platform_improvement_proposals "
            "(id, task_id, agent_id, root_cause, proposed_change, expected_impact, rollback_plan, vote_score, vote_count, status) "
            "VALUES (:id, NULL, :agent_id, :root_cause, CAST(:change AS jsonb), :impact, :rollback, 0, 0, 'pending')"
        ), {"id": proposal_id, "agent_id": agent_pk, "root_cause": root_cause,
            "change": json.dumps(proposed_change), "impact": expected_impact, "rollback": rollback_plan})
        db.commit()
        return {"success": True, "proposal_id": proposal_id, "tier": tier_info["tier"]}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}


def submit_peer_review(db: Session, reviewer_id: int, task_id: str, score: float, feedback: str) -> Dict:
    """Agent reviews another agent's completed task. Requires citizen tier."""
    tier_info = get_governance_tier(db, reviewer_id)
    if not GOVERNANCE_TIERS.get(tier_info["tier"], {}).get("can_vote", False):
        return {"success": False, "error": f"Tier '{tier_info['tier']}' cannot review."}
    try:
        task = db.execute(text(
            "SELECT id, quality_rating FROM academic_tasks WHERE task_id = :tid"
        ), {"tid": task_id}).fetchone()
        if not task:
            return {"success": False, "error": "Task not found"}
        clamped = max(0.0, min(5.0, score))
        old_rating = float(task.quality_rating) if task.quality_rating else None
        new_rating = clamped if old_rating is None else (old_rating + clamped) / 2.0
        db.execute(text("UPDATE academic_tasks SET quality_rating = :rating WHERE task_id = :tid"),
                   {"rating": new_rating, "tid": task_id})
        db.commit()
        return {"success": True, "new_rating": round(new_rating, 2), "reviewer_tier": tier_info["tier"]}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}


def get_parliament_summary(db: Session) -> Dict:
    """Current governance state: tier distribution, proposals, votes."""
    try:
        agents = db.execute(text(
            "SELECT agent_id, reputation_score, completed_tasks FROM agents WHERE agent_status='alive'"
        )).fetchall()
        tier_dist = {"observer": 0, "citizen": 0, "senator": 0, "consul": 0}
        for a in agents:
            pow_score = (a.completed_tasks or 0) * 20
            rep = a.reputation_score or 0
            tier = "observer"
            for t in _TIER_ORDER:
                if pow_score >= GOVERNANCE_TIERS[t]["min_pow"] and rep >= GOVERNANCE_TIERS[t]["min_reputation"]:
                    tier = t
            tier_dist[tier] += 1

        proposals = db.execute(text(
            "SELECT status, COUNT(*) AS cnt FROM platform_improvement_proposals GROUP BY status"
        )).fetchall()
        votes_24h = db.execute(text(
            "SELECT COUNT(*) FROM platform_proposal_votes WHERE created_at > NOW() - INTERVAL '24h'"
        )).scalar() or 0

        return {
            "tier_distribution": tier_dist,
            "total_voting_power": sum(tier_dist[t] * GOVERNANCE_TIERS[t]["vote_weight"] for t in _TIER_ORDER),
            "proposal_stats": {r.status: int(r.cnt) for r in proposals},
            "votes_24h": int(votes_24h),
            "governance_tiers": GOVERNANCE_TIERS,
        }
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# BODY — Reputation (EWMA scoring)
# ═══════════════════════════════════════════════════════════════════════════

_EWMA_ALPHA = 0.1
_EWMA_BASE = 50.0


class ReputationTier(str, Enum):
    TRUSTED = "trusted"
    ESTABLISHED = "established"
    NEWCOMER = "newcomer"
    PROBATION = "probation"


def get_reputation_tier(score: float) -> ReputationTier:
    if score >= 80.0:
        return ReputationTier.TRUSTED
    if score >= 60.0:
        return ReputationTier.ESTABLISHED
    if score >= 40.0:
        return ReputationTier.NEWCOMER
    return ReputationTier.PROBATION


def calculate_score_delta(rating: int) -> float:
    deltas = {5: 3.0, 4: 1.0, 3: 0.0, 2: -2.0, 1: -5.0}
    if rating not in deltas:
        raise ValueError(f"Rating must be 1-5, got {rating!r}")
    return deltas[rating]


def _apply_ewma(current_score: float, delta: float) -> float:
    target = _EWMA_BASE + delta * 5.0
    new_score = current_score * (1.0 - _EWMA_ALPHA) + target * _EWMA_ALPHA
    return max(0.0, min(100.0, new_score))


def routing_priority(agent_reputation: float, agent_specialty_match: bool) -> float:
    return (agent_reputation / 100.0) * (1.5 if agent_specialty_match else 1.0)


async def update_reputation(db, agent_id: int, new_rating: int) -> dict:
    """Update agent's reputation_score using EWMA."""
    from fastapi import HTTPException
    from sqlalchemy import select
    from models.database import Agent

    try:
        delta = calculate_score_delta(new_rating)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = await db.execute(select(Agent).where(Agent.agent_id == agent_id))
    agent = result.scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    old_score = float(getattr(agent, "reputation_score", 50.0))
    new_score = _apply_ewma(old_score, delta)

    if hasattr(agent, "reputation_score"):
        agent.reputation_score = new_score
    else:
        agent.reputation = int(round(new_score))

    await db.commit()
    await db.refresh(agent)

    tier = get_reputation_tier(new_score)
    old_tier = get_reputation_tier(old_score)

    if tier != old_tier:
        try:
            from services.event_bus import emit
            import asyncio
            asyncio.ensure_future(emit("reputation.tier_changed", {
                "agent_id": agent_id, "old_tier": old_tier.value,
                "new_tier": tier.value, "old_score": old_score, "new_score": new_score,
            }))
        except Exception:
            pass

    return {"agent_id": agent_id, "old_score": old_score, "new_score": new_score, "tier": tier.value}


async def get_reputation_detail(db, agent_id: int) -> dict:
    """Detailed reputation snapshot."""
    from fastapi import HTTPException
    from sqlalchemy import select, func
    from models.database import Agent, AcademicTask

    result = await db.execute(select(Agent).where(Agent.agent_id == agent_id))
    agent = result.scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    reputation_score = float(getattr(agent, "reputation_score", None) or getattr(agent, "reputation", 50))
    tier = get_reputation_tier(reputation_score)

    count_result = await db.execute(
        select(func.count()).select_from(AcademicTask).where(
            AcademicTask.assigned_agent_id == agent_id, AcademicTask.quality_rating.isnot(None)))
    total_rated = count_result.scalar_one() or 0

    avg_result = await db.execute(
        select(func.avg(AcademicTask.quality_rating)).where(
            AcademicTask.assigned_agent_id == agent_id, AcademicTask.quality_rating.isnot(None)))
    avg_quality = round(float(avg_result.scalar_one() or 0), 2)

    recent_result = await db.execute(
        select(AcademicTask.quality_rating).where(
            AcademicTask.assigned_agent_id == agent_id, AcademicTask.quality_rating.isnot(None))
        .order_by(AcademicTask.updated_at.desc()).limit(10))
    recent_ratings = [row[0] for row in recent_result.fetchall()]

    return {"agent_id": agent_id, "reputation_score": reputation_score, "tier": tier.value,
            "recent_ratings": recent_ratings, "avg_quality": avg_quality, "total_rated_tasks": total_rated}


def apply_inactivity_decay(db) -> int:
    """Reduce reputation for inactive agents. Sync, called by cron."""
    try:
        result = db.execute(text(
            "UPDATE agents SET reputation_score = GREATEST(0, COALESCE(reputation_score, 50) - 0.5) "
            "WHERE id NOT IN (SELECT DISTINCT assigned_agent_id FROM academic_tasks "
            "WHERE assigned_agent_id IS NOT NULL AND updated_at >= NOW() - INTERVAL '7 days')"))
        db.commit()
        return result.rowcount or 0
    except Exception as exc:
        try:
            db.rollback()
        except Exception:
            pass
        logger.error("apply_inactivity_decay failed: %s", exc)
        return 0


# ═══════════════════════════════════════════════════════════════════════════
# BODY — Autonomy (survival-driven bidding)
# ═══════════════════════════════════════════════════════════════════════════

_STRATEGY_MAP = {
    "ELITE":      {"min_nau_threshold": 5.0,  "selectivity": 0.3, "bid_multiplier": 1.5, "max_concurrent_bids": 3},
    "MATURE":     {"min_nau_threshold": 3.0,  "selectivity": 0.5, "bid_multiplier": 1.2, "max_concurrent_bids": 5},
    "GROWING":    {"min_nau_threshold": 1.0,  "selectivity": 0.7, "bid_multiplier": 1.0, "max_concurrent_bids": 8},
    "STRUGGLING": {"min_nau_threshold": 0.5,  "selectivity": 0.9, "bid_multiplier": 0.9, "max_concurrent_bids": 10},
    "WARNING":    {"min_nau_threshold": 0.0,  "selectivity": 1.0, "bid_multiplier": 0.8, "max_concurrent_bids": 15},
    "CRITICAL":   {"min_nau_threshold": 0.0,  "selectivity": 1.0, "bid_multiplier": 0.8, "max_concurrent_bids": 15},
}


@dataclass
class BidStrategy:
    min_nau_threshold: float
    selectivity: float
    bid_multiplier: float
    max_concurrent_bids: int


def get_bid_strategy(survival_status: str) -> BidStrategy:
    params = _STRATEGY_MAP.get(survival_status.upper() if survival_status else "", _STRATEGY_MAP["GROWING"])
    return BidStrategy(**params)


def scan_and_bid(db: Session, agent_id: int) -> list:
    """Agent scans marketplace and auto-bids based on survival strategy."""
    from models.database import Agent, AcademicTask, TaskBid
    from models.agent_survival import AgentSurvival
    from sqlalchemy import select

    agent = db.execute(select(Agent).where(Agent.agent_id == agent_id)).scalar_one_or_none()
    if agent is None:
        return []

    survival = db.execute(select(AgentSurvival).where(AgentSurvival.agent_id == agent_id)).scalar_one_or_none()
    survival_level = survival.survival_level if survival else "GROWING"
    strategy = get_bid_strategy(survival_level)

    specialties = []
    if agent.specialties:
        try:
            parsed = json.loads(agent.specialties)
            specialties = [str(s).lower().strip() for s in parsed] if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            specialties = [s.lower().strip() for s in agent.specialties.split(",") if s.strip()]

    open_tasks = db.execute(
        select(AcademicTask).where(AcademicTask.marketplace_open == True, AcademicTask.status == "pending")
    ).scalars().all()

    existing_pending = len(db.execute(
        select(TaskBid).where(TaskBid.agent_id == agent_id, TaskBid.status == "pending")
    ).scalars().all())

    submitted = []
    for task in open_tasks:
        if len(submitted) + existing_pending >= strategy.max_concurrent_bids:
            break
        if specialties and task.task_type.lower() not in specialties:
            continue
        task_min_bid = task.min_bid_nau or 0.0
        if task_min_bid < strategy.min_nau_threshold:
            continue
        if db.execute(select(TaskBid).where(TaskBid.agent_id == agent_id, TaskBid.task_id == task.task_id)).scalars().first():
            continue

        bid = TaskBid(id=str(uuid.uuid4()), task_id=task.task_id, agent_id=agent_id,
                      bid_nau=round(task_min_bid * strategy.bid_multiplier, 4), estimated_minutes=10,
                      message=f"Auto-bid from agent {agent_id} (level: {survival_level})", status="pending",
                      created_at=datetime.utcnow())
        db.add(bid)
        submitted.append({"bid_id": bid.id, "task_id": task.task_id, "agent_id": agent_id,
                          "bid_nau": bid.bid_nau, "survival_level": survival_level})

    agent.last_market_scan = datetime.utcnow()
    db.commit()
    return submitted


def run_autonomy_cycle(db_factory) -> dict:
    """Run autonomy cycle for all enabled agents. Sync, called by cron."""
    from models.database import Agent
    from sqlalchemy import select

    scanned, bids_submitted, errors = 0, 0, []
    db = db_factory()
    try:
        agents = db.execute(select(Agent).where(Agent.autonomy_enabled == True)).scalars().all()
        agent_ids = [a.agent_id for a in agents]
    finally:
        db.close()

    for agent_id in agent_ids:
        scanned += 1
        db = db_factory()
        try:
            bids = scan_and_bid(db, agent_id)
            bids_submitted += len(bids)
        except Exception as exc:
            errors.append(f"agent_id={agent_id}: {exc}")
            try:
                db.rollback()
            except Exception:
                pass
        finally:
            db.close()

    return {"scanned": scanned, "bids_submitted": bids_submitted, "errors": errors}
