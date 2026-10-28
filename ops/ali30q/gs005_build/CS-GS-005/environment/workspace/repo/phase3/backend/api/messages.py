"""
Agent-to-Agent Message Channel API

GET  /api/messages/{agent_id}         — 收件箱（未读 + 最近）
POST /api/messages                    — 发送消息
GET  /api/messages/thread/{a}/{b}     — 两个 agent 之间的对话历史
POST /api/messages/{msg_id}/read      — 标记已读
GET  /api/messages/{agent_id}/unread  — 未读数
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, or_, and_
from sqlalchemy.orm import Session

from models.marketplace_models import AgentMessage, MessageStatus
from models.database import Agent
from utils.database import get_db

# 无硬前缀 · main.py 双前缀挂载(/api/messages 旧约定 + /api/platform/messages
# 平台约定)——V5 a2a settle 打的是平台前缀,7/7 之前一直 404(合约 settle_routes_404 根因)。
router = APIRouter(tags=["Agent Messages"])
logger = logging.getLogger(__name__)


class MessageSend(BaseModel):
    sender_id: int
    recipient_id: int
    message_type: str = "text"
    subject: Optional[str] = None
    body: str
    related_task_id: Optional[str] = None
    payment_amount: float = 0.0
    payment_token: str = "NAU"


def _msg_to_dict(msg: AgentMessage) -> dict:
    return {
        "id": msg.id,
        "sender_id": msg.sender_id,
        "recipient_id": msg.recipient_id,
        "message_type": msg.message_type,
        "subject": msg.subject,
        "body": msg.body,
        "related_task_id": msg.related_task_id,
        "payment_amount": msg.payment_amount,
        "payment_token": msg.payment_token,
        "status": msg.status.value if msg.status else "sent",
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
        "read_at": msg.read_at.isoformat() if msg.read_at else None,
    }


@router.get("/{agent_id}")
async def get_inbox(
    agent_id: int,
    unread_only: bool = Query(False),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """获取收件箱。"""
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    q = db.query(AgentMessage).filter(AgentMessage.recipient_id == agent_id)
    if unread_only:
        q = q.filter(AgentMessage.status == MessageStatus.SENT)

    total = q.count()
    msgs = q.order_by(desc(AgentMessage.created_at)).offset(offset).limit(limit).all()

    # Unread count
    unread = db.query(AgentMessage).filter(
        AgentMessage.recipient_id == agent_id,
        AgentMessage.status == MessageStatus.SENT,
    ).count()

    return {
        "success": True,
        "data": {
            "agent_id": agent_id,
            "messages": [_msg_to_dict(m) for m in msgs],
            "total": total,
            "unread": unread,
        },
    }


@router.post("", status_code=201)
async def send_message(payload: MessageSend, db: Session = Depends(get_db)):
    """发送 Agent-to-Agent 消息。"""
    sender = db.query(Agent).filter(Agent.agent_id == payload.sender_id).first()
    if not sender:
        raise HTTPException(status_code=404, detail="Sender agent not found")

    recipient = db.query(Agent).filter(Agent.agent_id == payload.recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient agent not found")

    if not payload.body.strip():
        raise HTTPException(status_code=400, detail="Message body cannot be empty")

    msg = AgentMessage(
        sender_id=payload.sender_id,
        recipient_id=payload.recipient_id,
        message_type=payload.message_type,
        subject=payload.subject,
        body=payload.body,
        related_task_id=payload.related_task_id,
        payment_amount=payload.payment_amount,
        payment_token=payload.payment_token,
        status=MessageStatus.SENT,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    logger.info("Message %d sent: agent %d → agent %d (%s)",
                msg.id, payload.sender_id, payload.recipient_id, payload.message_type)
    return {"success": True, "data": _msg_to_dict(msg)}


@router.get("/thread/{agent_a}/{agent_b}")
async def get_thread(
    agent_a: int,
    agent_b: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """获取两个 agent 之间的完整对话历史。"""
    msgs = (
        db.query(AgentMessage)
        .filter(
            or_(
                and_(AgentMessage.sender_id == agent_a, AgentMessage.recipient_id == agent_b),
                and_(AgentMessage.sender_id == agent_b, AgentMessage.recipient_id == agent_a),
            )
        )
        .order_by(desc(AgentMessage.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "success": True,
        "data": {
            "thread_between": [agent_a, agent_b],
            "messages": [_msg_to_dict(m) for m in reversed(msgs)],
            "count": len(msgs),
        },
    }


@router.post("/{msg_id}/read")
async def mark_read(msg_id: int, agent_id: int = Query(...), db: Session = Depends(get_db)):
    """标记消息已读。"""
    from datetime import datetime

    msg = db.query(AgentMessage).filter(
        AgentMessage.id == msg_id,
        AgentMessage.recipient_id == agent_id,
    ).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    msg.status = MessageStatus.READ
    msg.read_at = datetime.utcnow()
    db.commit()
    return {"success": True, "data": {"id": msg_id, "status": "read"}}


@router.get("/{agent_id}/unread")
async def unread_count(agent_id: int, db: Session = Depends(get_db)):
    """获取未读消息数。"""
    count = db.query(AgentMessage).filter(
        AgentMessage.recipient_id == agent_id,
        AgentMessage.status == MessageStatus.SENT,
    ).count()
    return {"success": True, "data": {"agent_id": agent_id, "unread": count}}
