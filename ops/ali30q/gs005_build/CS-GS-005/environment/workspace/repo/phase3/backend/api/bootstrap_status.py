"""
Bootstrap feedback-loop API endpoints.

Provides monitoring and manual triggering of the task quality feedback loop:
- GET  /api/bootstrap-loop/status  - current metrics and trend
- POST /api/bootstrap-loop/run     - trigger one analysis cycle
- GET  /api/bootstrap-loop/history - past cycle reports
"""
import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from services.bootstrap_loop import BootstrapLoop
from utils.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

TESTING = os.getenv("TESTING", "false").lower() == "true"
limiter = Limiter(key_func=get_remote_address, enabled=not TESTING)


class RunCycleRequest(BaseModel):
    """Request body for triggering a feedback cycle."""
    days: int = Field(default=7, ge=1, le=90, description="Number of days to analyze")


@router.get("/status")
@limiter.limit("30/minute")
async def bootstrap_loop_status(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get current bootstrap feedback-loop metrics.

    Returns aggregate success-rate trend from past cycles.
    """
    try:
        loop = BootstrapLoop(db)
        metrics = loop.get_metrics()
        return {"success": True, "data": metrics}
    except Exception as e:
        logger.error("bootstrap-loop status error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run")
@limiter.limit("5/minute")
async def bootstrap_loop_run(
    request: Request,
    body: RunCycleRequest = RunCycleRequest(),
    db: Session = Depends(get_db),
):
    """
    Trigger one feedback-loop cycle manually.

    Analyzes tasks from the last N days, identifies failure patterns,
    and suggests template improvements.

    **Rate Limit**: 5 requests per minute
    """
    from api.org import _auth_check  # 2026-10-11 追补②孪生端点收口(主域 405 实测可达,预检报告§三更正)
    denied = _auth_check(db, request, "platform")
    if denied:
        return denied
    try:
        loop = BootstrapLoop(db)
        report = loop.run_cycle(days=body.days)
        return {"success": True, "data": report}
    except Exception as e:
        logger.error("bootstrap-loop run error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
@limiter.limit("30/minute")
async def bootstrap_loop_history(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get past feedback-loop cycle reports.

    Returns the most recent *limit* reports, newest last.
    """
    try:
        loop = BootstrapLoop(db)
        reports = loop._load_reports()
        trimmed = reports[-limit:]
        return {
            "success": True,
            "data": trimmed,
            "meta": {"total": len(reports), "returned": len(trimmed)},
        }
    except Exception as e:
        logger.error("bootstrap-loop history error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
