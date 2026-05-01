#!/usr/bin/env python3
"""Nautilus Compass HTTP / MCP-over-HTTP gateway.

Stateless gateway · delegates to BGE-m3 daemon (TCP 9876) · adds:
  · multi-tenant routing via X-Tenant-ID header → per-tenant anchor profile
  · MCP-over-HTTP (POST /mcp/tools/call · POST /mcp/tools/list · POST /mcp/initialize)
  · plain REST (POST /v1/recall · /v1/drift_check · /v1/feedback_log)
  · health probes (GET /healthz · /readyz)
  · request logging to .cache/gateway_access.jsonl

This is the entry point for Nautilus platform agents (Kairos · V5 · SuperAgent)
and external MCP clients that prefer HTTP over stdio.

Run:
   pip install fastapi uvicorn
   uvicorn compass_http:app --host 0.0.0.0 --port 8765 --workers 4

Or via Dockerfile / docker-compose (see ops/docker-compose.yml).
"""
from __future__ import annotations

import collections
import json
import os
import socket
import threading
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "nautilus-compass-gateway"
SERVER_VERSION = "0.7.2"

DAEMON_HOST = os.environ.get("COMPASS_DAEMON_HOST", "127.0.0.1")
DAEMON_PORT = int(os.environ.get("COMPASS_DAEMON_PORT", "9876"))
DAEMON_TIMEOUT = float(os.environ.get("COMPASS_DAEMON_TIMEOUT", "30"))
DEFAULT_TENANT = os.environ.get("COMPASS_DEFAULT_TENANT", "default")
PLUGIN_DIR = Path(__file__).resolve().parent
CACHE_DIR = PLUGIN_DIR / ".cache"
TENANT_ANCHOR_DIR = Path(os.environ.get("COMPASS_ANCHOR_DIR", str(PLUGIN_DIR)))
TENANTS_FILE = Path(os.environ.get(
    "COMPASS_TENANTS_FILE", str(PLUGIN_DIR / "tenants.json")))
# auth modes: "none" (no key check) · "header" (X-API-Key required when tenant has non-null key)
AUTH_MODE = os.environ.get("COMPASS_AUTH_MODE", "header").lower()


# ─── tenant config + rate limiting (in-memory · k8s autoscale will need redis) ───

_tenants_cache: dict = {"mtime": 0.0, "data": None}
_rate_buckets: dict = collections.defaultdict(collections.deque)
_rate_lock = threading.Lock()


def load_tenants() -> dict:
    """Reload tenants.json if file mtime changed · 0 cost on no-change."""
    if not TENANTS_FILE.exists():
        return {"tenants": {"default": {"api_key": None, "anchors_profile": "anchors.json", "rate_limit_per_min": 0}}}
    try:
        m = TENANTS_FILE.stat().st_mtime
        if _tenants_cache["data"] is not None and m == _tenants_cache["mtime"]:
            return _tenants_cache["data"]
        data = json.loads(TENANTS_FILE.read_text(encoding="utf-8"))
        _tenants_cache["mtime"] = m
        _tenants_cache["data"] = data
        return data
    except Exception:
        return _tenants_cache["data"] or {"tenants": {}}


def get_tenant_config(tenant: str) -> dict:
    cfg = load_tenants().get("tenants", {})
    return cfg.get(tenant, cfg.get("default", {}))


def authorize(tenant: str, api_key: str | None) -> dict:
    """Check API key · raise HTTPException on failure · return tenant config."""
    cfg = get_tenant_config(tenant)
    if not cfg:
        raise HTTPException(401, f"unknown tenant: {tenant}")
    expected = cfg.get("api_key")
    if AUTH_MODE == "none" or expected is None:
        return cfg
    if not api_key or api_key != expected:
        raise HTTPException(401, "invalid or missing X-API-Key")
    return cfg


def check_rate_limit(tenant: str, cfg: dict):
    """Sliding-window per-minute rate limit · 429 on exceed."""
    rpm = int(cfg.get("rate_limit_per_min", 0) or 0)
    if rpm <= 0:
        return
    now = time.time()
    cutoff = now - 60.0
    with _rate_lock:
        bucket = _rate_buckets[tenant]
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= rpm:
            raise HTTPException(429, f"rate limit exceeded ({rpm}/min for tenant={tenant})")
        bucket.append(now)


def resolve_anchors_path(cfg: dict) -> str | None:
    """Map tenant config → absolute anchors path passed to daemon."""
    profile = cfg.get("anchors_profile") or "anchors.json"
    candidate = TENANT_ANCHOR_DIR / profile
    if not candidate.exists():
        candidate = TENANT_ANCHOR_DIR / "anchors.json"
    return str(candidate.resolve()) if candidate.exists() else None

app = FastAPI(
    title="Nautilus Compass Gateway",
    version=SERVER_VERSION,
    description="MCP-over-HTTP gateway for Nautilus Compass · drift detection & memory recall",
)


# ─── daemon I/O ─────────────────────────────────────────────────────

def daemon_call(req: dict, timeout: float = DAEMON_TIMEOUT) -> dict:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((DAEMON_HOST, DAEMON_PORT))
        s.sendall((json.dumps(req) + "\n").encode("utf-8"))
        buf = b""
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
            if buf.endswith(b"\n"):
                break
        return json.loads(buf.decode("utf-8"))
    finally:
        s.close()


def resolve_tenant_anchors(tenant: str) -> Path | None:
    """Map tenant_id → anchors_<tenant>.json. Falls back to anchors.json."""
    candidate = TENANT_ANCHOR_DIR / f"anchors_{tenant}.json"
    if candidate.exists():
        return candidate
    default = TENANT_ANCHOR_DIR / "anchors.json"
    return default if default.exists() else None


def log_request(tenant: str, tool: str, ok: bool, latency_ms: int, extra: dict | None = None):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tenant": tenant,
        "tool": tool,
        "ok": ok,
        "latency_ms": latency_ms,
    }
    if extra:
        entry.update(extra)
    with open(CACHE_DIR / "gateway_access.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ─── pydantic models ───────────────────────────────────────────────

class RecallReq(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    project: str | None = Field(None, description="Memory dir under ~/.claude/projects/. Defaults via COMPASS_DEFAULT_PROJECT env.")
    top_k: int = Field(5, ge=1, le=50)


class DriftReq(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    project: str | None = None


class FeedbackReq(BaseModel):
    direction: str = Field(..., pattern="^(good|bad)$")
    reason: str = Field("", max_length=500)


class MCPToolCallReq(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


# ─── tool dispatch ─────────────────────────────────────────────────

def _resolve_project(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    env = os.environ.get("COMPASS_DEFAULT_PROJECT")
    if env:
        return env
    projects_dir = Path.home() / ".claude" / "projects"
    if not projects_dir.exists():
        return None
    best, best_mtime = None, 0.0
    for d in projects_dir.iterdir():
        mem = d / "memory"
        if not mem.is_dir():
            continue
        try:
            mtime = max((f.stat().st_mtime for f in mem.glob("*.md")), default=0)
        except Exception:
            mtime = 0
        if mtime > best_mtime:
            best, best_mtime = d.name, mtime
    return best


def do_recall(args: dict, tenant: str) -> dict:
    query = (args.get("query") or "").strip()
    if not query:
        raise HTTPException(400, "query required")
    project = _resolve_project(args.get("project"))
    if not project:
        raise HTTPException(400, "no project memory found · pass project= or set COMPASS_DEFAULT_PROJECT")
    top_k = int(args.get("top_k") or 5)
    try:
        res = daemon_call({"action": "recall", "query": query, "project": project, "top_k": top_k})
    except Exception as e:
        raise HTTPException(503, f"daemon unreachable: {e}")
    if not res.get("ok"):
        raise HTTPException(500, res.get("error", "daemon error"))
    return {
        "tenant": tenant,
        "project": project,
        "query": query[:80],
        "hits": res.get("recall", []),
        "fresh_extra": res.get("fresh_extra", []),
    }


def do_drift_check(args: dict, tenant: str, tenant_cfg: dict | None = None) -> dict:
    prompt = (args.get("prompt") or "").strip()
    if not prompt:
        raise HTTPException(400, "prompt required")
    project = _resolve_project(args.get("project")) or "C--Users-chunx"
    # v0.7.2 · per-tenant anchor profile: gateway resolves the absolute path
    # and passes it to daemon, which keeps a multi-profile cache.
    anchors_path = resolve_anchors_path(tenant_cfg or get_tenant_config(tenant))
    daemon_req = {"action": "drift", "query": prompt, "project": project, "top_k": 1}
    if anchors_path:
        daemon_req["anchors_path"] = anchors_path
    try:
        res = daemon_call(daemon_req)
    except Exception as e:
        raise HTTPException(503, f"daemon unreachable: {e}")
    if not res.get("ok"):
        raise HTTPException(500, res.get("error", "daemon error"))
    drift = res.get("drift") or {}
    return {
        "tenant": tenant,
        "score": drift.get("score"),
        "alignment": drift.get("alignment"),
        "deviation": drift.get("deviation"),
        "should_alert": drift.get("should_alert", False),
        "top_neg_hits": drift.get("top_neg_hits", []),
        "n_pos": drift.get("n_pos"),
        "n_neg": drift.get("n_neg"),
    }


def do_feedback_log(args: dict, tenant: str) -> dict:
    direction = (args.get("direction") or "").strip().lower()
    if direction not in ("good", "bad"):
        raise HTTPException(400, "direction must be 'good' or 'bad'")
    reason = (args.get("reason") or "").strip()[:500]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "http_gateway",
        "tenant": tenant,
        "direction": direction,
        "reason": reason,
    }
    log_path = CACHE_DIR / f"feedback_{tenant}.jsonl"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return {"logged": True, "tenant": tenant, "log": str(log_path.name)}


TOOL_FNS = {
    "recall": do_recall,
    "drift_check": do_drift_check,
    "feedback_log": do_feedback_log,
}

TOOL_SCHEMAS = [
    {
        "name": "recall",
        "description": "Semantic recall over project memory · BGE-m3 cosine top-k",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "project": {"type": "string"},
                "top_k": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "drift_check",
        "description": "Black-box persona drift detection · returns alignment/deviation/alert",
        "inputSchema": {
            "type": "object",
            "properties": {"prompt": {"type": "string"}, "project": {"type": "string"}},
            "required": ["prompt"],
        },
    },
    {
        "name": "feedback_log",
        "description": "Log good/bad signal for adaptive anchor retrain",
        "inputSchema": {
            "type": "object",
            "properties": {
                "direction": {"type": "string", "enum": ["good", "bad"]},
                "reason": {"type": "string"},
            },
            "required": ["direction"],
        },
    },
]


# ─── REST endpoints ────────────────────────────────────────────────

def _gate(tenant: str, api_key: str | None) -> dict:
    """Run auth + rate-limit · return tenant config or raise HTTPException."""
    cfg = authorize(tenant, api_key)
    check_rate_limit(tenant, cfg)
    return cfg


@app.post("/v1/recall")
def post_recall(
    req: RecallReq,
    x_tenant_id: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    tenant = x_tenant_id or DEFAULT_TENANT
    t0 = time.time()
    try:
        _gate(tenant, x_api_key)
        out = do_recall(req.model_dump(exclude_none=True), tenant)
        log_request(tenant, "recall", True, int((time.time() - t0) * 1000),
                    {"hits": len(out.get("hits", []))})
        return out
    except HTTPException:
        log_request(tenant, "recall", False, int((time.time() - t0) * 1000))
        raise


@app.post("/v1/drift_check")
def post_drift(
    req: DriftReq,
    x_tenant_id: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    tenant = x_tenant_id or DEFAULT_TENANT
    t0 = time.time()
    try:
        cfg = _gate(tenant, x_api_key)
        out = do_drift_check(req.model_dump(exclude_none=True), tenant, cfg)
        log_request(tenant, "drift_check", True, int((time.time() - t0) * 1000),
                    {"alert": out.get("should_alert"), "score": out.get("score"),
                     "profile": cfg.get("anchors_profile")})
        return out
    except HTTPException:
        log_request(tenant, "drift_check", False, int((time.time() - t0) * 1000))
        raise


@app.post("/v1/feedback_log")
def post_feedback(
    req: FeedbackReq,
    x_tenant_id: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    tenant = x_tenant_id or DEFAULT_TENANT
    t0 = time.time()
    try:
        _gate(tenant, x_api_key)
        out = do_feedback_log(req.model_dump(), tenant)
        log_request(tenant, "feedback_log", True, int((time.time() - t0) * 1000),
                    {"direction": req.direction})
        return out
    except HTTPException:
        log_request(tenant, "feedback_log", False, int((time.time() - t0) * 1000))
        raise


# ─── MCP-over-HTTP endpoints ───────────────────────────────────────

@app.post("/mcp/initialize")
def mcp_initialize():
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {"tools": {}},
        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
    }


@app.post("/mcp/tools/list")
def mcp_tools_list():
    return {"tools": TOOL_SCHEMAS}


@app.post("/mcp/tools/call")
def mcp_tools_call(
    req: MCPToolCallReq,
    x_tenant_id: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    tenant = x_tenant_id or DEFAULT_TENANT
    fn = TOOL_FNS.get(req.name)
    if not fn:
        raise HTTPException(404, f"unknown tool: {req.name}")
    t0 = time.time()
    try:
        cfg = _gate(tenant, x_api_key)
        # drift_check accepts cfg as 3rd arg · others ignore extras via kwargs check
        try:
            result = fn(req.arguments, tenant, cfg) if req.name == "drift_check" else fn(req.arguments, tenant)
        except TypeError:
            result = fn(req.arguments, tenant)
        log_request(tenant, req.name, True, int((time.time() - t0) * 1000))
        return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}
    except HTTPException as he:
        log_request(tenant, req.name, False, int((time.time() - t0) * 1000),
                    {"err": he.detail})
        return JSONResponse(
            status_code=he.status_code,
            content={"content": [{"type": "text", "text": f"Error: {he.detail}"}], "isError": True},
        )


# ─── health ─────────────────────────────────────────────────────────

@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": SERVER_NAME, "version": SERVER_VERSION}


@app.get("/readyz")
def readyz():
    """Daemon reachability probe · used by k8s readiness gate."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        s.connect((DAEMON_HOST, DAEMON_PORT))
        s.close()
        return {"status": "ready", "daemon": f"{DAEMON_HOST}:{DAEMON_PORT}"}
    except Exception as e:
        raise HTTPException(503, f"daemon not reachable: {e}")


@app.get("/")
def root():
    return {
        "service": SERVER_NAME,
        "version": SERVER_VERSION,
        "endpoints": {
            "rest": ["/v1/recall", "/v1/drift_check", "/v1/feedback_log"],
            "mcp": ["/mcp/initialize", "/mcp/tools/list", "/mcp/tools/call"],
            "health": ["/healthz", "/readyz"],
        },
        "auth": "X-Tenant-ID header (optional · defaults to 'default')",
        "daemon": f"{DAEMON_HOST}:{DAEMON_PORT}",
    }
