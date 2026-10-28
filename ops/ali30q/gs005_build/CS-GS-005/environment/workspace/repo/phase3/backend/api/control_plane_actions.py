"""Admin 控制层 · control_plane_actions(/control 指挥中心从只读升级为可控).

admin-email 白名单门控的后端 admin 控制模块。所有写动作走 admin 门
(`CONTROL_ADMIN_EMAILS` allowlist · fail-closed:allowlist 空 → 谁都不是 admin)。

复用现成 building block,不重造:
  - 路由复用 `api.platform_dispatch._ROUTES`(target→(routed_to_label, adapter))。
    这是统一 dispatch 的单一 source of truth · 我们只在前面加 admin 门 + 审计。
  - drill-down 读 `models.fde_verdict.FdeVerdict` / `models.database.Agent`。
  - `get_current_user` / `get_db` 复用 utils 既有依赖。

统一返回:`{success, data, error}`。错误用 HTTPException(FastAPI 自动 JSON)。
审计 fail-soft:`_audit` 找不到 emit 就 pass,绝不抛(写动作不能因审计失败而失败)。
"""
from __future__ import annotations

import logging
import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from utils.auth import get_current_user
from utils.database import get_db
from api.platform_dispatch import _ROUTES, _post_self

router = APIRouter(prefix="/api/platform/control-plane", tags=["Control Plane Admin"])
logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# 5. 统一返回 helper                                                          #
# --------------------------------------------------------------------------- #
def _ok(data) -> dict:
    return {"success": True, "data": data, "error": None}


# --------------------------------------------------------------------------- #
# 1. admin 白名单门控                                                          #
# --------------------------------------------------------------------------- #
def _admin_emails() -> set[str]:
    """读 env CONTROL_ADMIN_EMAILS(逗号分隔)→ 小写 set。每次调用即时读 env。"""
    raw = os.environ.get("CONTROL_ADMIN_EMAILS", "")
    return {p.strip().lower() for p in raw.split(",") if p.strip()}


def is_admin_user(user) -> bool:
    """allowlist 空 → False(fail-closed)。否则 {email, username} ∩ allowlist 非空 → True。"""
    allow = _admin_emails()
    if not allow:
        return False
    identities = set()
    email = getattr(user, "email", None)
    username = getattr(user, "username", None)
    if email:
        identities.add(str(email).lower())
    if username:
        identities.add(str(username).lower())
    return bool(identities & allow)


def require_admin(user=Depends(get_current_user)):
    """admin 门依赖:非 admin → 403。返回 user 供下游用。"""
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="admin only · not in CONTROL_ADMIN_EMAILS")
    return user


def _identity_of(user) -> str:
    """取一个可读身份串(email 优先,退 username)。"""
    return str(getattr(user, "email", None) or getattr(user, "username", None) or "")


# --------------------------------------------------------------------------- #
# 审计 · fail-soft 绝不抛                                                       #
# --------------------------------------------------------------------------- #
def _audit(kind: str, user, meta: dict) -> None:
    """记录一次 admin 控制动作。复用现成 emit;找不到/出错 → 静默 pass(fail-soft)。"""
    try:
        from engine.outcome_emit import emit_outcome  # 复用现成事件 emit
        emit_outcome({
            "kind": f"control_plane.{kind}",
            "actor": _identity_of(user),
            "meta": meta or {},
        })
    except Exception:  # noqa: BLE001 — 审计绝不能让写动作失败
        pass


# --------------------------------------------------------------------------- #
# whoami                                                                       #
# --------------------------------------------------------------------------- #
@router.get("/whoami")
def whoami(user=Depends(get_current_user)):
    """当前身份 + 是否 admin(前端据此决定显隐控制 UI)。任何已登录用户可调。"""
    return _ok({
        "is_admin": is_admin_user(user),
        "identity": _identity_of(user),
    })


# --------------------------------------------------------------------------- #
# 2. POST /dispatch(admin 门 · 复用 _ROUTES)                                  #
# --------------------------------------------------------------------------- #
def _do_dispatch(target: str, action: str, payload: dict, user) -> dict:
    """共享路由逻辑:校验 → 调 _ROUTES adapter → 审计 → 统一返回 data。"""
    if not target or not action:
        raise HTTPException(status_code=400, detail="both 'target' and 'action' are required")
    route = _ROUTES.get(target)
    if route is None:
        raise HTTPException(
            status_code=400,
            detail=f"unknown target '{target}' · valid: {', '.join(_ROUTES)}",
        )
    routed_to, adapter = route
    delivered, detail = adapter(action, payload or {})
    _audit("dispatch", user, {"target": target, "action": action, "delivered": delivered})
    return {
        "target": target,
        "action": action,
        "routed_to": routed_to,
        "delivered": delivered,
        "detail": detail,
    }


@router.post("/dispatch")
def dispatch(body: dict, user=Depends(require_admin)):
    """admin 把控制意图路由到正确的既有 building block(薄路由 · fail-soft)。"""
    data = _do_dispatch(body.get("target"), body.get("action"), body.get("payload") or {}, user)
    return _ok(data)


# --------------------------------------------------------------------------- #
# 3. POST /goal(admin · 派 goal 给 soul · 薄封装 dispatch)                    #
# --------------------------------------------------------------------------- #
@router.post("/goal")
def goal(body: dict, user=Depends(require_admin)):
    """派一个 goal 给 soul。薄封装 → target=soul · action=dispatch_goal。"""
    payload = dict(body.get("payload") or {})
    payload["goal"] = body.get("goal")
    data = _do_dispatch("soul", "dispatch_goal", payload, user)
    return _ok(data)


# --------------------------------------------------------------------------- #
# 4. drill-down GET(admin 门)                                                 #
# --------------------------------------------------------------------------- #
@router.get("/verdict/{verdict_id}")
def get_verdict(verdict_id: str, user=Depends(require_admin), db: Session = Depends(get_db)):
    """钻取一条 verdict 全量(含 per-item reason = 避坑知识)。缺 → 404。"""
    from models.fde_verdict import FdeVerdict
    v = db.query(FdeVerdict).filter(FdeVerdict.verdict_id == verdict_id).first()
    if v is None:
        raise HTTPException(status_code=404, detail=f"verdict '{verdict_id}' not found")
    return _ok(v.to_dict())


# --------------------------------------------------------------------------- #
# 6. 治理写交互代理(admin 门 · 复用现成 governance · 绝不重实现业务逻辑)        #
# --------------------------------------------------------------------------- #
@router.get("/governance/proposals")
def governance_proposals(user=Depends(require_admin), db: Session = Depends(get_db)):
    """admin 读治理提案/议会状态。复用现成 get_parliament_summary(in-process)。

    fail-soft:下游 service 缺表/列(测试沙箱 sqlite vs 生产 pg)→ 返回空占位 dict,
    绝不 500。返回的 data 即 parliament summary(含 proposal_stats/tier_distribution)。
    """
    try:
        from services.agent_parliament import get_parliament_summary
        summary = get_parliament_summary(db)
        if not isinstance(summary, dict):
            summary = {}
    except Exception as exc:  # noqa: BLE001 — fail-soft
        summary = {"unavailable": True, "detail": str(exc)[:120]}
    return _ok(summary)


@router.post("/governance/review")
def governance_review(body: dict, user=Depends(require_admin), db: Session = Depends(get_db)):
    """admin 审查/投票一个提案。decision∈{approve,reject}。

    复用现成治理 submit_peer_review(in-process)— 绝不重实现治理逻辑(anchor #5)。
    现成逻辑要 agent 身份(reviewer_id),admin 操作记录为服务端代行 → detail 透明标注
    admin 代行;下游 sqlite/pg 差异 → fail-soft(delivered=false)不抛。
    """
    proposal_id = body.get("proposal_id")
    decision = (body.get("decision") or "").strip().lower()
    if not proposal_id:
        raise HTTPException(status_code=400, detail="'proposal_id' is required")
    if decision not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="'decision' must be 'approve' or 'reject'")

    # approve→满分 / reject→0 分(映射到现成 peer_review 的 score 口径)。
    score = 5.0 if decision == "approve" else 0.0
    delivered, detail = False, ""
    try:
        from services.agent_parliament import submit_peer_review
        result = submit_peer_review(
            db,
            reviewer_id=str(_identity_of(user)),  # admin 代行身份(服务端记录)
            task_id=str(proposal_id),
            score=score,
            feedback=f"admin control-plane review · decision={decision}",
        )
        if isinstance(result, dict):
            delivered = bool(result.get("success"))
            detail = str(result.get("error") or result.get("new_rating") or "ok")[:160]
        else:
            detail = "review forwarded"
    except Exception as exc:  # noqa: BLE001 — fail-soft 下游不可达不抛
        delivered, detail = False, f"governance unreachable: {str(exc)[:120]}"

    _audit("governance_review", user,
           {"proposal_id": proposal_id, "decision": decision, "delivered": delivered})
    return _ok({
        "proposal_id": proposal_id,
        "decision": decision,
        "routed_to": "governance.submit_peer_review",
        "delivered": delivered,
        "detail": detail,
    })


# --------------------------------------------------------------------------- #
# 7. agent autonomy 代理(admin 门 · in-process 改 Agent.autonomy_enabled)      #
# --------------------------------------------------------------------------- #
@router.post("/agent/{agent_id}/autonomy")
def agent_autonomy(agent_id: int, body: dict, user=Depends(require_admin),
                   db: Session = Depends(get_db)):
    """admin 调一个 agent 的自治级别。in-process 改 Agent.autonomy_enabled(对齐
    api/agents.py POST /{agent_id}/autonomy 的真实语义)· 缺 agent → 404 · 审计。"""
    from models.database import Agent
    import models.agent_survival  # noqa: F401 — register mapper before query
    a = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if a is None:
        raise HTTPException(status_code=404, detail=f"agent '{agent_id}' not found")
    enabled = bool(body.get("enabled", False))
    a.autonomy_enabled = enabled
    db.commit()
    _audit("agent_autonomy", user, {"agent_id": agent_id, "enabled": enabled})
    return _ok({"agent_id": agent_id, "autonomy_enabled": enabled})


# --------------------------------------------------------------------------- #
# 8. task execute 代理(admin 门 · self-POST 转发现成 tasks execute · fail-soft) #
# --------------------------------------------------------------------------- #
@router.post("/task/{task_id}/execute")
def task_execute(task_id: int, user=Depends(require_admin)):
    """admin 触发一个任务执行。现成 tasks `POST /{task_id}/execute` 需 agent 鉴权 +
    引擎,不宜 in-process 直调 → self-POST 转发(复用 platform_dispatch._post_self 模式)。
    fail-soft:下游不可达/鉴权失败 → delivered=false 不 500 · 审计。"""
    delivered, detail = _post_self(f"/api/tasks/{task_id}/execute", {})
    _audit("task_execute", user, {"task_id": task_id, "delivered": delivered})
    return _ok({
        "task_id": task_id,
        "routed_to": "tasks.execute",
        "delivered": delivered,
        "detail": detail,
    })


@router.get("/agent/{agent_id}")
def get_agent(agent_id: int, user=Depends(require_admin), db: Session = Depends(get_db)):
    """钻取一个 agent 的基本字段。缺 → 404 · fail-soft(字段缺失不抛)。"""
    from models.database import Agent
    import models.agent_survival  # noqa: F401 — register mapper before query
    a = db.query(Agent).filter(Agent.id == agent_id).first()
    if a is None:
        raise HTTPException(status_code=404, detail=f"agent '{agent_id}' not found")
    out = {}
    for f in ("id", "agent_id", "name", "owner", "reputation", "tenant_id",
              "completed_tasks", "failed_tasks", "current_tasks"):
        try:
            out[f] = getattr(a, f, None)
        except Exception:  # noqa: BLE001 — fail-soft per field
            out[f] = None
    return _ok(out)
