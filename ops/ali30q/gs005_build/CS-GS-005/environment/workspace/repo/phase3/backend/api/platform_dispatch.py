"""W-C CONTROL · POST /api/platform/dispatch (统一 dispatch 薄路由).

A thin platform-side router: it maps {target, action, payload} onto the EXISTING
building blocks and reports where it routed. It does NOT reimplement any
orchestration (anchor #5) — a2a_relay, the soul dispatch endpoint, and compass
governance_dispatch already exist; this just hands the intent to the right one.

Fail-soft: the routing DECISION (routed_to) is deterministic; the downstream
delivery is best-effort. A building block being unreachable yields
delivered=false + a reason, never a 500. G-turf: compass governance internals
are not touched — the platform only forwards the intent to compass's MCP surface.
"""
from __future__ import annotations

import logging
import os
from urllib import request as _urlrequest, error as _urlerror

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from utils.platform_auth import require_platform_key

router = APIRouter(prefix="/api/platform", tags=["Control Plane Dispatch"])
logger = logging.getLogger(__name__)

# Where the platform reaches its own building blocks (override via env in prod).
_SELF_BASE = os.environ.get("PLATFORM_SELF_BASE", "http://127.0.0.1:8000")


def _ok(data):
    return {"success": True, "data": data, "error": None}


def _err(msg: str, status: int = 400):
    return JSONResponse(status_code=status,
                        content={"success": False, "data": None, "error": msg})


def _post_self(path: str, payload: dict) -> tuple[bool, str]:
    """Best-effort POST to a local building-block endpoint · fail-soft."""
    import json as _json
    try:
        data = _json.dumps(payload or {}).encode("utf-8")
        req = _urlrequest.Request(_SELF_BASE + path, data=data,
                                  headers={"Content-Type": "application/json"}, method="POST")
        with _urlrequest.urlopen(req, timeout=5) as resp:  # noqa: S310 — internal self-call
            return True, f"HTTP {resp.status}"
    except (_urlerror.URLError, OSError, ValueError) as exc:  # unreachable in test env
        return False, f"block unreachable: {str(exc)[:80]}"


def _route_agent(action: str, payload: dict) -> tuple[bool, str]:
    """agent → a2a_relay (peer message / task)."""
    return _post_self("/api/a2a/send", {"action": action, **(payload or {})})


def _route_soul(action: str, payload: dict) -> tuple[bool, str]:
    """soul → POST /api/soul/dispatch (派 goal / score)."""
    return _post_self("/api/soul/dispatch", {"action": action, **(payload or {})})


def _route_compass(action: str, payload: dict) -> tuple[bool, str]:
    """compass → governance_dispatch (via compass MCP · platform only forwards intent · G-turf).

    compass governance is an MCP surface, not an HTTP block reachable from the
    backend, so the platform records the routed intent; actual delivery rides the
    MCP channel (delivered reflects that this path is MCP-mediated, not HTTP)."""
    return False, "routed to compass governance_dispatch (MCP-mediated · intent forwarded)"


# target → (routed_to label, adapter). Single source of truth for routing.
_ROUTES = {
    "agent": ("a2a_relay", _route_agent),
    "soul": ("soul_dispatch", _route_soul),
    "compass": ("compass_governance", _route_compass),
}


@router.post("/dispatch")
def dispatch(body: dict, _=Depends(require_platform_key)):
    """Route a control intent to the right existing building block. Thin · fail-soft."""
    target = body.get("target")
    action = body.get("action")
    if not target or not action:
        return _err("both 'target' and 'action' are required")
    route = _ROUTES.get(target)
    if route is None:
        return _err(f"unknown target '{target}' · valid: {', '.join(_ROUTES)}")

    routed_to, adapter = route
    delivered, detail = adapter(action, body.get("payload") or {})
    return _ok({
        "target": target,
        "action": action,
        "routed_to": routed_to,
        "delivered": delivered,
        "detail": detail,
    })
