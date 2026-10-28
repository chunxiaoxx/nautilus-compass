"""OrgMailbox · 跨框函件必达信箱(org/bootstrap P0 · SSOT §⓪-E 治"回函靠碰运气")。

设计 docs/plans/2026-08-28-org-bootstrap-design.md §3:
- 投递必带 trace_id+deadline(无 deadline 的闲聊函拒收——信箱不做垃圾场)
- 幂等:(trace_id, to_agent) 唯一
- supervisor 牙齿:notified_at 记录催办已发,同函不重复亮牌
"""
from __future__ import annotations

from sqlalchemy import JSON, Column, Integer, String, Text, DateTime, UniqueConstraint, func

from models.database import Base


class OrgMailbox(Base):
    __tablename__ = "org_mailbox"
    __table_args__ = (UniqueConstraint("trace_id", "to_agent", name="uq_mail_trace_to"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_agent = Column(String(64), nullable=False)
    to_agent = Column(String(64), nullable=False, index=True)
    trace_id = Column(String(128), nullable=False)
    title = Column(String(256), nullable=False)
    body = Column(Text, nullable=False, default="")
    deadline = Column(DateTime, nullable=False)
    # 时钟统一(2026-10-04 根修):utcnow(naive UTC)曾致模型路径函 created_at 早 8h
    # (writeback/frames_declare 实证),与 SQL 路径(DB now)两钟混列——改 func.now()
    # 全路径统一 DB 服务器钟。承 9/22 deadline utcnow 病残部(那轮只修了 send_letter)。
    created_at = Column(DateTime, server_default=func.now())
    ack_at = Column(DateTime, nullable=True, index=True)
    ack_note = Column(String(512), nullable=True)
    notified_at = Column(DateTime, nullable=True)  # supervisor 催办去重
    # 任务五件套(task_type/acceptance/deliverable_format/consumer/…),
    # 普通函为 None——任务=带验收判据的函,一切经 mailbox 总线(§⓪-E)
    task_meta = Column(JSON, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "from_agent": self.from_agent, "to_agent": self.to_agent,
            "trace_id": self.trace_id, "title": self.title, "body": self.body,
            "deadline": str(self.deadline),
            "created_at": str(self.created_at), "ack_at": str(self.ack_at) if self.ack_at else None,
            "ack_note": self.ack_note, "task_meta": self.task_meta,
        }
