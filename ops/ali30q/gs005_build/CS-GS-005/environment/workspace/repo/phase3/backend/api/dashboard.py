"""
Dashboard API — real-time platform status for the website and bicameral mind.

Public endpoints (no auth required):
  GET /api/dashboard/flywheel      — flywheel health & pain signals
  GET /api/dashboard/consciousness — latest bicameral reflection
  GET /api/dashboard/agents        — agent roster and performance
  GET /api/dashboard/marketing     — latest marketing content
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from utils.database import get_db

logger = logging.getLogger(__name__)

dashboard_router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _flywheel_status(revenue_total: float, active_customers: int) -> str:
    """Derive flywheel stage from revenue and customer activity."""
    if revenue_total <= 0 and active_customers <= 0:
        return "stalled"
    if revenue_total > 0 and active_customers >= 3:
        return "spinning"
    if revenue_total > 1000:
        return "accelerating"
    return "warming"


def _top_pain(pain_signals: List[Dict[str, Any]]) -> str:
    """Return the description of the highest-intensity pain signal."""
    if not pain_signals:
        return "No active pain signals"
    top = max(pain_signals, key=lambda p: p.get("intensity", 0))
    return top.get("action", "Unknown")


# ---------------------------------------------------------------------------
# GET /flywheel
# ---------------------------------------------------------------------------

@dashboard_router.get("/flywheel")
def get_flywheel(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Flywheel health: revenue, tasks, customers, agents, quality."""
    from models.conversation import Order, Customer
    from models.database import AcademicTask
    from services.rehoboam import get_rehoboam
    from services.bicameral_mind import get_bicameral_mind

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    # --- Revenue ---
    def _revenue_since(since: datetime) -> float:
        val = (
            db.query(func.coalesce(func.sum(Order.paid_amount), 0.0))
            .filter(Order.payment_confirmed_at >= since)
            .scalar()
        )
        return float(val or 0.0)

    rev_today = _revenue_since(today_start)
    rev_week = _revenue_since(week_start)
    rev_month = _revenue_since(month_start)
    rev_total = float(
        db.query(func.coalesce(func.sum(Order.paid_amount), 0.0)).scalar() or 0.0
    )

    # --- Tasks ---
    tasks_today = int(
        db.query(func.count(AcademicTask.id))
        .filter(AcademicTask.status == "completed", AcademicTask.updated_at >= today_start)
        .scalar() or 0
    )
    tasks_failed = int(
        db.query(func.count(AcademicTask.id))
        .filter(AcademicTask.status == "failed", AcademicTask.updated_at >= today_start)
        .scalar() or 0
    )
    total_attempted = tasks_today + tasks_failed
    success_rate = round(tasks_today / total_attempted * 100, 1) if total_attempted > 0 else 100.0

    # --- Customers ---
    total_customers = int(db.query(func.count(Customer.id)).scalar() or 0)
    active_24h = int(
        db.query(func.count(Customer.id))
        .filter(Customer.updated_at >= now - timedelta(hours=24))
        .scalar() or 0
    )
    returning = int(
        db.query(func.count(Customer.id))
        .filter(Customer.total_orders >= 2)
        .scalar() or 0
    )

    # --- Agents ---
    rehoboam = get_rehoboam()
    registry = rehoboam.registry
    agents_list = list(registry.agents.values())
    total_agents = len(agents_list)
    active_agents = sum(1 for a in agents_list if a.is_active)
    top_performer = max(agents_list, key=lambda a: a.tasks_completed).name if agents_list else "none"

    # --- Quality ---
    audit_passed = int(
        db.query(func.count(AcademicTask.id))
        .filter(AcademicTask.audit_status == "passed")
        .scalar() or 0
    )
    audit_flagged = int(
        db.query(func.count(AcademicTask.id))
        .filter(AcademicTask.audit_status == "flagged")
        .scalar() or 0
    )
    avg_exec_time = float(
        db.query(func.coalesce(func.avg(AcademicTask.execution_time), 0.0))
        .filter(AcademicTask.execution_time.isnot(None))
        .scalar() or 0.0
    )

    # --- Pain / Flywheel ---
    bicameral = get_bicameral_mind()
    try:
        reflection = bicameral.reflect()
        pain_signals = reflection.get("pain_signals", [])
        pain_level = (
            sum(p.get("intensity", 0) for p in pain_signals) / len(pain_signals)
            if pain_signals
            else 0.0
        )
    except Exception as exc:
        logger.warning("Bicameral reflect failed in flywheel: %s", exc)
        pain_signals = []
        pain_level = 0.0

    status = _flywheel_status(rev_total, active_24h)

    return {
        "revenue": {
            "today": round(rev_today, 2),
            "week": round(rev_week, 2),
            "month": round(rev_month, 2),
            "total": round(rev_total, 2),
        },
        "tasks": {
            "today": tasks_today,
            "completed": tasks_today,
            "failed": tasks_failed,
            "success_rate": success_rate,
        },
        "customers": {
            "total": total_customers,
            "active_24h": active_24h,
            "returning": returning,
        },
        "agents": {
            "total": total_agents,
            "active": active_agents,
            "top_performer": top_performer,
        },
        "quality": {
            "audit_passed": audit_passed,
            "audit_flagged": audit_flagged,
            "avg_execution_time": round(avg_exec_time, 1),
        },
        "flywheel_status": status,
        "pain_level": round(pain_level, 2),
        "top_pain": _top_pain(pain_signals),
        "next_action": (
            pain_signals[0]["action"] if pain_signals else "Keep executing tasks"
        ),
    }


# ---------------------------------------------------------------------------
# GET /heartbeat
# ---------------------------------------------------------------------------

@dashboard_router.get("/heartbeat")
async def heartbeat_status():
    # services.heartbeat_monitor was moved to _dead_code_backup_20260327/phase2_4/
    # in 2026-04. Endpoint kept for backward-compat with platform-health-monitor
    # but returns graceful stub instead of crashing with 500. Remove the endpoint
    # entirely in a follow-up cleanup PR once no caller surfaces.
    try:
        from services.heartbeat_monitor import get_monitor  # type: ignore
        return get_monitor().scan()
    except ImportError:
        return {"status": "monitor_unavailable", "reason": "heartbeat_monitor module removed 2026-04"}


# ---------------------------------------------------------------------------
# GET /consciousness
# ---------------------------------------------------------------------------

@dashboard_router.get("/consciousness")
def get_consciousness() -> Dict[str, Any]:
    """Latest bicameral reflection report."""
    from services.bicameral_mind import get_bicameral_mind

    bicameral = get_bicameral_mind()
    try:
        result = bicameral.reflect()
    except Exception as exc:
        logger.error("Bicameral reflection failed: %s", exc)
        return {"report_text": "Reflection unavailable.", "error": str(exc)}

    return {
        "report_text": result.get("report_text", ""),
        "pain_signals": result.get("pain_signals", []),
        "dialogue": result.get("dialogue", []),
        "metrics": result.get("metrics", {}),
    }


# ---------------------------------------------------------------------------
# GET /agents
# ---------------------------------------------------------------------------

@dashboard_router.get("/agents")
def get_agents() -> Dict[str, Any]:
    """Agent roster with performance stats."""
    from services.rehoboam import get_rehoboam

    registry = get_rehoboam().registry
    roster = []
    for agent in registry.agents.values():
        roster.append({
            "agent_id": agent.agent_id,
            "name": agent.name,
            "role": agent.role,
            "provider": agent.provider,
            "model": agent.model,
            "capabilities": agent.capabilities,
            "tasks_completed": agent.tasks_completed,
            "success_rate": round(agent.success_rate, 3),
            "is_active": agent.is_active,
        })

    return {"agents": roster, "total": len(roster)}


# ---------------------------------------------------------------------------
# GET /marketing
# ---------------------------------------------------------------------------

@dashboard_router.get("/marketing")
def get_marketing() -> Dict[str, Any]:
    """Latest marketing content generated from real platform data."""
    try:
        from services.marketing_engine import MarketingEngine
        engine = MarketingEngine()
        post = engine.generate_daily_social_post()
        return {
            "social_post": post,
            "generated_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"social_post": None, "error": str(e)}


# ---------------------------------------------------------------------------
# POST /self-improve — manually trigger self-improvement cycle
# ---------------------------------------------------------------------------

@dashboard_router.post("/self-improve")
async def trigger_self_improvement(request: Request) -> Dict[str, Any]:
    """Manually trigger a self-improvement cycle: pain → tasks → publish."""
    from api.org import _auth_check  # 2026-10-11 追补④:pain→tasks→publish 全轮驱动口,限 platform
    from utils.database import SessionLocal
    _sess = SessionLocal()
    try:
        denied = _auth_check(_sess, request, "platform")
    finally:
        _sess.close()
    if denied:
        return denied
    from services.self_improvement_engine import get_self_improvement_engine
    engine = get_self_improvement_engine()
    result = await engine.run_cycle()
    return result


# ---------------------------------------------------------------------------
# GET /autonomous-status — show autonomous loop status
# ---------------------------------------------------------------------------

@dashboard_router.get("/autonomous-status")
def get_autonomous_status() -> Dict[str, Any]:
    """Current autonomous loop status."""
    try:
        from services.autonomous_loop import get_autonomous_loop
        loop = get_autonomous_loop()
        return {
            "running": loop._running,
            "cycle_count": loop._cycle_count,
            "total_actions": loop._total_actions,
            "last_actions": loop._last_actions,
            "cooldowns": loop._action_cooldowns,
        }
    except Exception as e:
        return {"running": False, "error": str(e)}
