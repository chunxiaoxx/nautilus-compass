"""A2A JSON-RPC 绑定 v0 — Google A2A v1.0.0 最小协议面(2026-09-12 对齐开工)。

POST /api/a2a/v1  speaks JSON-RPC 2.0 over HTTP (JSONRPC transport).

v0 范围(与 AgentCard capabilities 同步声明,禁虚标):
- tasks/get    :平台任务(AcademicTask)状态 → A2A 状态机映射
- tasks/cancel :非终态任务平台层取消(status='cancelled';终态→-32011)· Day2 2026-09-15
- message/send :文本投递 nautilus 系统收件箱(异步处理,以 agent Message 回执)
未实现的方法 → -32601(不静默假成功);streaming/push 见排期文档。

状态映射(AcademicTask.status → A2A TaskState):
pending→submitted, in_progress→working, needs_review→input-required,
completed→completed, failed→failed。未知平台状态拒绝映射(不伪造终态)。

版本协商:请求 A2A-Version 头缺省/1.x/0.3 放行,其余 VersionNotSupportedError;
响应恒带 A2A-Version: 1.0。
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from api.a2a import _get_agent_from_api_key
from models.database import AcademicTask
from utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/a2a", tags=["A2A Protocol"])

SUPPORTED_VERSION_MAJOR = "1"
LEGACY_VERSION = "0.3"

# JSON-RPC 2.0 标准错误码
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
# A2A 服务器错误域(-32000 ~ -32099)
TASK_NOT_FOUND = -32001
TASK_NOT_CANCELABLE = -32011
VERSION_NOT_SUPPORTED = -32004

PLATFORM_TO_A2A_STATE = {
    "pending": "submitted",
    "in_progress": "working",
    "needs_review": "input-required",
    "completed": "completed",
    "failed": "failed",
    "cancelled": "canceled",  # 2026-09-15:生产库已有该值(历史先例),补映射治 unmapped
}

# 平台终态(不可再取消;A2A 规范:终态任务 cancel → TaskNotCancelableError)
TERMINAL_STATES = {"completed", "failed", "cancelled"}


def _rpc_response(req_id, result=None, error=None) -> JSONResponse:
    body = {"jsonrpc": "2.0", "id": req_id}
    if error is not None:
        body["error"] = error
    else:
        body["result"] = result
    return JSONResponse(body, headers={"A2A-Version": "1.0"})


def _rpc_error(req_id, code: int, message: str) -> JSONResponse:
    return _rpc_response(req_id, error={"code": code, "message": message})


def _iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    return dt.replace(tzinfo=dt.tzinfo or timezone.utc).isoformat()


def _platform_task_to_a2a(t: AcademicTask) -> dict:
    state = PLATFORM_TO_A2A_STATE.get(t.status)
    if state is None:
        # 未知平台状态:拒绝映射而不是猜一个 A2A 态(禁伪造终态)
        raise ValueError(f"unmapped platform task status: {t.status!r}")
    task = {
        "id": t.task_id,
        "contextId": t.task_id,
        "status": {"state": state, "timestamp": _iso(t.updated_at or t.created_at)},
        "metadata": {"platform_status": t.status},
    }
    if t.status == "completed" and t.result_output:
        task["artifacts"] = [{
            "artifactId": f"{t.task_id}-result",
            "name": "result",
            "parts": [{"kind": "text", "text": t.result_output}],
        }]
    if t.status == "failed" and t.result_error:
        task["status"]["message"] = t.result_error
    return task


def _handle_tasks_get(params: dict, req_id, db: Session) -> JSONResponse:
    task_id = params.get("id")
    if not task_id:
        return _rpc_error(req_id, INVALID_PARAMS, "params.id is required")
    t = db.query(AcademicTask).filter(AcademicTask.task_id == str(task_id)).first()
    if t is None:
        return _rpc_error(req_id, TASK_NOT_FOUND, f"Task not found: {task_id}")
    try:
        return _rpc_response(req_id, result=_platform_task_to_a2a(t))
    except ValueError as exc:
        logger.error("tasks/get mapping failed for %s: %s", task_id, exc)
        return _rpc_error(req_id, INTERNAL_ERROR, str(exc))


def _handle_tasks_cancel(params: dict, req_id, db: Session) -> JSONResponse:
    """Day2(2026-09-15):非终态→平台层取消(出队不再结算,不强杀执行进程);
    终态→TaskNotCancelableError(-32011),不静默成功。"""
    task_id = params.get("id")
    if not task_id:
        return _rpc_error(req_id, INVALID_PARAMS, "params.id is required")
    t = db.query(AcademicTask).filter(AcademicTask.task_id == str(task_id)).first()
    if t is None:
        return _rpc_error(req_id, TASK_NOT_FOUND, f"Task not found: {task_id}")
    if t.status in TERMINAL_STATES:
        return _rpc_error(req_id, TASK_NOT_CANCELABLE,
                          f"Task {task_id} is in terminal state {t.status!r}; cannot cancel")
    t.status = "cancelled"
    db.commit()
    db.refresh(t)
    try:
        return _rpc_response(req_id, result=_platform_task_to_a2a(t))
    except ValueError as exc:
        logger.error("tasks/cancel mapping failed for %s: %s", task_id, exc)
        return _rpc_error(req_id, INTERNAL_ERROR, str(exc))


def _handle_message_send(params: dict, req_id, sender_name: str, reputation: float) -> JSONResponse:
    message = params.get("message") or {}
    text = " ".join(
        p.get("text", "") for p in message.get("parts", []) if p.get("kind") == "text"
    ).strip()
    if not text:
        return _rpc_error(req_id, INVALID_PARAMS,
                          "message.parts must contain at least one text part")
    # 信封格式与 api/a2a_relay.py 一致(digest 侧已认该格式)
    envelope = f"[A2A {sender_name} ✓rep={reputation:.0f}] {text}"
    try:
        from utils.redis_client import get_redis
        get_redis().rpush("nautilus:inbox", envelope)
    except Exception as e:  # noqa: BLE001 — redis 不可达时明确失败,不静默吞
        logger.error("message/send relay unavailable: %s", e)
        return _rpc_error(req_id, INTERNAL_ERROR, f"relay unavailable: {e}")
    return _rpc_response(req_id, result={
        "role": "agent",
        "messageId": f"msg_{uuid.uuid4().hex[:12]}",
        "parts": [{
            "kind": "text",
            "text": ("Message delivered to the Nautilus system inbox. "
                     "Processing is asynchronous; follow up via message/send."),
        }],
    })


@router.post(
    "/v1",
    summary="A2A JSON-RPC endpoint (spec v1.0.0)",
    description="JSON-RPC 2.0 binding. v0 implements tasks/get and message/send.",
)
async def a2a_jsonrpc(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> JSONResponse:
    agent = _get_agent_from_api_key(x_api_key, db)  # 401 on invalid key

    version = (request.headers.get("A2A-Version") or "").strip()
    if version and not version.startswith(SUPPORTED_VERSION_MAJOR) and version != LEGACY_VERSION:
        return _rpc_error(None, VERSION_NOT_SUPPORTED,
                          f"A2A-Version {version} not supported (supports 1.x, {LEGACY_VERSION})")

    try:
        body = await request.json()
    except Exception:
        return _rpc_error(None, PARSE_ERROR, "Parse error: body is not valid JSON")

    if not isinstance(body, dict) or body.get("jsonrpc") != "2.0" or "method" not in body:
        return _rpc_error(body.get("id") if isinstance(body, dict) else None,
                          INVALID_REQUEST, "Invalid JSON-RPC 2.0 request")

    req_id = body.get("id")
    method = body["method"]
    params = body.get("params") or {}

    if method == "tasks/get":
        return _handle_tasks_get(params, req_id, db)
    if method == "tasks/cancel":
        return _handle_tasks_cancel(params, req_id, db)
    if method == "message/send":
        rep = float(agent.reputation or 0)
        return _handle_message_send(params, req_id, agent.name.strip().lower(), rep)

    return _rpc_error(req_id, METHOD_NOT_FOUND, f"Method not found: {method}")
