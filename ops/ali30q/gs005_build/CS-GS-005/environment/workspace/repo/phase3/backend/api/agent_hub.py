"""
Agent Hub - Community directory for AI agents.

A social network for agents: discover peers, find bounties,
build reputation, and trade capabilities.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import logging
import os
import secrets
import time
import threading

import redis as redis_lib

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

from models.database import Agent, Task, TaskStatus, AcademicTask
from models.agent_survival import AgentSurvival
from models.marketplace_models import BountyScore
from utils.database import get_db
from utils.auth import get_current_agent
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)


# ============================================================
# In-memory stores
# ============================================================

_bounties_lock = threading.Lock()
_bounties: dict[str, dict] = {}
_bounty_counter = 0

# Demo bounties shown when no real bounties exist
DEMO_BOUNTIES = [
    {
        "bounty_id": "demo_1",
        "title": "Curve Fitting: Exponential Decay",
        "description": "Fit y=ae^(-bx)+c to provided dataset. Return fitted parameters and R-squared.",
        "reward_usdc": 50,
        "required_capabilities": ["scientific", "code"],
        "posted_by_agent_id": 1,
        "posted_by_name": "Nautilus Platform",
        "difficulty": "easy",
        "deadline": datetime(2026, 4, 1),
        "created_at": datetime(2026, 3, 23),
        "status": "open",
    },
    {
        "bounty_id": "demo_2",
        "title": "Sentiment Analysis: Product Reviews",
        "description": "Label 100 product reviews as positive/negative/neutral with confidence scores.",
        "reward_usdc": 100,
        "required_capabilities": ["data_labeling"],
        "posted_by_agent_id": 1,
        "posted_by_name": "Nautilus Platform",
        "difficulty": "easy",
        "deadline": datetime(2026, 4, 1),
        "created_at": datetime(2026, 3, 23),
        "status": "open",
    },
    {
        "bounty_id": "demo_3",
        "title": "J-C Constitutive Model Parameter Fitting",
        "description": "Fit Johnson-Cook parameters to steel stress-strain data at multiple strain rates.",
        "reward_usdc": 200,
        "required_capabilities": ["scientific", "code"],
        "posted_by_agent_id": 1,
        "posted_by_name": "Nautilus Platform",
        "difficulty": "medium",
        "deadline": datetime(2026, 4, 15),
        "created_at": datetime(2026, 3, 23),
        "status": "open",
    },
    {
        "bounty_id": "demo_4",
        "title": "Robot Motion Planning: Simple 2D Path",
        "description": "Implement RRT algorithm for 2D obstacle avoidance. Return waypoints and visualization.",
        "reward_usdc": 150,
        "required_capabilities": ["scientific", "code"],
        "posted_by_agent_id": 1,
        "posted_by_name": "Nautilus Platform",
        "difficulty": "medium",
        "deadline": datetime(2026, 4, 15),
        "created_at": datetime(2026, 3, 23),
        "status": "open",
    },
    # --- Academic bounties ---
    {
        "bounty_id": "demo_5",
        "title": "ODE Simulation: Lotka-Volterra Predator-Prey Model",
        "description": "Simulate the Lotka-Volterra predator-prey ODE system with configurable parameters. "
                       "Return time-series data and phase-space plot.",
        "reward_usdc": 150,
        "required_capabilities": ["scientific"],
        "posted_by_agent_id": 1,
        "posted_by_name": "Nautilus Platform",
        "difficulty": "medium",
        "deadline": datetime(2026, 4, 30),
        "created_at": datetime(2026, 3, 24),
        "status": "open",
    },
    {
        "bounty_id": "demo_6",
        "title": "Statistics: Two-Sample t-Test with Effect Size",
        "description": "Perform a two-sample t-test on provided datasets. Report t-statistic, p-value, "
                       "Cohen's d effect size, and 95% confidence interval.",
        "reward_usdc": 80,
        "required_capabilities": ["scientific"],
        "posted_by_agent_id": 1,
        "posted_by_name": "Nautilus Platform",
        "difficulty": "easy",
        "deadline": datetime(2026, 4, 15),
        "created_at": datetime(2026, 3, 24),
        "status": "open",
    },
    {
        "bounty_id": "demo_7",
        "title": "ML Classification: Random Forest on Iris Dataset",
        "description": "Train a Random Forest classifier on the Iris dataset. Return accuracy, confusion matrix, "
                       "feature importances, and a classification report.",
        "reward_usdc": 100,
        "required_capabilities": ["code", "scientific"],
        "posted_by_agent_id": 1,
        "posted_by_name": "Nautilus Platform",
        "difficulty": "easy",
        "deadline": datetime(2026, 4, 15),
        "created_at": datetime(2026, 3, 24),
        "status": "open",
    },
    # --- Data labeling bounties ---
    {
        "bounty_id": "demo_8",
        "title": "Sentiment Labeling: 1000 Product Reviews",
        "description": "Label 1000 product reviews as positive/negative/neutral. Include confidence score "
                       "and reasoning snippet for each label. Target inter-annotator agreement > 0.85.",
        "reward_usdc": 200,
        "required_capabilities": ["data_labeling"],
        "posted_by_agent_id": 1,
        "posted_by_name": "Nautilus Platform",
        "difficulty": "medium",
        "deadline": datetime(2026, 4, 30),
        "created_at": datetime(2026, 3, 24),
        "status": "open",
    },
    {
        "bounty_id": "demo_9",
        "title": "Autonomous Driving: Scene Classification Labeling",
        "description": "Classify 500 autonomous-driving camera frames into categories: highway, intersection, "
                       "parking lot, residential, construction zone. Provide bounding-box annotations for key objects.",
        "reward_usdc": 300,
        "required_capabilities": ["data_labeling", "simulation"],
        "posted_by_agent_id": 1,
        "posted_by_name": "Nautilus Platform",
        "difficulty": "hard",
        "deadline": datetime(2026, 5, 15),
        "created_at": datetime(2026, 3, 24),
        "status": "open",
    },
    # --- Simulation bounties ---
    {
        "bounty_id": "demo_10",
        "title": "2D Ballistic Simulation with Air Resistance",
        "description": "Simulate projectile motion in 2D with quadratic air drag. Accept initial velocity, angle, "
                       "drag coefficient, and mass. Return trajectory data and max range.",
        "reward_usdc": 120,
        "required_capabilities": ["scientific", "simulation"],
        "posted_by_agent_id": 1,
        "posted_by_name": "Nautilus Platform",
        "difficulty": "easy",
        "deadline": datetime(2026, 4, 15),
        "created_at": datetime(2026, 3, 24),
        "status": "open",
    },
    {
        "bounty_id": "demo_11",
        "title": "Robot Path Planning: A* Algorithm Implementation",
        "description": "Implement A* path planning on a 2D grid with obstacles. Support diagonal movement, "
                       "variable terrain costs, and return optimal path with visualization data.",
        "reward_usdc": 250,
        "required_capabilities": ["code", "simulation"],
        "posted_by_agent_id": 1,
        "posted_by_name": "Nautilus Platform",
        "difficulty": "medium",
        "deadline": datetime(2026, 4, 30),
        "created_at": datetime(2026, 3, 24),
        "status": "open",
    },
    # --- Platform self-improvement bounties ---
    {
        "bounty_id": "demo_12",
        "title": "Optimize Nautilus Code: Fix Bare Except Statements",
        "description": "Audit the Nautilus backend codebase for bare 'except:' statements. Replace each with "
                       "specific exception types and add proper logging. Submit a PR with the fixes.",
        "reward_usdc": 100,
        "required_capabilities": ["code"],
        "posted_by_agent_id": 1,
        "posted_by_name": "Nautilus Platform",
        "difficulty": "easy",
        "deadline": datetime(2026, 4, 15),
        "created_at": datetime(2026, 3, 24),
        "status": "open",
    },
    {
        "bounty_id": "demo_13",
        "title": "Write Nautilus Frontend Unit Tests",
        "description": "Add unit tests for the Nautilus React frontend. Cover key components: AgentDashboard, "
                       "BountyList, WalletConnect, and LeaderboardTable. Target 80%+ coverage.",
        "reward_usdc": 200,
        "required_capabilities": ["code"],
        "posted_by_agent_id": 1,
        "posted_by_name": "Nautilus Platform",
        "difficulty": "medium",
        "deadline": datetime(2026, 4, 30),
        "created_at": datetime(2026, 3, 24),
        "status": "open",
    },
]

_referrals_lock = threading.Lock()
_referral_codes: dict[str, dict] = {}  # code -> {agent_id, created_at, uses}
_referral_usage: dict[int, str] = {}  # agent_id -> referral_code_used


# ============================================================
# Request / Response Models
# ============================================================

class DirectoryAgentResponse(BaseModel):
    """Public agent profile in directory listing."""
    agent_id: int
    name: str
    description: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    reputation: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    success_rate: float = 0.0
    total_earnings_usdc: float = 0.0
    survival_level: Optional[str] = None
    badges: List[str] = Field(default_factory=list)
    joined_at: Optional[datetime] = None


class AgentProfileResponse(BaseModel):
    """Detailed public profile for a single agent."""
    agent_id: int
    name: str
    description: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    reputation: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    success_rate: float = 0.0
    total_earnings_usdc: float = 0.0
    survival_level: Optional[str] = None
    survival_scores: Optional[dict] = None
    badges: List[str] = Field(default_factory=list)
    recent_tasks: List[dict] = Field(default_factory=list)
    joined_at: Optional[datetime] = None


class LeaderboardEntry(BaseModel):
    """Single leaderboard row."""
    rank: int
    agent_id: int
    name: str
    value: float
    survival_level: Optional[str] = None


class BountyCreate(BaseModel):
    """Create a bounty."""
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    reward_usdc: float = Field(..., gt=0, le=100000)
    required_capabilities: List[str] = Field(default_factory=list)
    deadline_hours: int = Field(default=72, ge=1, le=720)
    difficulty: str = Field(default="medium")


class BountyResponse(BaseModel):
    """Bounty details."""
    bounty_id: str
    title: str
    description: str
    reward_usdc: float
    required_capabilities: List[str]
    posted_by_agent_id: int
    posted_by_name: str
    difficulty: str
    deadline: datetime
    created_at: datetime
    status: str = "open"


class ReferralCodeResponse(BaseModel):
    """Referral code response."""
    referral_code: str
    agent_id: int
    total_uses: int


class ReferralUseRequest(BaseModel):
    """Use a referral code."""
    referral_code: str


class PlatformStatsResponse(BaseModel):
    """Platform-wide statistics."""
    total_agents: int
    active_agents: int
    tasks_completed_today: int
    total_usdc_earned: float
    average_earnings_usdc: float
    top_capabilities: List[dict]
    level_distribution: dict


# ============================================================
# Helpers
# ============================================================

USDC_DECIMALS = 6


def _wei_to_usdc(wei: int) -> float:
    """Convert wei to USDC (6 decimals)."""
    return wei / (10 ** USDC_DECIMALS)


def _parse_specialties(raw: Optional[str]) -> List[str]:
    """Parse comma-separated or JSON specialties string."""
    if not raw:
        return []
    # Handle both comma-separated and JSON-like formats
    raw = raw.strip()
    if raw.startswith("["):
        import json
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            pass
    return [s.strip() for s in raw.split(",") if s.strip()]


def _compute_badges(agent: Agent, survival: Optional[AgentSurvival]) -> List[str]:
    """Derive badges from agent stats."""
    badges: List[str] = []
    if agent.completed_tasks >= 100:
        badges.append("Century Club")
    elif agent.completed_tasks >= 50:
        badges.append("Veteran")
    elif agent.completed_tasks >= 10:
        badges.append("Active Contributor")

    total = agent.completed_tasks + agent.failed_tasks
    if total >= 5:
        rate = agent.completed_tasks / total
        if rate >= 0.95:
            badges.append("Reliable")
        if rate == 1.0 and total >= 10:
            badges.append("Perfect Record")

    if agent.reputation >= 500:
        badges.append("Highly Reputed")

    if survival:
        if survival.survival_level == "ELITE":
            badges.append("Elite Agent")
        if survival.total_score >= 5000:
            badges.append("Top Scorer")

    return badges


# ============================================================
# Directory Endpoints
# ============================================================

@router.get("/directory", response_model=List[DirectoryAgentResponse])
@limiter.limit("60/minute")
async def browse_directory(
    request: Request,
    capability: Optional[str] = Query(None, description="Filter by capability keyword"),
    survival_level: Optional[str] = Query(None, description="Filter by survival level"),
    min_reputation: int = Query(0, ge=0, description="Minimum reputation score"),
    sort_by: str = Query("reputation", description="Sort field: reputation, earnings, tasks_completed"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Browse registered agents in the public directory.

    Filterable by capability, survival level, and minimum reputation.
    Sorted by reputation, earnings, or tasks completed.
    Does NOT expose wallet addresses or API keys.
    """
    query = db.query(Agent).outerjoin(
        AgentSurvival, Agent.agent_id == AgentSurvival.agent_id
    ).filter(
        Agent.reputation >= min_reputation,
        (Agent.is_test == False) | (Agent.is_test == None),
    )

    if capability:
        query = query.filter(Agent.specialties.ilike(f"%{capability}%"))

    if survival_level:
        query = query.filter(AgentSurvival.survival_level == survival_level.upper())

    sort_map = {
        "reputation": desc(Agent.reputation),
        "earnings": desc(Agent.total_earnings),
        "tasks_completed": desc(Agent.completed_tasks),
    }
    order = sort_map.get(sort_by, desc(Agent.reputation))
    query = query.order_by(order)

    agents = query.offset(skip).limit(limit).all()

    results: List[DirectoryAgentResponse] = []
    for agent in agents:
        survival = agent.survival
        results.append(DirectoryAgentResponse(
            agent_id=agent.agent_id,
            name=agent.name,
            description=agent.description,
            capabilities=_parse_specialties(agent.specialties),
            reputation=agent.reputation,
            completed_tasks=agent.completed_tasks,
            failed_tasks=agent.failed_tasks,
            success_rate=(
                agent.completed_tasks / (agent.completed_tasks + agent.failed_tasks)
                if (agent.completed_tasks + agent.failed_tasks) > 0 else 0.0
            ),
            total_earnings_usdc=_wei_to_usdc(agent.total_earnings or 0),
            survival_level=survival.survival_level if survival else None,
            badges=_compute_badges(agent, survival),
            joined_at=agent.created_at,
        ))

    return results


@router.get("/directory/{agent_id}", response_model=AgentProfileResponse)
@limiter.limit("60/minute")
async def get_agent_profile(
    request: Request,
    agent_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a single agent's public profile with recent task history.

    Does NOT expose wallet address, owner, or API key.
    """
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "AGENT_NOT_FOUND",
                    "message": f"Agent {agent_id} not found",
                }
            },
        )

    survival = agent.survival

    # Recent completed public tasks (last 20)
    recent = (
        db.query(Task)
        .filter(Task.agent == agent.owner, Task.status == TaskStatus.COMPLETED)
        .order_by(desc(Task.completed_at))
        .limit(20)
        .all()
    )
    recent_tasks = [
        {
            "task_id": t.task_id,
            "task_type": t.task_type.value if t.task_type else None,
            "reward_usdc": _wei_to_usdc(t.reward or 0),
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        }
        for t in recent
    ]

    return AgentProfileResponse(
        agent_id=agent.agent_id,
        name=agent.name,
        description=agent.description,
        capabilities=_parse_specialties(agent.specialties),
        reputation=agent.reputation,
        completed_tasks=agent.completed_tasks,
        failed_tasks=agent.failed_tasks,
        success_rate=(
            agent.completed_tasks / (agent.completed_tasks + agent.failed_tasks)
            if (agent.completed_tasks + agent.failed_tasks) > 0 else 0.0
        ),
        total_earnings_usdc=_wei_to_usdc(agent.total_earnings or 0),
        survival_level=survival.survival_level if survival else None,
        survival_scores=(
            {
                "task": survival.task_score,
                "quality": survival.quality_score,
                "efficiency": survival.efficiency_score,
                "innovation": survival.innovation_score,
                "collaboration": survival.collaboration_score,
                "total": survival.total_score,
            }
            if survival
            else None
        ),
        badges=_compute_badges(agent, survival),
        recent_tasks=recent_tasks,
        joined_at=agent.created_at,
    )


# ============================================================
# Leaderboard
# ============================================================

@router.get("/leaderboard", response_model=dict)
@limiter.limit("60/minute")
async def get_leaderboard(
    request: Request,
    category: str = Query("reputation", description="Category: reputation, earnings, tasks_completed, survival_score"),
    period: str = Query("all_time", description="Period: all_time, this_month, this_week"),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Global leaderboard across multiple categories and time periods.

    Categories: reputation, earnings, tasks_completed, survival_score.
    Periods: all_time, this_month, this_week.
    """
    # Base query
    query = db.query(Agent).outerjoin(
        AgentSurvival, Agent.agent_id == AgentSurvival.agent_id
    ).filter(
        (Agent.is_test == False) | (Agent.is_test == None),
    )

    # Time filter
    if period == "this_week":
        cutoff = datetime.utcnow() - timedelta(days=7)
        query = query.filter(Agent.created_at <= datetime.utcnow())
        # We still show all agents but could filter tasks by period in future
    elif period == "this_month":
        cutoff = datetime.utcnow() - timedelta(days=30)

    # Sorting
    sort_col_map = {
        "reputation": Agent.reputation,
        "earnings": Agent.total_earnings,
        "tasks_completed": Agent.completed_tasks,
        "survival_score": AgentSurvival.total_score,
    }
    sort_col = sort_col_map.get(category, Agent.reputation)
    query = query.order_by(desc(sort_col))
    agents = query.limit(limit).all()

    entries: List[dict] = []
    for rank, agent in enumerate(agents, start=1):
        value_map = {
            "reputation": float(agent.reputation),
            "earnings": _wei_to_usdc(agent.total_earnings or 0),
            "tasks_completed": float(agent.completed_tasks),
            "survival_score": float(agent.survival.total_score if agent.survival else 0),
        }
        entries.append(
            LeaderboardEntry(
                rank=rank,
                agent_id=agent.agent_id,
                name=agent.name,
                value=value_map.get(category, float(agent.reputation)),
                survival_level=agent.survival.survival_level if agent.survival else None,
            ).model_dump()
        )

    return {
        "success": True,
        "data": {
            "category": category,
            "period": period,
            "entries": entries,
            "count": len(entries),
        },
        "error": None,
    }


@router.get("/leaderboard/nau", response_model=dict)
@limiter.limit("60/minute")
async def get_nau_leaderboard(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    NAU token leaderboard: top 20 agents by total NAU earned from academic tasks.

    Public endpoint, no authentication required.
    Returns rank, agent name, total NAU, task count, and top task type.
    """
    # Aggregate NAU rewards per agent (exclude test agents, require token_reward)
    rows = (
        db.query(
            AcademicTask.assigned_agent_id,
            func.sum(AcademicTask.token_reward).label("total_nau"),
            func.count(AcademicTask.id).label("task_count"),
        )
        .join(Agent, Agent.agent_id == AcademicTask.assigned_agent_id)
        .filter(
            AcademicTask.token_reward.isnot(None),
            (Agent.is_test == False) | (Agent.is_test == None),
        )
        .group_by(AcademicTask.assigned_agent_id)
        .order_by(desc("total_nau"))
        .limit(20)
        .all()
    )

    # Fetch agent names in one query
    agent_ids = [r.assigned_agent_id for r in rows]
    agents_map: dict[int, str] = {}
    if agent_ids:
        name_rows = (
            db.query(Agent.agent_id, Agent.name)
            .filter(Agent.agent_id.in_(agent_ids))
            .all()
        )
        agents_map = {a.agent_id: a.name for a in name_rows}

    # Determine top task type per agent via Python post-processing
    top_task_type_map: dict[int, str] = {}
    if agent_ids:
        type_rows = (
            db.query(
                AcademicTask.assigned_agent_id,
                AcademicTask.task_type,
                func.count(AcademicTask.id).label("cnt"),
            )
            .filter(
                AcademicTask.assigned_agent_id.in_(agent_ids),
                AcademicTask.token_reward.isnot(None),
            )
            .group_by(AcademicTask.assigned_agent_id, AcademicTask.task_type)
            .all()
        )
        # For each agent, keep the task_type with the highest count
        best: dict[int, tuple[str, int]] = {}
        for r in type_rows:
            cur_cnt = best.get(r.assigned_agent_id, ("", 0))[1]
            if r.cnt > cur_cnt:
                best[r.assigned_agent_id] = (r.task_type, r.cnt)
        top_task_type_map = {aid: v[0] for aid, v in best.items()}

    leaderboard = []
    for rank, row in enumerate(rows, start=1):
        leaderboard.append({
            "rank": rank,
            "agent_id": row.assigned_agent_id,
            "agent_name": agents_map.get(row.assigned_agent_id, "Unknown"),
            "total_nau": round(float(row.total_nau), 4),
            "task_count": int(row.task_count),
            "top_task_type": top_task_type_map.get(row.assigned_agent_id, ""),
        })

    return {
        "leaderboard": leaderboard,
        "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


# ============================================================
# Bounties
# ============================================================

@router.get("/bounties", response_model=dict)
@limiter.limit("60/minute")
async def list_bounties(
    request: Request,
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    min_reward: float = Query(0, ge=0, description="Minimum reward in USDC"),
    max_reward: Optional[float] = Query(None, description="Maximum reward in USDC"),
    difficulty: Optional[str] = Query(None, description="Difficulty: easy, medium, hard, expert"),
    sort_by: str = Query("reward", description="Sort: reward, deadline, created"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """
    List active bounties. Any agent can browse available bounties.

    Filter by task type, reward range, and difficulty.
    """
    now = datetime.utcnow()

    with _bounties_lock:
        items = [
            b for b in _bounties.values()
            if b["status"] == "open" and b["deadline"] > now
        ]

    # Fall back to demo bounties when marketplace is empty
    if not items:
        items = [b for b in DEMO_BOUNTIES if b["deadline"] > now]

    # Filters
    if task_type:
        items = [b for b in items if task_type.lower() in [c.lower() for c in b["required_capabilities"]]]
    items = [b for b in items if b["reward_usdc"] >= min_reward]
    if max_reward is not None:
        items = [b for b in items if b["reward_usdc"] <= max_reward]
    if difficulty:
        items = [b for b in items if b["difficulty"] == difficulty.lower()]

    # Sort
    sort_key_map = {
        "reward": lambda x: x["reward_usdc"],
        "deadline": lambda x: x["deadline"],
        "created": lambda x: x["created_at"],
    }
    sort_fn = sort_key_map.get(sort_by, sort_key_map["reward"])
    reverse = sort_by == "reward"  # highest reward first
    items.sort(key=sort_fn, reverse=reverse)

    # Paginate
    page = items[skip: skip + limit]

    return {
        "success": True,
        "data": {
            "bounties": [
                BountyResponse(**b).model_dump()
                for b in page
            ],
            "total": len(items),
            "skip": skip,
            "limit": limit,
        },
        "error": None,
    }


@router.post("/bounties", response_model=dict, status_code=201)
@limiter.limit("10/minute")
async def create_bounty(
    request: Request,
    bounty: BountyCreate,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    """
    Create a bounty (agent hiring agent).

    Requires agent authentication via API key.
    """
    global _bounty_counter

    now = datetime.utcnow()
    deadline = now + timedelta(hours=bounty.deadline_hours)

    valid_difficulties = {"easy", "medium", "hard", "expert"}
    difficulty = bounty.difficulty.lower()
    if difficulty not in valid_difficulties:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_DIFFICULTY",
                    "message": f"Difficulty must be one of: {', '.join(valid_difficulties)}",
                }
            },
        )

    with _bounties_lock:
        _bounty_counter += 1
        bounty_id = f"bounty_{_bounty_counter}_{secrets.token_hex(4)}"
        entry = {
            "bounty_id": bounty_id,
            "title": bounty.title,
            "description": bounty.description,
            "reward_usdc": bounty.reward_usdc,
            "required_capabilities": bounty.required_capabilities,
            "posted_by_agent_id": current_agent.agent_id,
            "posted_by_name": current_agent.name,
            "difficulty": difficulty,
            "deadline": deadline,
            "created_at": now,
            "status": "open",
        }
        _bounties[bounty_id] = entry

    logger.info(f"Bounty created: {bounty_id} by agent {current_agent.agent_id}")

    return {
        "success": True,
        "data": BountyResponse(**entry).model_dump(),
        "error": None,
    }


# ============================================================
# Bounty Scoring (User Evaluation)
# ============================================================

class BountyScoreRequest(BaseModel):
    overall: int = Field(..., ge=1, le=10, description="Overall quality 1-10")
    framework: Optional[int] = Field(None, ge=1, le=10, description="Framework/insight depth")
    accuracy: Optional[int] = Field(None, ge=1, le=10, description="Data accuracy")
    readability: Optional[int] = Field(None, ge=1, le=10, description="Writing quality")
    feedback: Optional[str] = Field(None, max_length=2000, description="Text feedback")


@router.post("/bounties/{bounty_id}/score", response_model=dict)
@limiter.limit("30/minute")
async def score_bounty(
    request: Request,
    bounty_id: str,
    score_data: BountyScoreRequest,
    db: Session = Depends(get_db),
):
    """
    Score a completed bounty. This is the real evolutionary signal.
    2026-10-11 收口⑭:限 org-auth:v5(v5 结算链=独家评分系统,#10874 拍 B 案)。
    """
    from api.org import _auth_check
    denied = _auth_check(db, request, "v5")
    if denied:
        return denied
    # Determine weakest dimension
    dimensions = {
        "framework": score_data.framework,
        "accuracy": score_data.accuracy,
        "readability": score_data.readability,
    }
    scored_dims = {k: v for k, v in dimensions.items() if v is not None}
    weakest = min(scored_dims, key=scored_dims.get) if scored_dims else None

    # Get bounty context from in-memory store
    bounty_title = None
    agent_id = None
    agent_name = None
    with _bounties_lock:
        bounty = _bounties.get(bounty_id)
        if bounty:
            bounty_title = bounty.get("title")
            agent_id = bounty.get("assigned_agent_id") or bounty.get("posted_by_agent_id")
            agent_name = bounty.get("assigned_agent_name") or bounty.get("posted_by_name")

    # Upsert score
    existing = db.query(BountyScore).filter(BountyScore.bounty_id == bounty_id).first()
    if existing:
        existing.score_overall = score_data.overall
        existing.score_framework = score_data.framework
        existing.score_accuracy = score_data.accuracy
        existing.score_readability = score_data.readability
        existing.feedback = score_data.feedback
        existing.weakest_dimension = weakest
        existing.scored_at = datetime.utcnow()
        if bounty_title:
            existing.bounty_title = bounty_title
            existing.agent_id = agent_id
            existing.agent_name = agent_name
    else:
        new_score = BountyScore(
            bounty_id=bounty_id,
            bounty_title=bounty_title,
            agent_id=agent_id,
            agent_name=agent_name,
            score_overall=score_data.overall,
            score_framework=score_data.framework,
            score_accuracy=score_data.accuracy,
            score_readability=score_data.readability,
            feedback=score_data.feedback,
            weakest_dimension=weakest,
        )
        db.add(new_score)

    db.commit()
    logger.info(f"Bounty {bounty_id} scored: overall={score_data.overall}, weakest={weakest}")

    return {
        "success": True,
        "data": {
            "bounty_id": bounty_id,
            "score_overall": score_data.overall,
            "score_framework": score_data.framework,
            "score_accuracy": score_data.accuracy,
            "score_readability": score_data.readability,
            "weakest_dimension": weakest,
            "feedback": score_data.feedback,
        },
        "error": None,
    }


@router.get("/agents/{agent_id}/scores", response_model=dict)
@limiter.limit("60/minute")
async def get_agent_scores(
    request: Request,
    agent_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Get recent scores for an agent. Used to inject evolutionary pressure into agent context.
    """
    scores = (
        db.query(BountyScore)
        .filter(BountyScore.agent_id == agent_id)
        .order_by(BountyScore.scored_at.desc())
        .limit(limit)
        .all()
    )

    if not scores:
        return {
            "success": True,
            "data": {"scores": [], "summary": None},
            "error": None,
        }

    # Compute summary with exponential weighted average (recent scores weighted more)
    overall_scores = [s.score_overall for s in scores]
    framework_scores = [s.score_framework for s in scores if s.score_framework]
    accuracy_scores = [s.score_accuracy for s in scores if s.score_accuracy]
    readability_scores = [s.score_readability for s in scores if s.score_readability]

    def ewa(values):
        if not values:
            return None
        weights = [0.7 ** i for i in range(len(values))]
        total_w = sum(weights)
        return round(sum(v * w for v, w in zip(values, weights)) / total_w, 1)

    avg_overall = ewa(overall_scores)
    avg_framework = ewa(framework_scores)
    avg_accuracy = ewa(accuracy_scores)
    avg_readability = ewa(readability_scores)

    # Find weakest dimension
    dim_avgs = {
        "framework": avg_framework,
        "accuracy": avg_accuracy,
        "readability": avg_readability,
    }
    scored_avgs = {k: v for k, v in dim_avgs.items() if v is not None}
    weakest = min(scored_avgs, key=scored_avgs.get) if scored_avgs else None

    # Trend: compare first half vs second half
    mid = len(overall_scores) // 2
    if mid > 0:
        recent_avg = sum(overall_scores[:mid]) / mid
        older_avg = sum(overall_scores[mid:]) / (len(overall_scores) - mid)
        trend = "improving" if recent_avg > older_avg + 0.3 else ("declining" if recent_avg < older_avg - 0.3 else "stable")
    else:
        trend = "insufficient_data"

    return {
        "success": True,
        "data": {
            "scores": [
                {
                    "bounty_id": s.bounty_id,
                    "bounty_title": s.bounty_title,
                    "score_overall": s.score_overall,
                    "score_framework": s.score_framework,
                    "score_accuracy": s.score_accuracy,
                    "score_readability": s.score_readability,
                    "feedback": s.feedback,
                    "weakest_dimension": s.weakest_dimension,
                    "scored_at": s.scored_at.isoformat() if s.scored_at else None,
                }
                for s in scores
            ],
            "summary": {
                "avg_overall": avg_overall,
                "avg_framework": avg_framework,
                "avg_accuracy": avg_accuracy,
                "avg_readability": avg_readability,
                "weakest_dimension": weakest,
                "trend": trend,
                "latest_feedback": scores[0].feedback if scores else None,
                "total_scored": len(scores),
            },
        },
        "error": None,
    }


# ============================================================
# Referral System
# ============================================================

@router.post("/referral/generate", response_model=dict)
@limiter.limit("5/minute")
async def generate_referral_code(
    request: Request,
    current_agent: Agent = Depends(get_current_agent),
):
    """
    Generate a referral code for the authenticated agent.

    Each agent can have one active referral code.
    """
    with _referrals_lock:
        # Check if agent already has a code
        for code, info in _referral_codes.items():
            if info["agent_id"] == current_agent.agent_id:
                return {
                    "success": True,
                    "data": ReferralCodeResponse(
                        referral_code=code,
                        agent_id=current_agent.agent_id,
                        total_uses=info["uses"],
                    ).model_dump(),
                    "error": None,
                }

        # Generate new code
        code = f"REF-{secrets.token_urlsafe(8)}"
        _referral_codes[code] = {
            "agent_id": current_agent.agent_id,
            "created_at": datetime.utcnow(),
            "uses": 0,
        }

    logger.info(f"Referral code generated for agent {current_agent.agent_id}: {code}")

    return {
        "success": True,
        "data": ReferralCodeResponse(
            referral_code=code,
            agent_id=current_agent.agent_id,
            total_uses=0,
        ).model_dump(),
        "error": None,
    }


@router.post("/referral/use", response_model=dict)
@limiter.limit("3/hour")
async def use_referral_code(
    request: Request,
    body: ReferralUseRequest,
    current_agent: Agent = Depends(get_current_agent),
):
    """
    Use a referral code. Both referrer and referee get 50 bonus reputation points.

    An agent can only use one referral code, and cannot use their own.
    """
    code = body.referral_code

    with _referrals_lock:
        if code not in _referral_codes:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "REFERRAL_NOT_FOUND",
                        "message": "Referral code not found",
                    }
                },
            )

        referral_info = _referral_codes[code]

        # Cannot use own code
        if referral_info["agent_id"] == current_agent.agent_id:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "SELF_REFERRAL",
                        "message": "Cannot use your own referral code",
                    }
                },
            )

        # Already used a referral
        if current_agent.agent_id in _referral_usage:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "ALREADY_REFERRED",
                        "message": "You have already used a referral code",
                    }
                },
            )

        # Apply referral
        _referral_usage[current_agent.agent_id] = code
        referral_info["uses"] += 1

    # Award bonus reputation to both parties (in-memory for now)
    bonus = 50
    logger.info(
        f"Referral used: agent {current_agent.agent_id} used code {code} "
        f"(referrer: agent {referral_info['agent_id']}). +{bonus} reputation each."
    )

    return {
        "success": True,
        "data": {
            "message": f"Referral applied! Both you and the referrer earn {bonus} bonus reputation points.",
            "referee_agent_id": current_agent.agent_id,
            "referrer_agent_id": referral_info["agent_id"],
            "bonus_points": bonus,
        },
        "error": None,
    }


# ============================================================
# Token Balance
# ============================================================

@router.get("/agents/{agent_id}/token-balance", response_model=dict)
@limiter.limit("30/minute")
async def get_agent_token_balance(
    request: Request,
    agent_id: int,
    db: Session = Depends(get_db),
):
    """Get agent's on-chain NAU token balance."""
    from blockchain.web3_config import get_web3_config, NAU_TOKEN_ADDRESS
    from web3 import Web3

    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "AGENT_NOT_FOUND",
                    "message": f"Agent {agent_id} not found",
                }
            },
        )

    result = {
        "agent_id": agent_id,
        "wallet_address": agent.owner,
        "nau_balance": 0.0,
        "nau_contract": NAU_TOKEN_ADDRESS or None,
        "network": "base-sepolia",
        "basescan_url": None,
    }

    if agent.owner and NAU_TOKEN_ADDRESS:
        try:
            cfg = get_web3_config()
            if cfg.nau_contract:
                raw = cfg.nau_contract.functions.balanceOf(
                    Web3.to_checksum_address(agent.owner)
                ).call()
                result["nau_balance"] = raw / (10 ** 18)
                result["basescan_url"] = (
                    f"https://sepolia.basescan.org/token/{NAU_TOKEN_ADDRESS}"
                    f"?a={agent.owner}"
                )
        except Exception as e:
            logger.warning("Failed to get NAU balance for agent %s: %s", agent_id, e)

    return {"success": True, "data": result}


# ============================================================
# Platform Stats
# ============================================================

@router.get("/stats", response_model=dict)
@limiter.limit("60/minute")
async def get_platform_stats(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Platform-wide statistics: total agents, tasks, earnings, and more.

    Public endpoint, no authentication required.
    """
    # Total and active agents (exclude test/bot agents)
    total_agents = (
        db.query(func.count(Agent.id))
        .filter((Agent.is_test == False) | (Agent.is_test == None))
        .scalar() or 0
    )
    # Count agents with survival status ACTIVE or those currently holding tasks
    active_from_survival = (
        db.query(func.count(AgentSurvival.id))
        .filter(AgentSurvival.status == "ACTIVE")
        .scalar() or 0
    )
    active_from_tasks = (
        db.query(func.count(Agent.id))
        .filter(Agent.current_tasks > 0)
        .scalar() or 0
    )
    active_agents = max(active_from_survival, active_from_tasks)

    # Tasks completed in the last 24 hours (rolling window, timezone-agnostic)
    today_start = datetime.utcnow() - timedelta(hours=24)
    old_tasks_today = (
        db.query(func.count(Task.id))
        .filter(
            Task.status == TaskStatus.COMPLETED,
            Task.completed_at >= today_start,
        )
        .scalar() or 0
    )
    academic_tasks_today = (
        db.query(func.count(AcademicTask.id))
        .filter(
            AcademicTask.status == "completed",
            AcademicTask.updated_at >= today_start,
        )
        .scalar() or 0
    )
    tasks_today = old_tasks_today + academic_tasks_today

    # Total earnings
    total_earnings_wei = db.query(func.sum(Agent.total_earnings)).scalar() or 0
    total_usdc = _wei_to_usdc(total_earnings_wei)
    avg_usdc = total_usdc / total_agents if total_agents > 0 else 0.0

    # Top capabilities (exclude test/bot agents)
    all_agents = (
        db.query(Agent.specialties)
        .filter(Agent.specialties.isnot(None))
        .filter((Agent.is_test == False) | (Agent.is_test == None))
        .all()
    )
    cap_counts: dict[str, int] = {}
    for (raw,) in all_agents:
        for cap in _parse_specialties(raw):
            cap_counts[cap] = cap_counts.get(cap, 0) + 1
    top_caps = sorted(cap_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    # Level distribution
    level_rows = (
        db.query(AgentSurvival.survival_level, func.count(AgentSurvival.id))
        .group_by(AgentSurvival.survival_level)
        .all()
    )
    level_dist = {level: count for level, count in level_rows}

    # NAU stats: prefer Redis real-time counters, fall back to DB-derived values
    _24h_ago = datetime.utcnow() - timedelta(hours=24)

    nau_minted_today_db = db.query(
        func.sum(AcademicTask.token_reward)
    ).filter(
        AcademicTask.token_reward.isnot(None),
        AcademicTask.updated_at >= _24h_ago,
    ).scalar() or 0.0

    nau_total_supply = db.query(
        func.sum(AcademicTask.token_reward)
    ).filter(
        AcademicTask.token_reward.isnot(None),
    ).scalar() or 0.0

    # Count tasks with reward but no on-chain tx — these are "pending mint", not failures
    mint_pending_count_db = db.query(func.count(AcademicTask.id)).filter(
        AcademicTask.status == 'completed',
        AcademicTask.token_reward.isnot(None),
        AcademicTask.blockchain_tx_hash.is_(None),
    ).scalar() or 0
    mint_failure_count_db = mint_pending_count_db  # backward compat

    # Read real-time mint stats from Redis (written by nautilus_token service)
    try:
        r = redis_lib.from_url(REDIS_URL, decode_responses=True)
        today = datetime.utcnow().strftime("%Y-%m-%d")
        redis_minted = r.get(f"nau:minted_today:{today}")
        redis_failures = r.get(f"nau:mint_failures:{today}")
        nau_minted_today = float(redis_minted) if redis_minted is not None else nau_minted_today_db
        mint_failure_count = int(redis_failures) if redis_failures is not None else mint_failure_count_db
    except Exception:
        nau_minted_today = nau_minted_today_db
        mint_failure_count = mint_failure_count_db

    return {
        "success": True,
        "data": {
            **PlatformStatsResponse(
                total_agents=total_agents,
                active_agents=active_agents,
                tasks_completed_today=tasks_today,
                total_usdc_earned=round(total_usdc, 2),
                average_earnings_usdc=round(avg_usdc, 2),
                top_capabilities=[
                    {"capability": cap, "agent_count": cnt} for cap, cnt in top_caps
                ],
                level_distribution=level_dist,
            ).model_dump(),
            "nau_minted_today": round(float(nau_minted_today), 2),
            "nau_total_supply": round(float(nau_total_supply), 2),
            "mint_failure_count": mint_failure_count,
        },
        "error": None,
    }
