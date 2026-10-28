"""飞书决策卡 · 表模型(V5 设计稿 docs/plans/2026-08-29-feishu-decision-card-design.md · platform 实施)。

一次待拍板事项 = 一行;按钮回调落 choice;到期未决由 GET 读数时记 default。
"""
from __future__ import annotations

from datetime import datetime

from models.database import Base
from sqlalchemy import Boolean, Column, DateTime, Integer, Text


class FeishuDecision(Base):
    __tablename__ = "feishu_decisions"

    id = Column(Integer, primary_key=True)
    trace_id = Column(Text, unique=True, nullable=False, index=True)
    title = Column(Text, nullable=False)
    options_json = Column(Text, nullable=False)   # JSON 数组字符串
    default_choice = Column(Text, nullable=False)
    deadline = Column(DateTime, nullable=False)
    context = Column(Text, default="")
    card_sent = Column(Boolean, default=False)     # v0 未接卡片发送恒 False
    card_note = Column(Text, default="")           # 未发原因/回执说明
    choice = Column(Text, nullable=True)
    decided_at = Column(DateTime, nullable=True)
    decided_by = Column(Text, nullable=True)       # feishu-card | default
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        import json as _json
        return {
            "id": self.id, "trace_id": self.trace_id, "title": self.title,
            "options": _json.loads(self.options_json or "[]"),
            "default": self.default_choice,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "context": self.context or "",
            "card_sent": bool(self.card_sent), "card_note": self.card_note or "",
            "choice": self.choice,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "decided_by": self.decided_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
