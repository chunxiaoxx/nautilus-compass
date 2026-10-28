"""PlatformAudit · daemon 活性可观测(T1-A3 · 治双库分裂 #779)。

既有表(89054 行,prime-001 等直连写入);本模型=平台 API 写入路径,
让不连云 DB 的 worker(如本地主脑 ag_local_laptop_001)经端点亮活。
事件流语义:不幂等(调用方重试自担重复;如需去重后续加 event_id 列,禁过度工程预埋)。

列约束按生产实测对齐(2026-09-23 凌晨 NotNullViolation 修正:
除两 preview 外全列 NOT NULL;长度 actor128/actor_type32/action128/target256/target_type32/outcome16/ip64)。
"""
from __future__ import annotations

from sqlalchemy import JSON, BigInteger, Column, DateTime, Integer, String, Text

from models.database import Base


class PlatformAudit(Base):
    __tablename__ = "platform_audit"

    # PG=bigint(bigserial);sqlite 测试下 BigInteger 主键不自增,variant 落 Integer(ROWID)
    id = Column(BigInteger().with_variant(Integer, "sqlite"),
                primary_key=True, autoincrement=True)
    ts = Column(DateTime(timezone=True), nullable=False)   # 服务端时钟(禁客户端声明,防伪造时间线)
    actor = Column(String(128), nullable=False, index=True)
    actor_type = Column(String(32), nullable=False, default="unspecified")
    action = Column(String(128), nullable=False, index=True)
    target = Column(String(256), nullable=False, default="")
    target_type = Column(String(32), nullable=False, default="")
    outcome = Column(String(16), nullable=False)
    input_preview = Column(Text)
    output_preview = Column(Text)
    meta = Column("metadata", JSON, nullable=False, default=dict)  # 属性名避让 Declarative 保留字
    ip = Column(String(64), nullable=False)                 # 服务端记(request.client/X-Real-IP)

    def to_dict(self) -> dict:
        return {"id": self.id, "ts": str(self.ts) if self.ts else None,
                "actor": self.actor, "actor_type": self.actor_type,
                "action": self.action, "target": self.target,
                "target_type": self.target_type, "outcome": self.outcome,
                "input_preview": self.input_preview,
                "output_preview": self.output_preview,
                "metadata": self.meta, "ip": self.ip}
