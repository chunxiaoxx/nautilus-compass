"""
Skill Library API — CRUD and search for agent skills.
"""
from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, Field
from typing import Optional
import logging
import re

from skill_library.skill_manager import (
    save_skill, search_skills, list_skills, record_usage,
    get_agent_skills_context, build_extraction_prompt,
)
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)


class SkillCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=1000)
    procedure: str = Field(..., min_length=20, max_length=5000)
    input_schema: str = Field(default="", max_length=1000)
    output_schema: str = Field(default="", max_length=1000)
    tags: list[str] = Field(default_factory=list)
    quality_score: float = Field(default=7.0, ge=0, le=10)
    agent_id: Optional[int] = None
    source_bounty: Optional[str] = None
    depends_on: list[str] = Field(default_factory=list)


class SkillUsage(BaseModel):
    skill_id: str
    bounty_id: str
    agent_id: int
    score_after: Optional[float] = Field(None, ge=0, le=10)


@router.get("/skills", response_model=dict)
@limiter.limit("60/minute")
async def api_list_skills(
    request: Request,
    min_quality: float = Query(0.0, ge=0, le=10),
    limit: int = Query(50, ge=1, le=100),
):
    """List all skills in the library."""
    skills = list_skills(min_quality=min_quality, limit=limit)
    return {"success": True, "data": {"skills": skills, "total": len(skills)}, "error": None}


@router.get("/skills/search", response_model=dict)
@limiter.limit("60/minute")
async def api_search_skills(
    request: Request,
    q: str = Query(..., min_length=2, max_length=200),
    min_quality: float = Query(5.0, ge=0, le=10),
    limit: int = Query(5, ge=1, le=20),
):
    """Search skills by keyword."""
    results = search_skills(q, min_quality=min_quality, limit=limit)
    return {"success": True, "data": {"skills": results, "total": len(results)}, "error": None}


@router.post("/skills", response_model=dict, status_code=201)
@limiter.limit("30/minute")
async def api_create_skill(request: Request, skill: SkillCreate):
    """Create a new skill in the library."""
    # Generate skill ID from name
    slug = re.sub(r'[^a-z0-9]+', '_', skill.name.lower()).strip('_')[:50]
    skill_id = f"skill_{slug}_v1"

    save_skill(
        skill_id=skill_id,
        name=skill.name,
        description=skill.description,
        procedure=skill.procedure,
        input_schema=skill.input_schema,
        output_schema=skill.output_schema,
        tags=skill.tags,
        quality_score=skill.quality_score,
        agent_id=skill.agent_id,
        source_bounty=skill.source_bounty,
        depends_on=skill.depends_on,
    )

    logger.info(f"Skill created: {skill_id}")
    return {"success": True, "data": {"skill_id": skill_id, "name": skill.name}, "error": None}


@router.post("/skills/usage", response_model=dict)
@limiter.limit("60/minute")
async def api_record_usage(request: Request, usage: SkillUsage):
    """Record that a skill was used in a bounty."""
    record_usage(
        skill_id=usage.skill_id,
        bounty_id=usage.bounty_id,
        agent_id=usage.agent_id,
        score_after=usage.score_after,
    )
    return {"success": True, "data": {"recorded": True}, "error": None}


@router.get("/skills/context/{agent_id}", response_model=dict)
@limiter.limit("60/minute")
async def api_get_skills_context(
    request: Request,
    agent_id: int,
    task: str = Query(..., min_length=3, max_length=500),
    limit: int = Query(3, ge=1, le=10),
):
    """Get relevant skills context for an agent facing a new task."""
    context = get_agent_skills_context(agent_id, task, limit=limit)
    return {"success": True, "data": {"context": context}, "error": None}


@router.get("/skills/extraction-prompt", response_model=dict)
@limiter.limit("30/minute")
async def api_extraction_prompt(
    request: Request,
    title: str = Query(...),
    description: str = Query(...),
    output_summary: str = Query(default=""),
    score: int = Query(..., ge=1, le=10),
    feedback: str = Query(default=""),
):
    """Generate the skill extraction prompt for post-task processing."""
    prompt = build_extraction_prompt(title, description, output_summary, score, feedback)
    return {"success": True, "data": {"prompt": prompt}, "error": None}
