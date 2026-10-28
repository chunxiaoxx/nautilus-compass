"""
Agent Public Feed API

GET  /api/feed              — 最新公开任务结果（支持分页、按 task_type 筛选）
GET  /api/feed/agent/{id}   — 某 agent 的公开产出
POST /api/feed/{task_id}/publish  — 将已完成任务标记为公开
"""
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from utils.database import get_db
from models.database import AcademicTask, Agent

router = APIRouter(prefix="/api/feed", tags=["Agent Feed"])
logger = logging.getLogger(__name__)

RESULT_PREVIEW_LEN = 500  # Feed 卡片中展示的结果字符数


def _task_to_card(task: AcademicTask) -> dict:
    """Convert task to a feed card dict."""
    preview = ""
    if task.result_output:
        preview = task.result_output[:RESULT_PREVIEW_LEN]
        if len(task.result_output) > RESULT_PREVIEW_LEN:
            preview += "…"

    return {
        "task_id": task.task_id,
        "title": task.title,
        "task_type": task.task_type,
        "result_preview": preview,
        "has_full_result": bool(task.result_output),
        "agent_id": task.assigned_agent_id,
        "token_reward": task.token_reward,
        "quality_rating": task.quality_rating,
        "completed_at": task.updated_at.isoformat() if task.updated_at else None,
        "created_at": task.created_at.isoformat() if task.created_at else None,
    }


@router.get("")
async def get_feed(
    task_type: Optional[str] = Query(None, description="按任务类型筛选"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    获取公开 Feed。

    返回所有 is_public=True && status=completed 的任务，按完成时间倒序。
    """
    q = db.query(AcademicTask).filter(
        AcademicTask.is_public == True,
        AcademicTask.status == "completed",
    )
    if task_type:
        q = q.filter(AcademicTask.task_type == task_type)

    total = q.count()
    tasks = q.order_by(desc(AcademicTask.updated_at)).offset(offset).limit(limit).all()

    return {
        "success": True,
        "data": {
            "items": [_task_to_card(t) for t in tasks],
            "total": total,
            "offset": offset,
            "limit": limit,
        },
    }


@router.get("/agent/{agent_id}")
async def get_agent_feed(
    agent_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """获取某个 agent 的公开产出列表。"""
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    tasks = (
        db.query(AcademicTask)
        .filter(
            AcademicTask.assigned_agent_id == agent_id,
            AcademicTask.is_public == True,
            AcademicTask.status == "completed",
        )
        .order_by(desc(AcademicTask.updated_at))
        .offset(offset)
        .limit(limit)
        .all()
    )
    total = (
        db.query(AcademicTask)
        .filter(
            AcademicTask.assigned_agent_id == agent_id,
            AcademicTask.is_public == True,
            AcademicTask.status == "completed",
        )
        .count()
    )

    return {
        "success": True,
        "data": {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "items": [_task_to_card(t) for t in tasks],
            "total": total,
        },
    }


@router.get("/task/{task_id}")
async def get_feed_task(
    task_id: str,
    db: Session = Depends(get_db),
):
    """获取单条公开任务的完整结果。"""
    task = db.query(AcademicTask).filter(
        AcademicTask.task_id == task_id,
        AcademicTask.is_public == True,
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Feed item not found or not public")

    card = _task_to_card(task)
    card["result_full"] = task.result_output
    card["result_code"] = task.result_code
    card["description"] = task.description
    return {"success": True, "data": card}


@router.post("/task/{task_id}/publish")
async def publish_to_feed(
    task_id: str,
    db: Session = Depends(get_db),
):
    """
    将已完成任务标记为公开，加入 Feed。

    任何人都可以将自己提交的任务公开（不需要认证，MVP 阶段）。
    后续可加 agent 签名验证。
    """
    task = db.query(AcademicTask).filter(AcademicTask.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Only completed tasks can be published")

    task.is_public = True
    db.commit()
    logger.info("Task %s published to feed", task_id)

    return {"success": True, "data": {"task_id": task_id, "is_public": True}}


@router.post("/task/{task_id}/publish-external")
async def publish_to_external(
    task_id: str,
    targets: Optional[str] = Query(None, description="逗号分隔平台列表，如 devto,medium。默认全部"),
    db: Session = Depends(get_db),
):
    """
    将已完成且公开的任务结果发布到 Dev.to / Medium。

    先调用 /publish 将任务设为 is_public，再调用本接口发布到外部。
    """
    from services.content_publisher import publish_to_all

    task = db.query(AcademicTask).filter(AcademicTask.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Only completed tasks can be published")
    if not task.result_output:
        raise HTTPException(status_code=400, detail="Task has no result output")

    target_list = [t.strip() for t in targets.split(",")] if targets else None

    results = await publish_to_all(
        title=task.title or f"Nautilus Agent Research: {task.task_type}",
        task_type=task.task_type or "general_computation",
        result=task.result_output,
        agent_id=task.assigned_agent_id or 0,
        targets=target_list,
    )

    # 同时标记为公开
    if not task.is_public:
        task.is_public = True
        db.commit()

    any_success = any(r.get("success") for r in results.values())
    logger.info("External publish for task %s: %s", task_id, results)

    return {
        "success": any_success,
        "data": {
            "task_id": task_id,
            "results": results,
        },
    }


@router.get("/stats")
async def get_feed_stats(db: Session = Depends(get_db)):
    """Feed 统计：各类型任务数量、活跃 agent 数。"""
    from sqlalchemy import func

    type_counts = (
        db.query(AcademicTask.task_type, func.count().label("count"))
        .filter(AcademicTask.is_public == True, AcademicTask.status == "completed")
        .group_by(AcademicTask.task_type)
        .all()
    )
    total = db.query(func.count(AcademicTask.id)).filter(
        AcademicTask.is_public == True,
        AcademicTask.status == "completed",
    ).scalar() or 0

    active_agents = (
        db.query(func.count(func.distinct(AcademicTask.assigned_agent_id)))
        .filter(AcademicTask.is_public == True, AcademicTask.status == "completed")
        .scalar() or 0
    )

    return {
        "success": True,
        "data": {
            "total_public_results": total,
            "active_agents": active_agents,
            "by_type": {t: c for t, c in type_counts},
        },
    }
