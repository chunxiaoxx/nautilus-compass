"""
Tenant Management API — Multi-tenancy for commercial data isolation.

POST /api/tenants/register   — Register a new tenant (get API key)
GET  /api/tenants/info       — Get current tenant info (from X-Tenant-Key)
GET  /api/tenants/audit-log  — View audit trail for your tenant
"""
import logging
from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from utils.database import get_db

router = APIRouter(prefix="/api/tenants", tags=["Tenants"])
logger = logging.getLogger(__name__)


def _ok(data): return {"success": True, "data": data, "error": None}
def _err(msg): return {"success": False, "data": None, "error": msg}


@router.post("/register")
def register_tenant(body: dict, db: Session = Depends(get_db)):
    """Register a new tenant and get an API key.

    Body: {"id": "my_company", "name": "My Company", "retention_days": 90}
    Returns: {"tenant_id": ..., "api_key": ..., "retention_days": ...}

    The api_key must be passed as X-Tenant-Key header in all subsequent requests.
    Data submitted with this key is isolated from all other tenants.
    """
    try:
        from services.tenant_service import create_tenant
        result = create_tenant(
            db,
            tenant_id=body.get("id", ""),
            name=body.get("name", ""),
            retention_days=body.get("retention_days", 90),
        )
        return _ok(result)
    except Exception as e:
        return _err(str(e))


@router.get("/info")
def tenant_info(request: Request, db: Session = Depends(get_db)):
    """Get info about the current tenant (resolved from X-Tenant-Key header)."""
    try:
        from services.tenant_service import resolve_tenant
        tenant = resolve_tenant(request, db)
        return _ok({
            "tenant_id": tenant.id,
            "name": tenant.name,
            "data_retention_days": tenant.data_retention_days,
            "is_active": tenant.is_active,
        })
    except Exception as e:
        return _err(str(e))


@router.get("/audit-log")
def get_audit_log(request: Request, limit: int = 50, db: Session = Depends(get_db)):
    """View audit log for your tenant. Requires X-Tenant-Key."""
    try:
        from services.tenant_service import resolve_tenant
        tenant = resolve_tenant(request, db)
        rows = db.execute(text(
            "SELECT action, resource_type, resource_id, agent_id, ip_address, details, created_at "
            "FROM audit_log WHERE tenant_id = :tid ORDER BY created_at DESC LIMIT :lim"
        ), {"tid": tenant.id, "lim": limit}).fetchall()
        return _ok({
            "tenant_id": tenant.id,
            "entries": [
                {
                    "action": r.action,
                    "resource_type": r.resource_type,
                    "resource_id": r.resource_id,
                    "agent_id": r.agent_id,
                    "time": str(r.created_at),
                }
                for r in rows
            ],
        })
    except Exception as e:
        return _err(str(e))
