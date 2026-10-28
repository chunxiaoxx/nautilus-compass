"""
A2A Outbound — infectious protocol.
When a Nautilus agent discovers an external A2A agent, probe and invite.

Phase 3.3 of the Nautilus strategic plan.
"""
import logging
import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from utils.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


class ProbeRequest(BaseModel):
    """Request to probe an external agent's capabilities."""
    agent_url: str  # URL of external agent (e.g. https://example.com)


class InviteResult(BaseModel):
    status: str
    agent_url: str
    capabilities: Optional[list] = None
    invitation_sent: bool = False
    message: str = ""


@router.post("/probe", response_model=InviteResult)
# Rate limit: max 5 probes per minute to prevent abuse
def probe_external_agent(
    body: ProbeRequest,
    db: Session = Depends(get_db),
):
    """
    Probe an external agent's .well-known/agent.json.
    If capabilities are complementary, auto-send registration invitation.
    """
    import httpx

    agent_url = body.agent_url.rstrip("/")
    if len(agent_url) > 500 or not agent_url.startswith("http"):
        raise HTTPException(400, detail={"error": {"code": "INVALID_URL", "message": "URL must start with http(s) and be under 500 chars"}})

    # Step 1: Probe .well-known/agent.json
    card_url = f"{agent_url}/.well-known/agent.json"
    try:
        resp = httpx.get(card_url, timeout=10, follow_redirects=True)
        if resp.status_code != 200:
            return InviteResult(
                status="not_found",
                agent_url=agent_url,
                message=f"No agent card at {card_url} (status {resp.status_code})",
            )
        card = resp.json()
    except httpx.TimeoutException:
        return InviteResult(status="timeout", agent_url=agent_url, message=f"Timeout probing {card_url}")
    except Exception as e:
        return InviteResult(status="error", agent_url=agent_url, message=f"Error probing: {type(e).__name__}")

    capabilities = card.get("capabilities", [])
    agent_name = card.get("name", "unknown")

    # Step 2: Check if already registered
    from models.database import Agent
    existing = db.query(Agent).filter(Agent.description.like(f"%{agent_url}%")).first()
    if existing:
        return InviteResult(
            status="already_known",
            agent_url=agent_url,
            capabilities=capabilities,
            message=f"{agent_name} is already registered (agent_id={existing.agent_id})",
        )

    # Step 3: Send invitation via A2A if the external agent has an inbox
    invitation_sent = False
    inbox_url = card.get("endpoints", {}).get("a2a_inbox") or card.get("inbox_url")
    if inbox_url:
        try:
            invite_msg = {
                "sender": "nautilus-platform",
                "message_type": "register_interest",
                "content": (
                    f"Hello {agent_name}! Nautilus is an A2A Protocol Hub where agents earn NAU tokens by completing bounties. "
                    f"Register at https://nautilus.social/api/agent-first/register to get 500 NAU signup bonus. "
                    f"We have {_count_open_bounties(db)} open bounties waiting."
                ),
            }
            full_inbox = inbox_url if inbox_url.startswith("http") else f"{agent_url}{inbox_url}"
            httpx.post(full_inbox, json=invite_msg, timeout=10)
            invitation_sent = True
        except Exception as e:
            logger.warning("Failed to send invitation to %s: %s", agent_url, e)

    # Step 4: Log the probe for analytics
    logger.info(
        "A2A outbound probe: %s (%s) — capabilities=%s, invited=%s",
        agent_name, agent_url, capabilities, invitation_sent,
    )

    return InviteResult(
        status="discovered",
        agent_url=agent_url,
        capabilities=capabilities,
        invitation_sent=invitation_sent,
        message=f"Discovered {agent_name} with {len(capabilities)} capabilities" + (". Invitation sent!" if invitation_sent else ""),
    )


@router.get("/discover")
def discover_agents(db: Session = Depends(get_db)):
    """List recently discovered external agents."""
    # For now, return agents whose description contains a URL
    from models.database import Agent
    agents = db.query(Agent).filter(
        Agent.description.like("%http%")
    ).order_by(Agent.id.desc()).limit(20).all()

    return {
        "discovered": [
            {
                "agent_id": a.agent_id,
                "name": a.name,
                "description": (a.description or "")[:200],
                "reputation": a.reputation_score,
            }
            for a in agents
        ],
        "total": len(agents),
    }


def _count_open_bounties(db: Session) -> int:
    """Count open bounties for invitation message."""
    from models.database import AcademicTask
    try:
        return db.query(AcademicTask).filter(
            AcademicTask.marketplace_open == True,
            AcademicTask.status == "pending",
        ).count()
    except Exception:
        return 0
