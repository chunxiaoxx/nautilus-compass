"""
OpenClaw Network API — Standard node endpoints for the OpenClaw peer protocol.

Exposes:
  GET  /api/openclaw/node/info                — node descriptor
  POST /api/openclaw/node/tasks               — receive external task (auth required)
  GET  /api/openclaw/node/tasks/{id}          — query task status (auth required)
  POST /api/openclaw/node/tasks/{id}/result   — submit/publish result (auth required)
  POST /api/openclaw/node/register            — register with external registry (auth required)
  GET  /api/openclaw/node/metrics             — node performance metrics (auth required)

Authentication: X-OpenClaw-Token header must match ADMIN_SECRET env var.
"""
import logging
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from services.openclaw_network import OpenClawNode, get_openclaw_node
from utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------

def _require_openclaw_token(
    x_openclaw_token: Optional[str] = Header(default=None, alias="X-OpenClaw-Token"),
) -> None:
    """Validate the shared bearer token used between OpenClaw nodes."""
    secret = os.environ.get("ADMIN_SECRET", "")
    if not secret:
        logger.error("ADMIN_SECRET not configured; blocking all node API access")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Node authentication not configured",
        )
    if not x_openclaw_token or x_openclaw_token != secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-OpenClaw-Token",
        )


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class ExternalTaskPayload(BaseModel):
    task_id: Optional[str] = Field(None, description="External task identifier")
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    task_type: str = Field(..., min_length=1, max_length=30)
    reward: Optional[str] = Field(None, description="Token reward amount")
    deadline: Optional[str] = Field(None, description="ISO-8601 deadline")
    callback_url: Optional[str] = Field(None, description="URL to receive result")
    source_node: Optional[str] = Field(None, description="Originating node ID")


class RegisterPayload(BaseModel):
    registry_url: str = Field(..., description="External OpenClaw registry base URL")


class ResultSubmitPayload(BaseModel):
    """Optional body when a peer submits a result directly to this node."""
    result_output: Optional[str] = None
    result_error: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(completed|failed)$")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/node/info", tags=["OpenClaw Network"])
async def node_info(
    node: OpenClawNode = Depends(get_openclaw_node),
) -> Dict[str, Any]:
    """Public node descriptor — no auth required."""
    return {"success": True, "data": node.get_node_info()}


@router.post("/node/tasks", tags=["OpenClaw Network"])
async def receive_external_task(
    payload: ExternalTaskPayload,
    db: Session = Depends(get_db),
    node: OpenClawNode = Depends(get_openclaw_node),
    _auth: None = Depends(_require_openclaw_token),
) -> Dict[str, Any]:
    """Receive an inbound task from a peer node and inject it into the queue."""
    internal_id = await node.receive_external_task(payload.model_dump(), db)
    return {
        "success": True,
        "data": {
            "internal_task_id": internal_id,
            "message": "Task accepted and queued",
        },
    }


@router.get("/node/tasks/{task_id}", tags=["OpenClaw Network"])
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db),
    node: OpenClawNode = Depends(get_openclaw_node),
    _auth: None = Depends(_require_openclaw_token),
) -> Dict[str, Any]:
    """Query the status of an injected external task by its internal ID."""
    # Accept both bare IDs and prefixed IDs
    internal_id = task_id if task_id.startswith("ocn-") else f"ocn-{task_id}"
    info = node.get_task_status(internal_id, db)
    if info is None:
        # Try bare id in case this was a native task
        info = node.get_task_status(task_id, db)
    if info is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    return {"success": True, "data": info}


@router.post("/node/tasks/{task_id}/result", tags=["OpenClaw Network"])
async def publish_task_result(
    task_id: str,
    db: Session = Depends(get_db),
    node: OpenClawNode = Depends(get_openclaw_node),
    _auth: None = Depends(_require_openclaw_token),
) -> Dict[str, Any]:
    """Push a completed task result to the registered callback or registry."""
    internal_id = task_id if task_id.startswith("ocn-") else f"ocn-{task_id}"
    result = await node.publish_result(internal_id, db)
    if not result.get("success"):
        # Degrade gracefully — return 200 with error details rather than 500
        logger.warning("publish_result degraded for %s: %s", internal_id, result.get("error"))
    return {"success": result.get("success", False), "data": result}


@router.post("/node/register", tags=["OpenClaw Network"])
async def register_with_registry(
    payload: RegisterPayload,
    node: OpenClawNode = Depends(get_openclaw_node),
    _auth: None = Depends(_require_openclaw_token),
) -> Dict[str, Any]:
    """Register this Nautilus node with an external OpenClaw registry."""
    result = await node.register_as_node(payload.registry_url)
    return {"success": result.get("success", False), "data": result}


@router.get("/node/metrics", tags=["OpenClaw Network"])
async def node_metrics(
    node: OpenClawNode = Depends(get_openclaw_node),
    _auth: None = Depends(_require_openclaw_token),
) -> Dict[str, Any]:
    """Return runtime performance metrics for this node."""
    return {"success": True, "data": node.metrics.to_dict()}
