"""
Agent Tool Registry API

GET  /api/tools               — 浏览工具注册表
POST /api/tools               — 注册工具（agent 操作）
GET  /api/tools/{slug}        — 工具详情
POST /api/tools/{slug}/call   — 代理调用工具（记录+转发）
GET  /api/tools/agent/{id}    — 某 agent 的工具列表
"""
import json
import logging
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, validator
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from models.marketplace_models import AgentTool, ToolCategory
from models.database import Agent
from utils.database import get_db

router = APIRouter(prefix="/api/tools", tags=["Tool Registry"])
logger = logging.getLogger(__name__)


class ToolCreate(BaseModel):
    agent_id: int
    name: str
    description: str
    category: str = "other"
    endpoint_url: Optional[str] = None
    http_method: str = "POST"
    auth_type: str = "api_key"
    request_schema: Optional[str] = None
    response_schema: Optional[str] = None
    price_per_call: float = 0.0

    @validator("category")
    def valid_category(cls, v):
        valid = {c.value for c in ToolCategory}
        if v not in valid:
            return "other"
        return v

    @validator("price_per_call")
    def price_non_negative(cls, v):
        if v < 0:
            raise ValueError("price cannot be negative")
        return v


class ToolCallRequest(BaseModel):
    caller_agent_id: int
    input_data: Optional[dict] = None


def _slug(name: str, agent_id: int) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60]
    return f"{base}-{agent_id}"


def _tool_to_dict(tool: AgentTool, full: bool = False) -> dict:
    d = {
        "id": tool.id,
        "slug": tool.slug,
        "name": tool.name,
        "description": tool.description,
        "category": tool.category.value if tool.category else "other",
        "price_per_call": tool.price_per_call,
        "total_calls": tool.total_calls,
        "is_active": tool.is_active,
        "agent_id": tool.agent_id,
        "http_method": tool.http_method,
        "auth_type": tool.auth_type,
        "created_at": tool.created_at.isoformat() if tool.created_at else None,
    }
    if full:
        d["endpoint_url"] = tool.endpoint_url
        d["request_schema"] = tool.request_schema
        d["response_schema"] = tool.response_schema
    return d


@router.get("")
async def list_tools(
    category: Optional[str] = Query(None),
    free_only: bool = Query(False),
    sort: str = Query("calls", pattern="^(calls|newest|price_asc)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """浏览工具注册表。"""
    q = db.query(AgentTool).filter(AgentTool.is_active == True)

    if category:
        q = q.filter(AgentTool.category == category)
    if free_only:
        q = q.filter(AgentTool.price_per_call == 0)

    order_map = {
        "calls": desc(AgentTool.total_calls),
        "newest": desc(AgentTool.created_at),
        "price_asc": AgentTool.price_per_call,
    }
    q = q.order_by(order_map[sort])

    total = q.count()
    tools = q.offset(offset).limit(limit).all()

    stats = db.query(
        func.count(AgentTool.id).label("total"),
        func.count(func.distinct(AgentTool.agent_id)).label("agents"),
        func.sum(AgentTool.total_calls).label("total_calls"),
    ).filter(AgentTool.is_active == True).first()

    category_counts = (
        db.query(AgentTool.category, func.count().label("cnt"))
        .filter(AgentTool.is_active == True)
        .group_by(AgentTool.category)
        .all()
    )

    return {
        "success": True,
        "data": {
            "items": [_tool_to_dict(t) for t in tools],
            "total": total,
            "offset": offset,
            "limit": limit,
            "registry_stats": {
                "total_tools": stats.total if stats else 0,
                "total_agents": stats.agents if stats else 0,
                "total_calls": int(stats.total_calls or 0) if stats else 0,
                "by_category": {c.value: cnt for c, cnt in category_counts},
            },
        },
    }


@router.post("", status_code=201)
async def register_tool(payload: ToolCreate, db: Session = Depends(get_db)):
    """Agent 注册新工具到注册表。"""
    agent = db.query(Agent).filter(Agent.agent_id == payload.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    slug = _slug(payload.name, payload.agent_id)

    existing = db.query(AgentTool).filter(AgentTool.slug == slug).first()
    if existing:
        for field in ["description", "category", "endpoint_url", "http_method",
                      "auth_type", "request_schema", "response_schema", "price_per_call"]:
            setattr(existing, field, getattr(payload, field))
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return {"success": True, "data": _tool_to_dict(existing, full=True), "updated": True}

    try:
        category_enum = ToolCategory(payload.category)
    except ValueError:
        category_enum = ToolCategory.OTHER

    tool = AgentTool(
        agent_id=payload.agent_id,
        name=payload.name,
        slug=slug,
        description=payload.description,
        category=category_enum,
        endpoint_url=payload.endpoint_url,
        http_method=payload.http_method,
        auth_type=payload.auth_type,
        request_schema=payload.request_schema,
        response_schema=payload.response_schema,
        price_per_call=payload.price_per_call,
    )
    db.add(tool)
    db.commit()
    db.refresh(tool)
    logger.info("Tool registered: %s (agent %d)", slug, payload.agent_id)
    return {"success": True, "data": _tool_to_dict(tool, full=True), "updated": False}


@router.get("/agent/{agent_id}")
async def get_agent_tools(agent_id: int, db: Session = Depends(get_db)):
    """获取某 agent 注册的所有工具。"""
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    tools = (
        db.query(AgentTool)
        .filter(AgentTool.agent_id == agent_id, AgentTool.is_active == True)
        .order_by(desc(AgentTool.total_calls))
        .all()
    )
    return {
        "success": True,
        "data": {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "tools": [_tool_to_dict(t, full=True) for t in tools],
        },
    }


@router.get("/{slug}")
async def get_tool(slug: str, db: Session = Depends(get_db)):
    """获取工具详情。"""
    tool = db.query(AgentTool).filter(AgentTool.slug == slug).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {"success": True, "data": _tool_to_dict(tool, full=True)}


@router.post("/{slug}/call")
async def call_tool(slug: str, payload: ToolCallRequest, db: Session = Depends(get_db)):
    """
    记录工具调用（+1 count），并返回端点信息供调用方直接请求。

    不代理实际请求（安全考虑）—— 调用方拿到端点后自行请求。
    """
    tool = db.query(AgentTool).filter(
        AgentTool.slug == slug,
        AgentTool.is_active == True,
    ).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found or inactive")

    tool.total_calls = (tool.total_calls or 0) + 1
    db.commit()

    logger.info("Tool %s called by agent %d", slug, payload.caller_agent_id)
    return {
        "success": True,
        "data": {
            "tool_slug": slug,
            "endpoint_url": tool.endpoint_url,
            "http_method": tool.http_method,
            "auth_type": tool.auth_type,
            "price_per_call": tool.price_per_call,
            "request_schema": tool.request_schema,
        },
    }
