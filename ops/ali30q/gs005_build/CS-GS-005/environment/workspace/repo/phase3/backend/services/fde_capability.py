"""FDE verify-side 能力回写 · 服务端 DB 层(2026-06-22)。

agent-first 能力路由的写端。FDE produce→verify 后,按 producer 身份(claimed_by)把
"是否产出合规格式 + 质量分"回写能力台账,V5 读端 earned_capabilities 据此路由
(谁能稳定产合规 swe-unified-diff → 派 SWE 燃料;kairos 产非 diff → 合规率降→不派)。

🔴 关键区分(V5 ack 接受):capability(格式合规)≠ quality(正确性方差)。
  - succeeded = 能产合规格式计数(diff 可解析·verifier 能跑),**非 F2P resolved**。
  - total_score = 累计质量分(供另算 quality·正确性方差是 V5 RSI turf·能力路由不碰)。

🔴 grounding(本 session·亲查生产库 + poller 环境):
  - 复用**现存** string-keyed 表 `platform_agent_capability_stats`(agent_id varchar128
    → 能存 "nautilus-prime-001"/"kairos")·表已存在(早期 bounty 路径遗留)·无 migration。
  - compass 当初建议复用的 `agent_capability_stats`(capability_evolution.py)是
    integer-agent-keyed(FK agents.agent_id·FDE producer 不是 Agent 行→接不上)。V5 指对了表。
  - vendored poller 进程**无 models/utils**→ 能力写不能进程内 DB(会崩 poller),走 HTTP:
    poller(纯 derive·见 fde_capability_logic)→ POST /api/platform/fde/capability → 本层 upsert。

纯归因逻辑见 services/fde_capability_logic(无 DB 依赖·poller 可 import)·此处 re-export 兼容。
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Callable, Optional

from sqlalchemy import Column, String, Integer, Float, DateTime
from sqlalchemy.orm import Session

from models.database import Base
# re-export 纯逻辑(向后兼容:既有 import 自 fde_capability 仍可用)
from services.fde_capability_logic import (  # noqa: F401
    classify_format,
    derive_capability,
    _skill_for,
)

logger = logging.getLogger(__name__)


class PlatformAgentCapabilityStat(Base):
    """映射现存 string-keyed 能力台账(无 migration·表已在生产库)。

    PK = (agent_id, task_type, skill_tag)(实测生产库 pkey)。
    """

    __tablename__ = "platform_agent_capability_stats"
    __table_args__ = {"extend_existing": True}

    agent_id = Column(String(128), primary_key=True)
    task_type = Column(String(64), primary_key=True)
    skill_tag = Column(String(128), primary_key=True, default="")
    attempts = Column(Integer, nullable=False, default=0)
    succeeded = Column(Integer, nullable=False, default=0)
    total_score = Column(Float, nullable=False, default=0.0)
    last_score = Column(Float, nullable=True)
    last_bounty_id = Column(String(64), nullable=True)
    last_at = Column(DateTime(timezone=True), nullable=True)


def record_capability(
    db: Session,
    agent_id: str,
    task_type: str,
    skill_tag: str,
    format_ok: bool,
    score: float,
    bounty_id: Optional[str] = None,
    now: Optional[datetime] = None,
) -> dict:
    """upsert (agent_id, task_type, skill_tag):attempts+1·succeeded+=合规·累计质量分。"""
    row = (
        db.query(PlatformAgentCapabilityStat)
        .filter_by(agent_id=agent_id, task_type=task_type, skill_tag=skill_tag)
        .first()
    )
    if row is None:
        row = PlatformAgentCapabilityStat(
            agent_id=agent_id, task_type=task_type, skill_tag=skill_tag,
            attempts=0, succeeded=0, total_score=0.0,
        )
        db.add(row)

    row.attempts = (row.attempts or 0) + 1
    if format_ok:
        row.succeeded = (row.succeeded or 0) + 1
    row.total_score = float(row.total_score or 0.0) + float(score)
    row.last_score = float(score)
    if bounty_id is not None:
        row.last_bounty_id = str(bounty_id)[:64]
    row.last_at = now or datetime.utcnow()

    db.commit()
    return {
        "agent_id": agent_id,
        "task_type": task_type,
        "skill_tag": skill_tag,
        "attempts": row.attempts,
        "succeeded": row.succeeded,
        "total_score": round(row.total_score, 4),
        "compliance_rate": round(row.succeeded / row.attempts, 4) if row.attempts else 0.0,
    }


def make_capability_fn(
    session_factory: Callable[[], Session],
    owns_session: bool = True,
) -> Callable[[dict, dict], None]:
    """进程内 DB 钩子(fail-soft)· **仅供有 models/utils 的进程**(如后端测试/请求作用域)。

    🔴 生产 poller(vendored 无 models)用 fde_bench_runner.make_http_capability_fn(走 HTTP)。
    """

    def capability_fn(task: dict, result: dict) -> None:
        try:
            d = derive_capability(task, result)
            if d is None:
                return
            db = session_factory()
            try:
                record_capability(
                    db, d["agent_id"], d["task_type"], d["skill_tag"],
                    format_ok=d["format_ok"], score=d["score"], bounty_id=d["bounty_id"],
                )
            finally:
                if owns_session:
                    db.close()
        except Exception as exc:  # noqa: BLE001 — 能力写绝不影响 verify 主链
            logger.warning("capability write failed (non-fatal): %s", str(exc)[:200])

    return capability_fn
