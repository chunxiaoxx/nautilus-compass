"""
Skill Marketplace API

GET  /api/skills              — 浏览技能市集
POST /api/skills              — 注册技能（agent 操作）
GET  /api/skills/{slug}       — 技能详情
POST /api/skills/{slug}/hire  — 雇佣 agent 执行技能
GET  /api/skills/agent/{id}   — 某 agent 的技能列表
"""
import hashlib
import json
import logging
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, validator
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from models.marketplace_models import AgentSkill, SkillStatus
from models.database import Agent
from utils.database import get_db

router = APIRouter(prefix="/api/skills", tags=["Skill Marketplace"])
logger = logging.getLogger(__name__)


# ---------- Request / Response schemas ----------

class SkillCreate(BaseModel):
    agent_id: int
    name: str
    description: str
    task_type: str
    price_usdc: float = 0.0
    price_nau: float = 0.0
    input_schema: Optional[str] = None
    output_schema: Optional[str] = None
    example_input: Optional[str] = None
    example_output: Optional[str] = None

    @validator("name")
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    @validator("price_usdc", "price_nau")
    def price_non_negative(cls, v):
        if v < 0:
            raise ValueError("price cannot be negative")
        return v


class SkillHire(BaseModel):
    requester_agent_id: int
    input_data: Optional[dict] = None
    note: Optional[str] = None


def _slug_from_name(name: str, agent_id: int) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60]
    return f"{base}-{agent_id}"


def _skill_to_dict(skill: AgentSkill, include_agent: bool = False) -> dict:
    d = {
        "id": skill.id,
        "slug": skill.slug,
        "name": skill.name,
        "description": skill.description,
        "task_type": skill.task_type,
        "price_usdc": skill.price_usdc,
        "price_nau": skill.price_nau,
        "total_hires": skill.total_hires,
        "avg_rating": round(skill.avg_rating, 2),
        "success_rate": round(skill.success_rate, 3),
        "agent_id": skill.agent_id,
        "status": skill.status.value if skill.status else "active",
        "created_at": skill.created_at.isoformat() if skill.created_at else None,
    }
    if include_agent:
        d["input_schema"] = skill.input_schema
        d["output_schema"] = skill.output_schema
        d["example_input"] = skill.example_input
        d["example_output"] = skill.example_output
    return d


# ---------- Endpoints ----------

@router.get("")
async def list_skills(
    task_type: Optional[str] = Query(None),
    max_price_usdc: Optional[float] = Query(None, ge=0),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    sort: str = Query("hires", pattern="^(hires|rating|price_asc|price_desc|newest)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """浏览公开技能市集。"""
    q = db.query(AgentSkill).filter(AgentSkill.status == SkillStatus.ACTIVE)

    if task_type:
        q = q.filter(AgentSkill.task_type == task_type)
    if max_price_usdc is not None:
        q = q.filter(AgentSkill.price_usdc <= max_price_usdc)
    if min_rating is not None:
        q = q.filter(AgentSkill.avg_rating >= min_rating)

    order_map = {
        "hires": desc(AgentSkill.total_hires),
        "rating": desc(AgentSkill.avg_rating),
        "price_asc": AgentSkill.price_usdc,
        "price_desc": desc(AgentSkill.price_usdc),
        "newest": desc(AgentSkill.created_at),
    }
    q = q.order_by(order_map[sort])

    total = q.count()
    skills = q.offset(offset).limit(limit).all()

    # Aggregate stats
    stats = db.query(
        func.count(AgentSkill.id).label("total"),
        func.count(func.distinct(AgentSkill.agent_id)).label("agents"),
        func.count(func.distinct(AgentSkill.task_type)).label("categories"),
    ).filter(AgentSkill.status == SkillStatus.ACTIVE).first()

    return {
        "success": True,
        "data": {
            "items": [_skill_to_dict(s) for s in skills],
            "total": total,
            "offset": offset,
            "limit": limit,
            "market_stats": {
                "total_skills": stats.total if stats else 0,
                "total_agents": stats.agents if stats else 0,
                "total_categories": stats.categories if stats else 0,
            },
        },
    }


@router.post("", status_code=201)
async def register_skill(payload: SkillCreate, db: Session = Depends(get_db)):
    """Agent 注册新技能到市集。"""
    agent = db.query(Agent).filter(Agent.agent_id == payload.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    slug = _slug_from_name(payload.name, payload.agent_id)

    # Dedup: same agent + same name = update existing
    existing = db.query(AgentSkill).filter(AgentSkill.slug == slug).first()
    if existing:
        existing.description = payload.description
        existing.price_usdc = payload.price_usdc
        existing.price_nau = payload.price_nau
        existing.input_schema = payload.input_schema
        existing.output_schema = payload.output_schema
        existing.example_input = payload.example_input
        existing.example_output = payload.example_output
        existing.status = SkillStatus.ACTIVE
        db.commit()
        db.refresh(existing)
        return {"success": True, "data": _skill_to_dict(existing, include_agent=True), "updated": True}

    skill = AgentSkill(
        agent_id=payload.agent_id,
        name=payload.name,
        slug=slug,
        description=payload.description,
        task_type=payload.task_type,
        price_usdc=payload.price_usdc,
        price_nau=payload.price_nau,
        input_schema=payload.input_schema,
        output_schema=payload.output_schema,
        example_input=payload.example_input,
        example_output=payload.example_output,
    )
    # Compute ACP-compatible hash
    skill_content = f"{payload.name}|{payload.task_type}|{payload.description}"
    skill.acp_skill_hash = hashlib.sha256(skill_content.encode()).hexdigest()[:16]

    db.add(skill)
    db.commit()
    db.refresh(skill)
    logger.info("Skill registered: %s (agent %d)", slug, payload.agent_id)

    return {"success": True, "data": _skill_to_dict(skill, include_agent=True), "updated": False}


@router.get("/agent/{agent_id}")
async def get_agent_skills(
    agent_id: int,
    db: Session = Depends(get_db),
):
    """获取某 agent 的所有技能。"""
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    skills = (
        db.query(AgentSkill)
        .filter(AgentSkill.agent_id == agent_id, AgentSkill.status == SkillStatus.ACTIVE)
        .order_by(desc(AgentSkill.total_hires))
        .all()
    )
    return {
        "success": True,
        "data": {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "skills": [_skill_to_dict(s, include_agent=True) for s in skills],
        },
    }


@router.get("/{slug}")
async def get_skill(slug: str, db: Session = Depends(get_db)):
    """获取技能详情。"""
    skill = db.query(AgentSkill).filter(AgentSkill.slug == slug).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"success": True, "data": _skill_to_dict(skill, include_agent=True)}


@router.post("/{slug}/hire")
async def hire_skill(slug: str, payload: SkillHire, db: Session = Depends(get_db)):
    """
    雇佣 agent 执行技能。

    MVP 阶段：创建一个 academic task 并分配给技能所有者，返回 task_id。
    """
    from models.database import AcademicTask
    import uuid

    skill = db.query(AgentSkill).filter(
        AgentSkill.slug == slug,
        AgentSkill.status == SkillStatus.ACTIVE,
    ).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found or inactive")

    # Create a task for the skill execution
    task_id = f"skill_{uuid.uuid4().hex[:16]}"
    task = AcademicTask(
        task_id=task_id,
        title=f"Skill execution: {skill.name}",
        description=f"Hired via skill marketplace. Note: {payload.note or 'None'}",
        task_type=skill.task_type,
        status="open",
        assigned_agent_id=skill.agent_id,
        parameters=json.dumps(payload.input_data or {}),
        token_reward=skill.price_nau,
    )
    db.add(task)

    # Update hire count
    skill.total_hires = (skill.total_hires or 0) + 1
    db.commit()

    logger.info("Skill %s hired by agent %d, task %s", slug, payload.requester_agent_id, task_id)
    return {
        "success": True,
        "data": {
            "task_id": task_id,
            "skill_slug": slug,
            "agent_id": skill.agent_id,
            "price_usdc": skill.price_usdc,
            "price_nau": skill.price_nau,
        },
    }
