"""
VC Radar API — Endpoint for 创投雷达 daily report generation via Nautilus.

POST /api/vc-radar/generate — Submit events, get multi-agent generated report
GET  /api/vc-radar/latest   — Get the latest generated report
"""
import json
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from utils.database import get_db

router = APIRouter(prefix="/api/vc-radar", tags=["VC Radar"])
logger = logging.getLogger(__name__)


def _ok(data): return {"success": True, "data": data, "error": None}
def _err(msg): return {"success": False, "data": None, "error": msg}


class ReportRequest(BaseModel):
    report_date: str  # "2026-04-02"
    events: List[dict]  # Event data from data governance pipeline
    industry_stats: Optional[dict] = None
    investor_stats: Optional[list] = None


_jobs: dict[str, dict] = {}  # in-memory job store (Redis-backed in production)


@router.post("/generate")
async def generate_report(req: ReportRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Submit daily VC report generation. Returns job_id immediately.

    Poll GET /api/vc-radar/job/{job_id} for results.
    """
    import uuid
    job_id = f"vc_{req.report_date}_{uuid.uuid4().hex[:8]}"
    _jobs[job_id] = {"status": "processing", "report_date": req.report_date, "events_count": len(req.events)}

    # Save to Redis for persistence
    try:
        from utils.redis_client import get_redis
        get_redis().setex(f"vc_job:{job_id}", 3600, json.dumps(_jobs[job_id]))
    except Exception:
        pass

    async def _run():
        from utils.database import SessionLocal
        _db = SessionLocal()
        try:
            from services.vc_radar_adapter import generate_report_via_nautilus
            result = await generate_report_via_nautilus(
                db=_db, report_date=req.report_date, events=req.events,
                industry_stats=req.industry_stats, investor_stats=req.investor_stats,
            )
            _jobs[job_id] = {"status": "completed", **result}
            try:
                from utils.redis_client import get_redis
                get_redis().setex(f"vc_job:{job_id}", 3600, json.dumps(_jobs[job_id], default=str))
            except Exception:
                pass
        except Exception as e:
            _jobs[job_id] = {"status": "failed", "error": str(e)}
        finally:
            _db.close()

    background_tasks.add_task(_run)
    return _ok({"job_id": job_id, "status": "processing", "poll_url": f"/api/vc-radar/job/{job_id}"})


@router.get("/job/{job_id}")
def get_job_status(job_id: str):
    """Poll for report generation status."""
    # Check memory first, then Redis
    job = _jobs.get(job_id)
    if not job:
        try:
            from utils.redis_client import get_redis
            data = get_redis().get(f"vc_job:{job_id}")
            if data:
                job = json.loads(data)
        except Exception:
            pass
    if not job:
        return _err(f"Job {job_id} not found")
    return _ok(job)


@router.get("/latest")
def get_latest_report(db: Session = Depends(get_db)):
    """Get the latest generated VC report sections."""
    try:
        from sqlalchemy import text
        rows = db.execute(text(
            "SELECT task_id, title, result_output, quality_rating, created_at "
            "FROM academic_tasks "
            "WHERE task_type='vc_daily_report' "
            "ORDER BY created_at DESC LIMIT 7"
        )).fetchall()

        if not rows:
            return _ok({"message": "No reports generated yet"})

        sections = []
        for r in rows:
            sections.append({
                "task_id": r.task_id,
                "title": r.title,
                "content": r.result_output[:2000] if r.result_output else None,
                "quality": r.quality_rating,
                "created_at": str(r.created_at),
            })

        return _ok({"sections": sections, "count": len(sections)})

    except Exception as e:
        return _err(str(e))
