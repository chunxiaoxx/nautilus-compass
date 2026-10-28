"""
Knowledge Package + Human Review API.

POST /api/knowledge/packages          — Upload a knowledge package
GET  /api/knowledge/packages          — List packages
POST /api/knowledge/bind-agent        — Bind package to agent
POST /api/knowledge/review            — Submit human review
GET  /api/knowledge/pending-reviews   — Get tasks awaiting review
"""
import logging
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from utils.database import get_db

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge & Review"])
logger = logging.getLogger(__name__)

def _ok(data): return {"success": True, "data": data, "error": None}
def _err(msg): return {"success": False, "data": None, "error": msg}


@router.post("/packages")
def create_package(body: dict, request: Request, db: Session = Depends(get_db)):
    """Upload a domain knowledge package.

    Body: {package_id, name, domain, content, metadata?}
    domain: comma-separated keywords for auto-matching (e.g. "quantum,buddhism,meditation")
    """
    try:
        from services.knowledge_package_service import create_knowledge_package
        from services.tenant_service import resolve_tenant
        tenant = resolve_tenant(request, db)
        result = create_knowledge_package(
            db,
            package_id=body.get("package_id", ""),
            name=body.get("name", ""),
            domain=body.get("domain", ""),
            content=body.get("content", ""),
            tenant_id=tenant.id,
            metadata=body.get("metadata"),
        )
        return _ok(result)
    except Exception as e:
        return _err(str(e))


@router.get("/packages")
def list_packages(request: Request, db: Session = Depends(get_db)):
    """List all knowledge packages visible to current tenant."""
    try:
        from services.tenant_service import resolve_tenant
        from sqlalchemy import text
        tenant = resolve_tenant(request, db)
        rows = db.execute(text(
            "SELECT package_id, name, domain, LENGTH(content) AS size, tenant_id, created_at "
            "FROM knowledge_packages WHERE tenant_id IN (:tid, 'public') ORDER BY created_at DESC"
        ), {"tid": tenant.id}).fetchall()
        return _ok([
            {"package_id": r.package_id, "name": r.name, "domain": r.domain,
             "size": r.size, "tenant_id": r.tenant_id}
            for r in rows
        ])
    except Exception as e:
        return _err(str(e))


@router.post("/bind-agent")
def bind_agent(body: dict, db: Session = Depends(get_db)):
    """Bind a knowledge package to an agent.

    Body: {agent_id: int, package_id: str, system_context?: str}
    """
    try:
        from services.knowledge_package_service import bind_agent_to_package
        result = bind_agent_to_package(
            db,
            agent_id=body.get("agent_id"),
            package_id=body.get("package_id"),
            system_context=body.get("system_context"),
        )
        return _ok(result)
    except Exception as e:
        return _err(str(e))


@router.post("/review")
def submit_review(body: dict, request: Request, db: Session = Depends(get_db)):
    """Submit human review for a task.

    Body: {task_id, reviewer_id, score: 1-5, feedback}
    """
    try:
        from services.knowledge_package_service import submit_human_review
        from services.tenant_service import resolve_tenant
        tenant = resolve_tenant(request, db)
        result = submit_human_review(
            db, task_id=body.get("task_id", ""),
            reviewer_id=body.get("reviewer_id", "human"),
            score=float(body.get("score", 3.0)),
            feedback=body.get("feedback", ""),
            tenant_id=tenant.id,
        )
        return _ok(result)
    except Exception as e:
        return _err(str(e))


@router.get("/pending-reviews")
def pending_reviews(request: Request, db: Session = Depends(get_db)):
    """Get tasks awaiting human review for your tenant."""
    try:
        from services.knowledge_package_service import get_pending_reviews
        from services.tenant_service import resolve_tenant
        tenant = resolve_tenant(request, db)
        return _ok(get_pending_reviews(db, tenant.id))
    except Exception as e:
        return _err(str(e))
