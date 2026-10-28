"""转移线④ · 权威能力喂点服务(2026-08-27)。

语义(对齐"自报不算"):capability_evolution 的 FDE 喂点**只跟 external-verify
权威转换走**;settle 自报口径旧喂点已下线;MISMATCH 失败面由 auto-verify runner
经 feed_capability_on_verify(success=False) 喂;历史由 backfill 一次性重建。

task_type 映射:task_uid 冒号前缀(g2b1:* → g2b1_code_repair),无冒号 → fde_misc。
quality 口径:score(0-1)×5(与 fde_capability_link 的 1-5 量纲一致)。
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_UID_TYPE_MAP = {"g2b1": "g2b1_code_repair"}


def task_type_from_uid(task_uid: str) -> str:
    uid = (task_uid or "").strip()
    if ":" in uid:
        prefix = uid.split(":", 1)[0].lower()
        return _UID_TYPE_MAP.get(prefix, prefix or "fde_misc")
    return "fde_misc"


def feed_capability_on_verify(
    db: Session,
    agent_id: int,
    task_uid: str,
    score: float,
    success: bool,
) -> Optional[dict]:
    """权威喂点:external-verify 转换(MATCH=success=True / MISMATCH=success=False)。

    fail-soft:能力记账绝不炸主链。同步调用(record_task_outcome 内部 commit)。
    """
    if not isinstance(agent_id, int):
        return None
    try:
        import asyncio
        from models.database import Agent
        from services.capability_evolution import record_task_outcome
        if db.query(Agent.agent_id).filter_by(agent_id=agent_id).first() is None:
            logger.warning("capability feed skip: agent %s not registered (ghost)", agent_id)
            return None  # FK 防御:幽灵身份不喂(云端实测 9000009 未注册)
        quality = round(float(score) * 5.0, 4)
        out = asyncio.run(record_task_outcome(
            db=db, agent_id=agent_id,
            task_type=task_type_from_uid(task_uid),
            success=bool(success), quality_score=quality,
        ))
        return out
    except Exception as exc:  # noqa: BLE001
        logger.warning("capability feed failed (non-fatal): %s", str(exc)[:200])
        return None


def feed_capability_failure_by_verdict(db: Session, verdict_id: str) -> Optional[dict]:
    """MISMATCH 失败面:按 verdict_id 取 producer/score 喂 success=False(auto-verify runner 用)。"""
    from models.fde_verdict import FdeVerdict

    row = db.query(FdeVerdict).filter_by(verdict_id=str(verdict_id)).first()
    if row is None:
        return None
    agent_id = (row.artifacts or {}).get("producer_agent_id")
    return feed_capability_on_verify(
        db, agent_id=agent_id, task_uid=str(row.task_uid),
        score=float(row.score or 0.0), success=False)


def backfill_capability_from_verified(db: Session) -> int:
    """一次性重建:遍历 external_verified=True 且 producer_agent_id 为整数的 verdict。

    ⚠️ 不幂等(重跑双计)——运维一次性动作,跑前快照、跑后以 attempts==verified 数验收。
    """
    from models.fde_verdict import FdeVerdict

    rows = db.query(FdeVerdict).filter(FdeVerdict.external_verified.is_(True)).all()
    n = 0
    for row in rows:
        art = row.artifacts or {}
        agent_id = art.get("producer_agent_id")
        if not isinstance(agent_id, int):
            continue
        out = feed_capability_on_verify(
            db, agent_id=agent_id, task_uid=str(row.task_uid),
            score=float(row.score or 0.0), success=True)
        if out is not None:
            n += 1
    logger.info("capability backfill: fed %d/%d verified verdicts", n, len(rows))
    return n
