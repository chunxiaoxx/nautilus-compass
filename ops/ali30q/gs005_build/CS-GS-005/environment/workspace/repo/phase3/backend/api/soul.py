"""Soul API · shared self-modify capability endpoint.

POST /api/soul/generate — any authenticated agent submits a task spec; soul
generates code + runs checks (dry-run · no writes, no PR) and returns the result.

The apply/draft-PR path is via the queue consumer (soul_consumer), not this sync
endpoint. This endpoint is the synchronous wrapper over the same engine.ship().
"""
from __future__ import annotations
import hashlib
import os
import re
import uuid
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from utils.database import get_db

router = APIRouter()

# Inc 3 Slice B Task B2 · accepted task types for /dispatch.
# Each maps to a check pipeline shipped in Slice C (config) / Slice D (schema-migration).
DispatchTaskType = Literal["code", "config", "schema-migration"]


class GenerateRequest(BaseModel):
    task_spec: str = Field(..., min_length=20, max_length=10000)


class DispatchRequest(BaseModel):
    task_spec: str = Field(..., min_length=20, max_length=10000)
    task_type: DispatchTaskType = "code"


def _require_agent(x_agent_key: str, db: Session) -> int:
    """Resolve API key to agent_id, 401 if invalid. Mirrors openclaw auth."""
    from models.database import APIKey
    row = db.query(APIKey).filter(
        APIKey.key == x_agent_key, APIKey.is_active == True  # noqa: E712
    ).first()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid or expired API key")
    return row.agent_id


@router.post("/generate")
async def soul_generate(
    body: GenerateRequest,
    x_agent_key: str = Header(..., alias="X-Agent-Key"),
    db: Session = Depends(get_db),
):
    """Dry-run code generation + checks. No writes, no PR. Auth required."""
    agent_id = _require_agent(x_agent_key, db)
    from services.soul_service import generate
    base_dir = os.getenv("SOUL_WORKSPACE", ".")
    result = generate(body.task_spec, base_dir=base_dir, cycle_id=f"api-{agent_id}")
    return {
        "success": result["success"],
        "data": {
            "cycle_id": result["cycle_id"],
            "files_planned": result["files_planned"],
            "check_result": result["check_result"],
        },
        "error": None,
    }


@router.post("/audit-generate")
async def soul_audit_generate(
    body: GenerateRequest,
    x_agent_key: str = Header(..., alias="X-Agent-Key"),
    db: Session = Depends(get_db),
):
    """Dry-run generate + synchronous self-audit -> signed cert. No PR, no master writes.

    Returns the generated proposal plus a verify_certificate-valid JSON-LD cert
    carrying a real fidelity_score. The audit-subject rows persisted by run_self_audit
    are inert records (reward_nau=0, prefix soul-audit-api-). Auth required.
    """
    import time
    import uuid

    agent_id = _require_agent(x_agent_key, db)
    from services.soul_service import generate
    from services.soul_self_audit import run_self_audit

    base_dir = os.getenv("SOUL_WORKSPACE", ".")
    # uuid suffix → unique per call even for the same agent within one second
    cycle_id = f"api-{agent_id}-{int(time.time())}-{uuid.uuid4().hex[:8]}"

    try:
        gen = generate(body.task_spec, base_dir=base_dir, cycle_id=cycle_id, capture_content=True)
    except Exception as exc:  # LLM/provider/engine failure → clean degradation, not a 500 storm
        try:
            db.rollback()
        except Exception:
            pass
        return {"success": False, "data": {"cycle_id": cycle_id},
                "error": f"generation error: {type(exc).__name__}"}

    if not gen["success"]:
        return {
            "success": False,
            "data": {"cycle_id": cycle_id, "check_result": gen["check_result"]},
            "error": "generation checks failed",
        }

    # Fail closed: if no real generated content was captured, do NOT certify the prompt
    # text as if it were code (the fidelity score would be meaningless / misleading).
    contents = [f.get("content", "") for f in gen["files_planned"]]
    if not any(c.strip() for c in contents):
        return {
            "success": False,
            "data": {"cycle_id": cycle_id, "files_planned": gen["files_planned"],
                     "check_result": gen["check_result"]},
            "error": "no generated content captured to certify",
        }

    output = "\n\n".join(f"# {f['path']}\n{f.get('content', '')}" for f in gen["files_planned"])
    bounty_id = f"soul-audit-api-{cycle_id[4:]}"  # carries agent_id-ts-uuid → unique
    try:
        sa = run_self_audit(db, task_spec=body.task_spec, output=output, bounty_id=bounty_id)
    except Exception as exc:
        try:
            db.rollback()
        except Exception:
            pass
        return {"success": False, "data": {"cycle_id": cycle_id, "bounty_id": bounty_id},
                "error": f"self-audit error: {type(exc).__name__}"}

    return {
        "success": bool(sa.get("cert_valid")),
        "data": {
            "cycle_id": cycle_id,
            "files_planned": gen["files_planned"],
            "check_result": gen["check_result"],
            "fidelity_score": sa.get("fidelity_score"),
            "cert": sa.get("cert"),
            "cert_valid": sa.get("cert_valid"),
            "bounty_id": bounty_id,
        },
        "error": None if sa.get("cert_valid") else "cert verification failed",
    }


# ---------------------------------------------------------------------------
# Inc 3 Slice B Task B2 · POST /api/soul/dispatch · async P2 enqueue
# ---------------------------------------------------------------------------


def _insert_agent_dispatch_log(
    *, db: Session, agent_id: int, task_spec: str, task_spec_hash: str, task_type: str
) -> int:
    """INSERT one row into agent_dispatch_log · returns BIGSERIAL id.

    Fails closed if the table is missing (pre-Slice-A apply) — callers must
    surface that as 503. ship_outcome left NULL so daemon goal_stack P2 query
    picks it up on the next cycle.

    Slice B followup · task_spec (full text) is persisted alongside the hash
    so the daemon can read it back as the goal description for engine.ship().
    The b2c3d4e5f6a7 migration adds the column with a '' default, so this
    INSERT is safe even if the migration has not been applied (the row stores
    the spec; an older daemon ignores the column).
    """
    res = db.execute(
        text(
            "INSERT INTO agent_dispatch_log "
            "(agent_id, task_spec, task_spec_hash, task_type) "
            "VALUES (:aid, :spec, :hash, :tt) RETURNING id"
        ),
        {"aid": agent_id, "spec": task_spec, "hash": task_spec_hash, "tt": task_type},
    )
    new_id = res.scalar()
    db.commit()
    return int(new_id)


@router.post("/dispatch")
async def soul_dispatch(
    body: DispatchRequest,
    x_agent_key: str = Header(..., alias="X-Agent-Key"),
    db: Session = Depends(get_db),
):
    """Enqueue a task spec for the soul daemon · returns immediately with cycle_id.

    The daemon (Slice A wiring) reads pending rows via goal_stack.next_goal() at
    its next tick (2h default, sooner if pause_check absent). cycle_id format
    matches goal_stack P2: dispatch-<row_id>.
    """
    agent_id = _require_agent(x_agent_key, db)
    task_spec_hash = hashlib.sha256(body.task_spec.encode("utf-8")).hexdigest()[:64]
    try:
        row_id = _insert_agent_dispatch_log(
            db=db,
            agent_id=agent_id,
            task_spec=body.task_spec,
            task_spec_hash=task_spec_hash,
            task_type=body.task_type,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"agent_dispatch_log unavailable: {type(exc).__name__}",
        )
    return {
        "success": True,
        "data": {
            "cycle_id": f"dispatch-{row_id}",
            "queued": True,
            "task_type": body.task_type,
            "task_spec_hash": task_spec_hash,
        },
        "error": None,
    }


# ---------------------------------------------------------------------------
# Option B (2026-09-10 activation) · POST/GET /api/soul/proposals
# Closes the agent→soul queue loop (SOUL_PROPOSAL_CONTRACT_20260528 Option B):
# agents INSERT into `platform_proposals` (status='pending'), the scheduled
# soul_consumer ships each through gate→draft PR and writes the verdict back
# (status='reviewed' + resolution_note). Poll via the GET endpoint below.
# ---------------------------------------------------------------------------

_PROPOSAL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,63}$")


class SubmitProposalRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    proposed_change: str = Field(..., min_length=20, max_length=10000)
    target_agent: str = Field(..., min_length=1, max_length=128)
    rationale: str = Field("", max_length=2000)
    change_type: str = Field("code", max_length=32)
    proposal_id: Optional[str] = Field(None, max_length=64)


def _agent_display_name(db: Session, agent_id: int) -> str:
    """Resolve agent_id to its display name for the proposing_agent column."""
    try:
        from models.database import Agent
        row = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        if row is not None and getattr(row, "name", None):
            return str(row.name)[:128]
    except Exception:
        db.rollback()
    return f"agent-{agent_id}"


@router.post("/proposals")
async def soul_submit_proposal(
    body: SubmitProposalRequest,
    x_agent_key: str = Header(..., alias="X-Agent-Key"),
    db: Session = Depends(get_db),
):
    """Queue a coding proposal for the soul consumer. Returns the proposal_id
    to poll. Dedup on proposal_id; client-chosen ids allowed (unique key)."""
    agent_id = _require_agent(x_agent_key, db)
    proposal_id = body.proposal_id or f"pr-soul-{uuid.uuid4().hex[:12]}"
    if not _PROPOSAL_ID_RE.match(proposal_id):
        raise HTTPException(
            status_code=422,
            detail="proposal_id must match [A-Za-z0-9][A-Za-z0-9._-]{2,63}",
        )
    exists = db.execute(
        text("SELECT 1 FROM platform_proposals WHERE proposal_id = :p"),
        {"p": proposal_id},
    ).first()
    if exists:
        raise HTTPException(
            status_code=409, detail=f"proposal_id already exists: {proposal_id}"
        )
    db.execute(
        text(
            "INSERT INTO platform_proposals "
            "(proposal_id, proposing_agent, target_agent, title, rationale, "
            " proposed_change, change_type, status) "
            "VALUES (:pid, :pa, :ta, :ti, :ra, :pc, :ct, :st)"
        ),
        {
            "pid": proposal_id,
            "pa": _agent_display_name(db, agent_id),
            "ta": body.target_agent,
            "ti": body.title,
            "ra": body.rationale,
            "pc": body.proposed_change,
            "ct": body.change_type,
            "st": "pending",
        },
    )
    db.commit()
    return {
        "success": True,
        "data": {
            "proposal_id": proposal_id,
            "status": "pending",
            "poll": f"GET /api/soul/proposals/{proposal_id}",
        },
        "error": None,
    }


@router.get("/proposals/{proposal_id}")
async def soul_proposal_status(
    proposal_id: str,
    x_agent_key: str = Header(..., alias="X-Agent-Key"),
    db: Session = Depends(get_db),
):
    """Read back a proposal's verdict: status pending→reviewed and
    resolution_note (= draft PR url on success, gate-rejection detail else)."""
    _require_agent(x_agent_key, db)
    if not _PROPOSAL_ID_RE.match(proposal_id):
        raise HTTPException(status_code=422, detail="invalid proposal_id")
    row = db.execute(
        text(
            "SELECT proposal_id, status, resolution_note, resolved_by, resolved_at "
            "FROM platform_proposals WHERE proposal_id = :p"
        ),
        {"p": proposal_id},
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="proposal not found")
    return {
        "success": True,
        "data": {
            "proposal_id": row[0],
            "status": row[1],
            "resolution_note": row[2],
            "resolved_by": row[3],
            "resolved_at": row[4].isoformat() if row[4] else None,
        },
        "error": None,
    }
