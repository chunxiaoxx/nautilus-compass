"""FDE 能力台账 ingest API · POST/GET /api/platform/fde/capability(2026-06-22)。

🔴🔴 非系统依赖(2026-06-22 用户战略纠正):本端点 key 在 producer 字符串身份(claimed_by·
含对话框 kairos/v7-telegram)。用户定:**Claude Code 对话框不该计入系统**(ephemeral·不可依赖)·
系统 producer 必须是**注册自主 agent**(agent_first_register→整数 agent_id),能力跟踪用**现成
integer-keyed `capability_evolution`**(和 marketplace/survival 同一套·非本 string-keyed 表)。
本端点 fail-soft 留着(零危害)但 **别在它上面建读端/依赖** · 正道见 _OUTBOUND..._CORRECTION_
producers_must_be_registered_agents。producer 注册化落地后本套自然淘汰。


verify-side 能力回写的服务端写点。poller(vendored 无 models/utils)derive 出归因记录
后 POST 这里;本端点 upsert platform_agent_capability_stats(string-keyed)。V5 路由读端
earned_capabilities 从同一表读。架构镜像 fde_verdict(poller=瘦 HTTP 客户端·写在服务端)。

capability(格式合规)≠ quality(正确性方差)。succeeded=格式合规计数·total_score=累计质量分。
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from utils.database import get_db
from services.fde_capability import record_capability, PlatformAgentCapabilityStat

router = APIRouter(prefix="/api/platform/fde", tags=["FDE Capability Ledger"])
logger = logging.getLogger(__name__)

_REQUIRED = ("agent_id", "task_type", "skill_tag", "format_ok", "score")


def _ok(data):
    return {"success": True, "data": data, "error": None}


def _err(msg: str, status: int = 400):
    return JSONResponse(status_code=status,
                        content={"success": False, "data": None, "error": msg})


@router.post("/capability")
def ingest_capability(body: dict, request: Request, db=Depends(get_db)):
    """回写一条 producer 能力归因(upsert by agent_id+task_type+skill_tag)。"""
    from api.org import _auth_check  # 2026-10-11 收口⑫:能力归因入口绑定
    denied = _auth_check(db, request, str(body.get("agent_id", "")))
    if denied:
        return denied
    missing = [k for k in _REQUIRED if body.get(k) is None]
    if missing:
        return _err(f"missing required field(s): {', '.join(missing)}")
    try:
        score = float(body["score"])
    except (TypeError, ValueError):
        return _err("score must be a number")

    try:
        out = record_capability(
            db,
            agent_id=str(body["agent_id"]),
            task_type=str(body["task_type"]),
            skill_tag=str(body["skill_tag"]),
            format_ok=bool(body["format_ok"]),
            score=score,
            bounty_id=body.get("bounty_id"),
        )
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.warning("capability ingest failed: %s", str(exc)[:200])
        return _err("capability persistence failed", status=500)
    return _ok(out)


@router.get("/capability/{agent_id}")
def get_capabilities(agent_id: str, db=Depends(get_db)):
    """读回某 producer 的能力台账行(V5 路由读端可用·或调试)。"""
    rows = (
        db.query(PlatformAgentCapabilityStat)
        .filter_by(agent_id=agent_id)
        .order_by(PlatformAgentCapabilityStat.attempts.desc())
        .all()
    )
    data = [
        {
            "agent_id": r.agent_id,
            "task_type": r.task_type,
            "skill_tag": r.skill_tag,
            "attempts": r.attempts,
            "succeeded": r.succeeded,
            "total_score": round(r.total_score or 0.0, 4),
            "compliance_rate": round(r.succeeded / r.attempts, 4) if r.attempts else 0.0,
            "last_score": r.last_score,
            "last_at": r.last_at.isoformat() if r.last_at else None,
        }
        for r in rows
    ]
    return _ok(data)
