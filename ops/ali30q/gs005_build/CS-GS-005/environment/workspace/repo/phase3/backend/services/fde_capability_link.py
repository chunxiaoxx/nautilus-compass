"""④ capability LINK(2026-06-22)· 让 5/21 起死的 capability_evolution 表真跑。

compass 7 齿轮实测:④结算+capability_evolution 双断(死表)。根因 = FDE producer 用
字符串 `claimed_by` claim,而 `capability_evolution`(整数键·接 survival/marketplace)
认 integer agent_id → 整数能力台账永远 0 行。

正道(V5 实测·**LINK 不 register**):字符串 claimed_by 别名到**整数注册身份**
(nautilus-prime-001=9000002·kairos=9000003·v7-telegram=9000004 都是真注册 agent·
别 register 新的造碎片身份),verdict settle 时喂现成 `record_task_outcome`(整数键)。
**复用现成能力系统不另造·不动 claim 历史·这是"让建好却没跑的架构真跑"。**

写点 = verdict ingest(服务端·有 models/db)·fail-soft(能力记账绝不炸 verdict 主链)。
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Callable, Optional

from sqlalchemy.orm import Session

from models.database import Agent
from services.capability_evolution import record_task_outcome

logger = logging.getLogger(__name__)

# V5 实测:这三个 producer 已是真注册整数身份(migration seed·真钱包·survival/governance)
DEFAULT_AGENT_ALIASES: dict[str, int] = {
    "nautilus-prime-001": 9000002,
    "kairos": 9000003,
    "v7-telegram": 9000004,
}


def normalize_claimed_by(claimed_by: Optional[str]) -> str | None:
    """Normalize claimed_by value for identity lookup."""
    if not claimed_by:
        return None
    identity = str(claimed_by).strip()
    if identity.startswith("expert:"):
        identity = identity[len("expert:"):].strip()
    return identity or None


def resolve_agent_id(
    db: Optional[Session],
    claimed_by: Optional[str],
    aliases: dict[str, int] = DEFAULT_AGENT_ALIASES,
) -> Optional[int]:
    """字符串 claimed_by → 整数注册 agent_id。

    顺序:① 已知别名(无需 db)② agents 表 name 精确匹配 ③ None(未知 producer·不臆造)。
    """
    claimed_by = normalize_claimed_by(claimed_by)
    if not claimed_by:
        return None
    if claimed_by in aliases:
        return aliases[claimed_by]
    if claimed_by.isdigit():
        return int(claimed_by)
    if db is not None:
        row = db.query(Agent).filter(Agent.name == claimed_by).first()
        if row is not None:
            return int(row.agent_id)
    return None


def derive_task_type(task: dict) -> str:
    """从 task(含 description spec)推能力 task_type(SWE→swe:{family}·否则 fde)。"""
    desc = task.get("description")
    if isinstance(desc, str) and desc.strip():
        try:
            spec = json.loads(desc)
        except (ValueError, TypeError):
            spec = None
        if isinstance(spec, dict):
            if spec.get("swe_instance_id"):
                return "swe:%s" % (spec.get("bench_family") or "swe")
            if spec.get("kb_problem_id") is not None:
                return "kernelbench"
            if spec.get("fde_class") is not None:
                return "fde:%s" % spec.get("fde_class")
    return "fde"


def _default_record_fn(db, agent_id, task_type, success, quality_score):
    """sync 上下文调 async record_task_outcome(body 实为 sync·ingest 端点在 threadpool)。"""
    asyncio.run(record_task_outcome(db, agent_id, task_type, success, quality_score))


def link_capability_from_verdict(
    db: Optional[Session],
    claimed_by: Optional[str],
    task_type: str,
    overall_pass: bool,
    score: float,
    aliases: dict[str, int] = DEFAULT_AGENT_ALIASES,
    record_fn: Optional[Callable] = None,
) -> Optional[dict]:
    """verdict settle → 解析 producer 整数身份 → 喂 capability_evolution。fail-soft。

    quality_score:verdict score(0-1)映射到 1-5 量纲(capability expert 门=avg≥4.5)。
    未知 producer → None(不记·不臆造)。
    """
    try:
        agent_id = resolve_agent_id(db, claimed_by, aliases)
        if agent_id is None:
            return None
        quality = round(float(score) * 5.0, 4)
        fn = record_fn or _default_record_fn
        fn(db, agent_id, task_type, bool(overall_pass), quality)
        return {"agent_id": agent_id, "task_type": task_type,
                "success": bool(overall_pass), "quality_score": quality}
    except Exception as exc:  # noqa: BLE001 — 能力记账绝不炸 verdict 主链
        logger.warning("capability link failed (non-fatal): %s", str(exc)[:200])
        return None
