"""Soul service catalog · GET /api/discover/

Inc 3 Slice B Task B1. External callers (agents · scripts · LLM tool-use loops)
query this endpoint to enumerate platform soul capabilities without reading
source. Mirrors the OpenAI tool-discovery pattern but for the 3 currently
exposed soul services:

  * generate         · sync dry-run code gen + checks (no PR)
  * audit_generate   · sync dry-run + JSON-LD cert
  * dispatch         · async P2 task enqueue → daemon picks up via goal_stack

This is a NEW prefix (no co-tenant with /api/soul) so callers can probe
catalog freshness independent of soul auth.
"""
from __future__ import annotations

from fastapi import APIRouter


router = APIRouter()


_SOUL_SERVICES = [
    {
        "name": "generate",
        "method": "POST",
        "path": "/api/soul/generate",
        "auth": "X-Agent-Key",
        "description": "Dry-run code gen + checks (no writes, no PR). Returns cycle_id + files_planned.",
    },
    {
        "name": "audit_generate",
        "method": "POST",
        "path": "/api/soul/audit-generate",
        "auth": "X-Agent-Key",
        "description": "Dry-run code gen + JSON-LD HMAC cert (verifiable fidelity_score).",
    },
    {
        "name": "dispatch",
        "method": "POST",
        "path": "/api/soul/dispatch",
        "auth": "X-Agent-Key",
        "description": "Async enqueue task spec for daemon · P2 source in goal_stack. Returns cycle_id immediately.",
    },
]


@router.get("/")
async def discover():
    """Return the catalog of soul services platform exposes."""
    return {
        "success": True,
        "data": {
            "services": _SOUL_SERVICES,
            "count": len(_SOUL_SERVICES),
        },
        "error": None,
    }
