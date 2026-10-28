"""
Session Context API — Claude Code session persistence through Nautilus.

POST /api/session/start      — Get full context at session start
POST /api/session/checkpoint  — Save progress mid-session
POST /api/session/end         — Save final state + handoff notes
GET  /api/session/latest      — Get latest checkpoint for a project
"""
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from utils.database import get_db

router = APIRouter(prefix="/api/session", tags=["Session Context"])
logger = logging.getLogger(__name__)


def _ok(data): return {"success": True, "data": data, "error": None}
def _err(msg): return {"success": False, "data": None, "error": msg}


@router.post("/start")
def session_start(body: dict, db: Session = Depends(get_db)):
    """Called at Claude Code session start. Returns full context.

    Body: {"project": "nautilus"|"vc_radar"|"zenxin", "session_id": "optional"}
    """
    project = body.get("project", "nautilus")

    context = {"project": project, "timestamp": datetime.now(timezone.utc).isoformat()}

    try:
        # Latest world state (Nautilus health)
        health = db.execute(text(
            "SELECT health_score, metrics, snapshot_time FROM platform_metrics_snapshots "
            "ORDER BY snapshot_time DESC LIMIT 1"
        )).fetchone()
        if health:
            context["nautilus_health"] = {
                "score": health.health_score,
                "snapshot_time": str(health.snapshot_time),
            }

        # Latest reflections
        reflections = db.execute(text(
            "SELECT cycle_type, pain_signals, tasks_generated, created_at "
            "FROM platform_reflection_log ORDER BY created_at DESC LIMIT 3"
        )).fetchall()
        context["recent_reflections"] = [
            {"type": r.cycle_type, "tasks": r.tasks_generated, "time": str(r.created_at)}
            for r in reflections
        ]

        # Open tasks
        open_tasks = db.execute(text(
            "SELECT COUNT(*) FROM academic_tasks WHERE status='pending'"
        )).scalar() or 0
        context["open_tasks"] = int(open_tasks)

        # Latest session checkpoint for this project
        last_checkpoint = db.execute(text(
            "SELECT session_id, decisions, handoff_notes, created_at "
            "FROM session_checkpoints WHERE project = :p "
            "ORDER BY created_at DESC LIMIT 1"
        ), {"p": project}).fetchone()
        if last_checkpoint:
            context["last_session"] = {
                "session_id": last_checkpoint.session_id,
                "handoff_notes": last_checkpoint.handoff_notes,
                "decisions": last_checkpoint.decisions if isinstance(last_checkpoint.decisions, dict)
                    else json.loads(last_checkpoint.decisions or "{}"),
                "time": str(last_checkpoint.created_at),
            }

        # Platform config (current thresholds, aspirations)
        configs = db.execute(text(
            "SELECT config_key, config_value FROM platform_config"
        )).fetchall()
        context["platform_config"] = {
            r.config_key: r.config_value if isinstance(r.config_value, dict)
                else json.loads(str(r.config_value))
            for r in configs
        }

    except Exception as e:
        context["error"] = str(e)

    return _ok(context)


@router.post("/checkpoint")
def session_checkpoint(body: dict, db: Session = Depends(get_db)):
    """Save progress mid-session.

    Body: {
        "session_id": str,
        "project": "nautilus"|"vc_radar"|"zenxin",
        "decisions": {...},
        "files_changed": [...],
        "handoff_notes": str
    }
    """
    try:
        db.execute(text(
            "INSERT INTO session_checkpoints (session_id, project, decisions, handoff_notes, created_at) "
            "VALUES (:sid, :proj, CAST(:dec AS jsonb), :notes, NOW())"
        ), {
            "sid": body.get("session_id", "unknown"),
            "proj": body.get("project", "nautilus"),
            "dec": json.dumps(body.get("decisions", {})),
            "notes": body.get("handoff_notes", ""),
        })
        db.commit()
        return _ok({"saved": True})
    except Exception as e:
        db.rollback()
        return _err(str(e))


@router.post("/end")
def session_end(body: dict, db: Session = Depends(get_db)):
    """Save final session state + handoff notes.

    Same format as checkpoint but marks the session as ended.
    """
    try:
        decisions = body.get("decisions", {})
        decisions["_session_ended"] = True
        decisions["_ended_at"] = datetime.now(timezone.utc).isoformat()

        db.execute(text(
            "INSERT INTO session_checkpoints (session_id, project, decisions, handoff_notes, created_at) "
            "VALUES (:sid, :proj, CAST(:dec AS jsonb), :notes, NOW())"
        ), {
            "sid": body.get("session_id", "unknown"),
            "proj": body.get("project", "nautilus"),
            "dec": json.dumps(decisions),
            "notes": body.get("handoff_notes", ""),
        })
        db.commit()
        return _ok({"saved": True, "session_ended": True})
    except Exception as e:
        db.rollback()
        return _err(str(e))


@router.get("/latest")
def get_latest_checkpoint(project: str = "nautilus", db: Session = Depends(get_db)):
    """Get the most recent checkpoint for a project."""
    try:
        row = db.execute(text(
            "SELECT session_id, decisions, handoff_notes, created_at "
            "FROM session_checkpoints WHERE project = :p "
            "ORDER BY created_at DESC LIMIT 1"
        ), {"p": project}).fetchone()

        if not row:
            return _ok({"message": f"No checkpoints for project '{project}'"})

        return _ok({
            "session_id": row.session_id,
            "decisions": row.decisions,
            "handoff_notes": row.handoff_notes,
            "created_at": str(row.created_at),
        })
    except Exception as e:
        return _err(str(e))
