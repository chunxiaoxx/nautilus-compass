"""
Agent Tasks API
Provides task query and management interface for external agents like OpenClaw
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from utils.database import get_db
from models.database import Task, Agent, User
from api.auth import get_current_user

router = APIRouter(prefix="/api", tags=["agent-tasks"])


# Pydantic Models
class TaskProgress(BaseModel):
    progress: int  # 0-100
    message: str


class TaskSubmission(BaseModel):
    result: str
    files: Optional[List[str]] = []


class AgentAPIKey(BaseModel):
    api_key: str
    created_at: datetime


# Agent API Key verification
async def verify_agent_api_key(
    x_agent_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Agent:
    """Verify Agent API Key"""
    if not x_agent_api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")

    # Extract Agent ID from API Key (format: nautilus_ak_{agent_id}_{random})
    try:
        parts = x_agent_api_key.split('_')
        if len(parts) < 3 or parts[0] != 'nautilus' or parts[1] != 'ak':
            raise ValueError("Invalid API Key format")

        agent_id = int(parts[2])
        agent = db.query(Agent).filter(Agent.id == agent_id).first()

        if not agent:
            raise HTTPException(status_code=401, detail="Invalid API Key")

        # TODO: Verify complete API Key (need to store hashed key in database)
        return agent

    except (ValueError, IndexError):
        raise HTTPException(status_code=401, detail="Invalid API Key format")


@router.get("/agents/{agent_id}/tasks")
async def get_agent_tasks(
    agent_id: int,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    agent: Agent = Depends(verify_agent_api_key),
    db: Session = Depends(get_db)
):
    """
    Query Agent's task list

    - **agent_id**: Agent ID
    - **status**: Filter by status (pending/in_progress/completed)
    - **limit**: Result limit
    - **offset**: Offset
    """
    # Verify Agent permission
    if agent.id != agent_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Build query
    query = db.query(Task)

    if status == "pending":
        # Pending: Open status and not accepted
        query = query.filter(Task.status == "Open", Task.agent_id == None)
    elif status == "in_progress":
        # In progress: Accepted by this agent but not completed
        query = query.filter(
            Task.agent_id == agent_id,
            Task.status.in_(["Accepted", "Submitted"])
        )
    elif status == "completed":
        # Completed
        query = query.filter(
            Task.agent_id == agent_id,
            Task.status.in_(["Completed", "Verified"])
        )
    else:
        # All tasks related to this agent
        query = query.filter(Task.agent_id == agent_id)

    # Pagination
    tasks = query.order_by(Task.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "tasks": [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "reward": task.reward,
                "timeout": task.timeout,
                "created_at": task.created_at.isoformat(),
                "accepted_at": task.accepted_at.isoformat() if task.accepted_at else None,
                "creator": {
                    "id": task.creator_id,
                    "username": task.creator.username if task.creator else None
                }
            }
            for task in tasks
        ],
        "total": query.count(),
        "limit": limit,
        "offset": offset
    }


@router.post("/tasks/{task_id}/accept")
async def accept_task(
    task_id: int,
    agent: Agent = Depends(verify_agent_api_key),
    db: Session = Depends(get_db)
):
    """
    Agent accepts task

    - **task_id**: Task ID
    """
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != "Open":
        raise HTTPException(status_code=400, detail="Task is not available")

    if task.agent_id is not None:
        raise HTTPException(status_code=400, detail="Task already accepted")

    # Accept task
    task.agent_id = agent.id
    task.status = "Accepted"
    task.accepted_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(task)

    return {
        "success": True,
        "message": "Task accepted successfully",
        "task": {
            "id": task.id,
            "status": task.status,
            "accepted_at": task.accepted_at.isoformat()
        }
    }


@router.post("/tasks/{task_id}/progress")
async def update_task_progress(
    task_id: int,
    progress: TaskProgress,
    agent: Agent = Depends(verify_agent_api_key),
    db: Session = Depends(get_db)
):
    """
    Update task progress

    - **task_id**: Task ID
    - **progress**: Progress (0-100)
    - **message**: Progress message
    """
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.agent_id != agent.id:
        raise HTTPException(status_code=403, detail="Not your task")

    if task.status not in ["Accepted", "Submitted"]:
        raise HTTPException(status_code=400, detail="Cannot update progress")

    # Update progress (need to add progress field to Task model)
    # task.progress = progress.progress
    # task.progress_message = progress.message

    db.commit()

    # TODO: Send real-time notification to task creator

    return {
        "success": True,
        "message": "Progress updated",
        "progress": progress.progress
    }


@router.post("/tasks/{task_id}/submit")
async def submit_task_result(
    task_id: int,
    submission: TaskSubmission,
    agent: Agent = Depends(verify_agent_api_key),
    db: Session = Depends(get_db)
):
    """
    Submit task result

    - **task_id**: Task ID
    - **result**: Task result
    - **files**: Attachment file list (optional)
    """
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.agent_id != agent.id:
        raise HTTPException(status_code=403, detail="Not your task")

    if task.status != "Accepted":
        raise HTTPException(status_code=400, detail="Task cannot be submitted")

    # Submit result
    task.result = submission.result
    task.status = "Submitted"
    task.submitted_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(task)

    # TODO: Notify task creator to verify result

    return {
        "success": True,
        "message": "Result submitted successfully",
        "task": {
            "id": task.id,
            "status": task.status,
            "submitted_at": task.submitted_at.isoformat()
        }
    }


@router.post("/agents/{agent_id}/generate-key")
async def generate_agent_api_key(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate Agent API Key

    - **agent_id**: Agent ID
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your agent")

    # Generate API Key
    import secrets
    random_part = secrets.token_urlsafe(32)
    api_key = f"nautilus_ak_{agent_id}_{random_part}"

    # TODO: Store hashed API Key in database

    return {
        "agent_id": agent_id,
        "api_key": api_key,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "warning": "Please keep this API Key safe, it will not be shown again"
    }
