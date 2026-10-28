"""
Deep Research API.

Endpoints:
  POST /api/research/deep          — Start a deep research job (sync, may take 30-120s)
  GET  /api/research/status/{id}   — Poll job status (for long-running jobs)
"""
import asyncio
import logging
import time
import uuid
from typing import Dict, Literal, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/research", tags=["Deep Research"])

# ──────────────────────────────────────────────────────────────────────────────
# In-memory job store (suitable for single-process; extend with Redis for scale)
# ──────────────────────────────────────────────────────────────────────────────

_jobs: Dict[str, Dict] = {}


def _store_job(job_id: str, status: str, **kwargs) -> None:
    _jobs[job_id] = {"job_id": job_id, "status": status, "updated_at": time.time(), **kwargs}


def _update_job(job_id: str, **kwargs) -> None:
    if job_id in _jobs:
        _jobs[job_id].update({"updated_at": time.time(), **kwargs})


# ──────────────────────────────────────────────────────────────────────────────
# Request / Response models
# ──────────────────────────────────────────────────────────────────────────────

class DeepResearchRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500, description="Research topic")
    depth: Literal["quick", "standard", "thorough"] = Field(
        "standard",
        description="quick=3 sub-questions, standard=4, thorough=5",
    )
    save_to_gdoc: bool = Field(False, description="Export report to Google Docs")


class SectionsModel(BaseModel):
    summary: str = ""
    findings: str = ""
    recommendations: str = ""


class DeepResearchResponse(BaseModel):
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────────────
# Background runner
# ──────────────────────────────────────────────────────────────────────────────

async def _run_pipeline_background(job_id: str, topic: str, depth: str, save_to_gdoc: bool) -> None:
    """Execute the pipeline and update the job store."""
    try:
        from services.deep_research import get_deep_research
        pipeline = get_deep_research()
        result = await pipeline.run(topic=topic, depth=depth, save_to_gdoc=save_to_gdoc)
        _update_job(job_id, status="completed", result=result)
        logger.info("[Research API] Job %s completed", job_id)
    except Exception as exc:
        logger.error("[Research API] Job %s failed: %s", job_id, exc)
        _update_job(job_id, status="failed", error=str(exc))


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/deep", response_model=DeepResearchResponse, summary="Run deep research pipeline")
async def deep_research(body: DeepResearchRequest, background_tasks: BackgroundTasks):
    """
    Launch the DeerFlow multi-agent deep research pipeline.

    - **quick**: 3 sub-questions, fastest (~20-40s)
    - **standard**: 4 sub-questions, balanced (~40-80s)
    - **thorough**: 5 sub-questions, most comprehensive (~60-120s)

    The endpoint runs synchronously for quick/standard and returns the full report.
    For long-running jobs the job_id can be polled via GET /api/research/status/{job_id}.
    """
    job_id = str(uuid.uuid4())
    _store_job(job_id, "running", topic=body.topic, depth=body.depth)

    # All depths run in background — pipeline takes 60-120s with DDGS search
    background_tasks.add_task(
        _run_pipeline_background, job_id, body.topic, body.depth, body.save_to_gdoc
    )
    return DeepResearchResponse(
        success=True,
        data={
            "job_id": job_id,
            "status": "running",
            "message": f"Research started ({body.depth} depth). Poll /api/research/status/{job_id}.",
        },
    )


@router.get("/status/{job_id}", response_model=DeepResearchResponse, summary="Poll research job status")
async def get_research_status(job_id: str):
    """
    Poll the status of a background research job.

    Possible statuses: **running** | **completed** | **failed**
    """
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "JOB_NOT_FOUND",
                    "message": f"No research job found with id: {job_id}",
                }
            },
        )

    status = job["status"]

    if status == "running":
        return DeepResearchResponse(
            success=True,
            data={"job_id": job_id, "status": "running", "topic": job.get("topic")},
        )

    if status == "failed":
        return DeepResearchResponse(
            success=False,
            data={"job_id": job_id, "status": "failed"},
            error=job.get("error", "Unknown error"),
        )

    # Completed
    result = job.get("result", {})
    return DeepResearchResponse(
        success=True,
        data={
            "job_id": job_id,
            "status": "completed",
            "report": result.get("report", ""),
            "sections": result.get("sections", {}),
            "sub_questions": result.get("sub_questions", []),
            "gdoc_url": result.get("gdoc_url"),
            "duration_seconds": result.get("duration_seconds"),
        },
    )
