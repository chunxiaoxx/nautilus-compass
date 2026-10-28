"""Agent service stubs."""
from sqlalchemy.orm import Session
from models.database import Agent
import logging

logger = logging.getLogger(__name__)

async def get_agent_cached(agent_id: int, db: Session) -> dict:
    # agent_id is the public 9000xxx identity; id is the internal PK. A lookup
    # by PK only made GET /api/agents/9000010 miss and 500 on None.
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if not agent:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        return None
    return {k: v for k, v in agent.__dict__.items() if not k.startswith("_")}

async def get_agents_list_cached(limit: int = 20, offset: int = 0, db: Session = None) -> dict:
    # Shape contract: the only caller (api/agents.py list_agents) reads
    # result["agents"]. Returning a bare list (as the a4c39c1d restore did)
    # made GET /api/agents 500 on every request.
    agents = db.query(Agent).offset(offset).limit(limit).all()
    return {"agents": [{k: v for k, v in a.__dict__.items() if not k.startswith("_")} for a in agents]}

def invalidate_agent_cache(agent_id: int):
    pass
