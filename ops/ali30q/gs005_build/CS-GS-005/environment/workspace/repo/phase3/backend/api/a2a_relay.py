"""A2A Relay — authenticated inter-agent messaging with trust layer.

Security (2026-08-27 · 转移线⑤升级债①修复):
- 认证走注册体系 APIKey 表(x-api-key 同款):X-Agent-Token 必须是活跃 key,
  且 X-Agent-Name 与 key 所属 agent 的 name 一致(防冒名)。
- 未认证 401——旧版"标 ? 继续投递"的开放写入已封死。
- 收件人须为注册 agent(或系统名 nautilus),不再硬编码白名单。
- 旧 AGENT_SECRETS 明文字典已删除。零流量切换安全(云端五表 0 行 + 7 天 log 0 调用)。
"""
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.database import Agent, APIKey
from utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/a2a", tags=["A2A"])

# 系统名:非注册 agent 的本地投递目标(平台自身收件箱)
SYSTEM_RECIPIENTS = {"nautilus"}


def _authenticate(
    name: Optional[str],
    token: Optional[str],
    db: Session,
) -> Optional[Agent]:
    """X-Agent-Token → APIKey 表 → Agent;name 必须与 key 所属 agent 一致。"""
    name = (name or "").strip().lower()
    token = (token or "").strip()
    if not name or not token:
        return None
    key_obj = db.query(APIKey).filter(APIKey.key == token).first()
    if key_obj is None or not key_obj.is_active:
        return None
    agent = db.query(Agent).filter(Agent.agent_id == key_obj.agent_id).first()
    if agent is None or agent.name.strip().lower() != name:
        return None
    return agent


def _require_agent(
    x_agent_name: Optional[str],
    x_agent_token: Optional[str],
    db: Session,
) -> Agent:
    agent = _authenticate(x_agent_name, x_agent_token, db)
    if agent is None:
        raise HTTPException(status_code=401, detail="Invalid agent name/token")
    return agent


class A2AMessage(BaseModel):
    from_agent: str = ""
    to: str
    message: str


def _recipient_exists(to: str, db: Session) -> bool:
    if to in SYSTEM_RECIPIENTS:
        return True
    return db.query(Agent).filter(Agent.name == to).first() is not None


@router.post("/send")
async def send_message(
    msg: A2AMessage,
    request: Request,
    x_agent_name: Optional[str] = Header(None),
    x_agent_token: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    sender_agent = _require_agent(x_agent_name, x_agent_token, db)
    sender = sender_agent.name.strip().lower()
    to = msg.to.strip().lower()

    if not _recipient_exists(to, db):
        raise HTTPException(status_code=404, detail=f"Unknown target: {msg.to}")
    if to == sender:
        raise HTTPException(status_code=400, detail="Cannot message yourself")

    msg_id = f"a2a_{uuid.uuid4().hex[:12]}"
    rep = float(sender_agent.reputation or 0)
    envelope = f"[A2A {sender} ✓rep={rep:.0f}] {msg.message}"

    try:
        from utils.redis_client import get_redis
        get_redis().rpush(f"{to}:inbox", envelope)
    except Exception as e:  # noqa: BLE001 — redis 不可达时明确失败,不静默吞
        raise HTTPException(status_code=503, detail=f"relay unavailable: {e}")

    logger.info("A2A: %s → %s [%s]", sender, to, msg_id)
    return {"success": True, "message_id": msg_id, "from": sender,
            "to": to, "verified": True, "reputation": rep}


@router.get("/inbox/{agent_name}")
async def poll_inbox(
    agent_name: str,
    x_agent_name: Optional[str] = Header(None),
    x_agent_token: Optional[str] = Header(None),
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Poll and consume messages from an agent's inbox (agent itself only)."""
    agent = _require_agent(x_agent_name, x_agent_token, db)
    name = agent.name.strip().lower()
    if agent_name.strip().lower() != name:
        raise HTTPException(status_code=403, detail="Only the agent itself can poll its inbox")

    try:
        from utils.redis_client import get_redis
        r = get_redis()
        messages = []
        for _ in range(min(limit, 50)):
            m = r.lpop(f"{name}:inbox")
            if m is None:
                break
            messages.append(m if isinstance(m, str) else m.decode("utf-8"))
        return {"success": True, "messages": messages, "remaining": r.llen(f"{name}:inbox")}
    except Exception as e:  # noqa: BLE001
        return {"success": False, "error": str(e)}


@router.get("/agents")
async def list_agents(db: Session = Depends(get_db)):
    """List registered agents with inbox depth (no hardcoded names)."""
    agents = []
    try:
        from utils.redis_client import get_redis
        r = get_redis()
        for a in db.query(Agent).limit(50).all():
            agents.append({"name": a.name, "agent_id": a.agent_id,
                           "reputation": a.reputation or 0,
                           "inbox_pending": r.llen(f"{a.name.strip().lower()}:inbox")})
    except Exception:  # noqa: BLE001 — redis 挂了仍可列出身份
        for a in db.query(Agent).limit(50).all():
            agents.append({"name": a.name, "agent_id": a.agent_id,
                           "reputation": a.reputation or 0})
    return {"agents": agents}
