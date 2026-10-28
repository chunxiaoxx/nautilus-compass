from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from utils.database import get_db
from models.database import Task, Agent, Reward, AcademicTask

router = APIRouter(prefix="/api/stats", tags=["stats"])

@router.get("")
async def get_platform_stats(db: Session = Depends(get_db)):
    """
    Get platform statistics.
    Public endpoint.
    """
    # Use academic_tasks as primary source (most tasks live there)
    academic_count = db.query(func.count(AcademicTask.task_id)).scalar() or 0
    legacy_count = db.query(func.count(Task.id)).scalar() or 0
    total_tasks = academic_count + legacy_count

    active_agents = db.query(func.count(Agent.id)).scalar() or 0
    total_rewards = db.query(func.sum(Reward.amount)).scalar() or 0

    return {
        "total_tasks": total_tasks,
        "active_agents": active_agents,
        "total_rewards": float(total_rewards) if total_rewards else 0.0
    }
