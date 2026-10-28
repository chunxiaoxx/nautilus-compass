"""Agent team coordination API endpoints."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from models.team import Team, TeamMember
from services.agent_team import AgentTeamService
from utils.database import get_db
from utils.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class AssembleRequest(BaseModel):
    task_description: str = Field(..., min_length=10, description="Task to assemble a team for")
    task_id: Optional[str] = Field(None, description="Optional linked task ID")
    min_agents: int = Field(3, ge=2, le=10, description="Minimum team size")


class ExecuteRequest(BaseModel):
    task_description: str = Field(..., min_length=10, description="Task description for decomposition")


class TeamResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/assemble", response_model=TeamResponse)
async def assemble_team(
    request: AssembleRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> TeamResponse:
    """Assemble a team dynamically based on task requirements."""
    try:
        service = AgentTeamService(db)
        result = await service.assemble(
            task_description=request.task_description,
            task_id=request.task_id,
            min_agents=request.min_agents,
        )
        return TeamResponse(success=True, data=result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Error assembling team: %s", exc)
        return TeamResponse(success=False, error=str(exc))


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> TeamResponse:
    """Get team status and member details."""
    team = db.query(Team).filter(Team.team_id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")

    members = db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
    return TeamResponse(
        success=True,
        data={
            "team_id": team.team_id,
            "name": team.name,
            "task_id": team.task_id,
            "status": team.status,
            "leader_agent_id": team.leader_agent_id,
            "quality_score": team.quality_score,
            "created_at": team.created_at.isoformat() if team.created_at else None,
            "completed_at": team.completed_at.isoformat() if team.completed_at else None,
            "members": [
                {
                    "agent_id": m.agent_id,
                    "role": m.role,
                    "subtask": m.subtask,
                    "status": m.status,
                    "result": m.result,
                }
                for m in members
            ],
        },
    )


@router.post("/{team_id}/execute", response_model=TeamResponse)
async def execute_team(
    team_id: str,
    request: ExecuteRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> TeamResponse:
    """Decompose task, execute subtasks in parallel, review, and merge."""
    team = db.query(Team).filter(Team.team_id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
    if team.status not in ("active", "assembling"):
        raise HTTPException(
            status_code=400,
            detail=f"Team is in '{team.status}' state; must be active",
        )

    try:
        service = AgentTeamService(db)
        await service.decompose_task(team_id, request.task_description)
        result = await service.execute_as_team(team_id)
        return TeamResponse(success=True, data=result.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Error executing team %s: %s", team_id, exc)
        return TeamResponse(success=False, error=str(exc))


@router.post("/{team_id}/dissolve", response_model=TeamResponse)
async def dissolve_team(
    team_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> TeamResponse:
    """Dissolve team and update collaboration scores."""
    team = db.query(Team).filter(Team.team_id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")

    try:
        service = AgentTeamService(db)
        await service.dissolve(team_id)
        return TeamResponse(success=True, data={"team_id": team_id, "status": "dissolved"})
    except Exception as exc:
        logger.error("Error dissolving team %s: %s", team_id, exc)
        return TeamResponse(success=False, error=str(exc))


@router.get("/", response_model=TeamResponse)
async def list_teams(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> TeamResponse:
    """List teams with optional status filter and pagination."""
    query = db.query(Team)
    if status:
        query = query.filter(Team.status == status)

    total = query.count()
    teams = query.order_by(Team.created_at.desc()).offset(offset).limit(limit).all()

    return TeamResponse(
        success=True,
        data={
            "teams": [
                {
                    "team_id": t.team_id,
                    "name": t.name,
                    "task_id": t.task_id,
                    "status": t.status,
                    "leader_agent_id": t.leader_agent_id,
                    "quality_score": t.quality_score,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in teams
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    )
