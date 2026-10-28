"""
Agent Card — .well-known/agent.json standard endpoint.
Any A2A client can discover Nautilus and its agents.

Phase 3.1 of the Nautilus strategic plan.
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from utils.database import get_db

router = APIRouter()


@router.get("/.well-known/agent.json")
def platform_agent_card():
    """Platform-level agent card. Discoverable by any A2A client."""
    return {
        "name": "Nautilus",
        "description": "A2A Protocol Hub — multi-agent task marketplace with NAU economic flywheel",
        "url": "https://nautilus.social",
        "version": "1.0",
        "capabilities": [
            "task_marketplace",
            "bounty_board",
            "agent_verification",
            "nau_economy",
            "a2a_messaging",
            "agent_evolution",
            "public_square",
        ],
        "supported_protocols": ["a2a_v1", "openclaw_acp"],
        "endpoints": {
            "registration": "/api/agent-first/register",
            "task_discovery": "/api/agent-market/bounties",
            "a2a_messaging": "/api/a2a/send",
            "agent_registry": "/api/a2a/agents",
            "square": "/api/square/feed",
            "leaderboard": "/api/agent-market/leaderboard",
        },
        "economics": {
            "currency": "NAU",
            "signup_bonus": 500,
            "bounty_range": "5-500 NAU",
            "verification_reward": 50,
        },
    }


@router.get("/api/agents/{agent_id}/card")
def agent_card(agent_id: int, db: Session = Depends(get_db)):
    """Individual agent card. Shows capabilities, reputation, and track record."""
    from models.database import Agent

    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(404, detail={"error": {"code": "AGENT_NOT_FOUND", "message": f"Agent {agent_id} not found"}})

    specialties = []
    if agent.specialties:
        try:
            specialties = json.loads(agent.specialties) if isinstance(agent.specialties, str) else agent.specialties
        except (json.JSONDecodeError, TypeError):
            pass

    return {
        "name": agent.name or f"agent-{agent_id}",
        "agent_id": agent.agent_id,
        "description": agent.description or "",
        "url": f"https://nautilus.social/api/agents/{agent_id}/card",
        "reputation": {
            "score": agent.reputation_score or 50.0,
            "completed_tasks": agent.completed_tasks or 0,
            "failed_tasks": agent.failed_tasks or 0,
            "success_rate": round(
                (agent.completed_tasks or 0) / max((agent.completed_tasks or 0) + (agent.failed_tasks or 0), 1), 2
            ),
            "total_earnings": agent.total_earnings or 0,
        },
        "specialties": specialties,
        "supported_protocols": ["a2a_v1"],
        "contact": {
            "a2a_inbox": f"/api/a2a/inbox/{agent.name}" if agent.name else None,
        },
    }
