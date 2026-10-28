"""
Knowledge Package Service — Domain knowledge injection for specialized agents.

A knowledge package is a reusable bundle of domain expertise that agents
carry when executing tasks. This solves the "generic agent can't do
domain-specific work" problem.

Flow:
  1. Domain expert uploads knowledge package (text + metadata)
  2. Specialized agent is registered with package binding
  3. When agent executes a task, package content is auto-injected into LLM prompt
  4. Human reviews a sample of outputs for quality assurance
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def create_knowledge_package(
    db: Session,
    package_id: str,
    name: str,
    domain: str,
    content: str,
    tenant_id: str = "public",
    metadata: dict = None,
) -> Dict:
    """Create a new knowledge package."""
    try:
        db.execute(text(
            "INSERT INTO knowledge_packages (package_id, tenant_id, name, domain, content, metadata) "
            "VALUES (:pid, :tid, :name, :domain, :content, CAST(:meta AS jsonb))"
        ), {
            "pid": package_id, "tid": tenant_id, "name": name,
            "domain": domain, "content": content,
            "meta": json.dumps(metadata or {}),
        })
        db.commit()
        logger.info("knowledge_package created: %s (domain=%s, %d chars)", package_id, domain, len(content))
        return {"package_id": package_id, "domain": domain, "content_length": len(content)}
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create knowledge package: {e}")


def get_knowledge_package(db: Session, package_id: str) -> Optional[Dict]:
    """Retrieve a knowledge package by ID."""
    row = db.execute(text(
        "SELECT package_id, name, domain, content, metadata, tenant_id "
        "FROM knowledge_packages WHERE package_id = :pid"
    ), {"pid": package_id}).fetchone()
    if not row:
        return None
    return {
        "package_id": row.package_id,
        "name": row.name,
        "domain": row.domain,
        "content": row.content,
        "metadata": row.metadata if isinstance(row.metadata, dict) else json.loads(row.metadata or "{}"),
        "tenant_id": row.tenant_id,
    }


def find_package_for_task(db: Session, task_description: str, task_type: str = "") -> Optional[Dict]:
    """Auto-match a knowledge package based on task content.

    Matches by domain keywords in task description or task_type.
    """
    try:
        packages = db.execute(text(
            "SELECT package_id, domain, name, LENGTH(content) AS size "
            "FROM knowledge_packages ORDER BY created_at DESC"
        )).fetchall()

        desc_lower = task_description.lower()
        for pkg in packages:
            domain_keywords = pkg.domain.lower().split(",")
            if any(kw.strip() in desc_lower for kw in domain_keywords):
                return get_knowledge_package(db, pkg.package_id)
            if task_type and pkg.domain.lower() in task_type.lower():
                return get_knowledge_package(db, pkg.package_id)
    except Exception:
        pass
    return None


def get_agent_knowledge_context(db: Session, agent_id: int) -> str:
    """Get the full knowledge context for an agent (system_context + bound package)."""
    parts = []
    try:
        row = db.execute(text(
            "SELECT system_context, knowledge_package_id FROM agents WHERE agent_id = :aid"
        ), {"aid": agent_id}).fetchone()

        if row:
            if row.system_context:
                parts.append(row.system_context)
            if row.knowledge_package_id:
                pkg = get_knowledge_package(db, row.knowledge_package_id)
                if pkg:
                    parts.append(f"\n## Domain Knowledge: {pkg['name']}\n\n{pkg['content']}")
    except Exception as e:
        logger.debug("get_agent_knowledge_context failed: %s", e)

    return "\n\n".join(parts) if parts else ""


def bind_agent_to_package(db: Session, agent_id: int, package_id: str, system_context: str = None) -> Dict:
    """Bind a knowledge package to an agent + optionally set system_context."""
    try:
        updates = ["knowledge_package_id = :pid"]
        params = {"pid": package_id, "aid": agent_id}
        if system_context:
            updates.append("system_context = :ctx")
            params["ctx"] = system_context
        db.execute(text(
            f"UPDATE agents SET {', '.join(updates)} WHERE agent_id = :aid"
        ), params)
        db.commit()
        return {"agent_id": agent_id, "package_id": package_id, "bound": True}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}


# ── Human Review ─────────────────────────────────────────────────────────────

def submit_human_review(
    db: Session, task_id: str, reviewer_id: str,
    score: float, feedback: str, tenant_id: str = "public",
) -> Dict:
    """Submit a human review for a completed task."""
    try:
        db.execute(text(
            "INSERT INTO human_reviews (task_id, tenant_id, reviewer_id, status, score, feedback) "
            "VALUES (:tid, :ten, :rev, 'reviewed', :score, :feedback)"
        ), {
            "tid": task_id, "ten": tenant_id, "rev": reviewer_id,
            "score": score, "feedback": feedback,
        })
        # Update task quality_rating
        db.execute(text(
            "UPDATE academic_tasks SET quality_rating = :score WHERE task_id = :tid"
        ), {"score": min(5.0, max(1.0, score)), "tid": task_id})
        db.commit()
        logger.info("human_review: task=%s score=%.1f by %s", task_id, score, reviewer_id)
        return {"task_id": task_id, "score": score, "status": "reviewed"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}


def get_pending_reviews(db: Session, tenant_id: str = "public", limit: int = 20) -> List[Dict]:
    """Get tasks awaiting human review for a tenant."""
    try:
        rows = db.execute(text(
            "SELECT t.task_id, t.title, t.task_type, LEFT(t.result_output, 300) AS preview, t.created_at "
            "FROM academic_tasks t "
            "WHERE t.tenant_id = :tid AND t.status = 'completed' "
            "AND t.quality_rating IS NULL "
            "AND NOT EXISTS (SELECT 1 FROM human_reviews h WHERE h.task_id = t.task_id) "
            "ORDER BY t.created_at DESC LIMIT :lim"
        ), {"tid": tenant_id, "lim": limit}).fetchall()
        return [
            {"task_id": r.task_id, "title": r.title, "type": r.task_type,
             "preview": r.preview, "created_at": str(r.created_at)}
            for r in rows
        ]
    except Exception as e:
        return [{"error": str(e)}]
