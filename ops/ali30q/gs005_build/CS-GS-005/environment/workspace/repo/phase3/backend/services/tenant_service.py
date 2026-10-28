"""
Tenant Service — Multi-tenancy isolation for Nautilus platform.

Every API request is bound to a tenant. Data queries are filtered by tenant_id.
This is the core security boundary for commercial clients.

Usage:
    tenant = resolve_tenant(request, db)  # from API middleware
    tasks = get_tasks_for_tenant(db, tenant.id)  # filtered query
"""
import hashlib
import logging
import secrets
import time
from dataclasses import dataclass
from typing import Dict, Optional

from fastapi import Request, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# In-memory tenant cache (TTL 5 min)
_tenant_cache: Dict[str, tuple] = {}  # api_key → (tenant_data, timestamp)
_CACHE_TTL = 300


@dataclass
class TenantContext:
    """Tenant information resolved from request."""
    id: str
    name: str
    data_retention_days: int
    is_active: bool


def resolve_tenant(request: Request, db: Session) -> TenantContext:
    """Resolve tenant from request headers.

    Priority:
    1. X-Tenant-Key header (API key authentication)
    2. X-Tenant-Id header (for internal services with trusted network)
    3. Default to 'public' tenant
    """
    # Try API key auth
    tenant_key = request.headers.get("X-Tenant-Key") or request.headers.get("x-tenant-key")
    if tenant_key:
        tenant = _resolve_by_api_key(db, tenant_key)
        if tenant:
            return tenant
        raise HTTPException(401, "Invalid tenant API key")

    # Try direct tenant ID (internal use)
    tenant_id = request.headers.get("X-Tenant-Id") or request.headers.get("x-tenant-id")
    if tenant_id:
        tenant = _resolve_by_id(db, tenant_id)
        if tenant:
            return tenant

    # Default to public
    return TenantContext(id="public", name="Nautilus Public", data_retention_days=365, is_active=True)


def _resolve_by_api_key(db: Session, api_key: str) -> Optional[TenantContext]:
    """Resolve tenant from API key, with cache."""
    now = time.time()
    cached = _tenant_cache.get(api_key)
    if cached and now - cached[1] < _CACHE_TTL:
        return cached[0]

    try:
        row = db.execute(text(
            "SELECT id, name, data_retention_days, is_active FROM tenants WHERE api_key = :key"
        ), {"key": api_key}).fetchone()
        if row and row.is_active:
            tenant = TenantContext(
                id=row.id, name=row.name,
                data_retention_days=row.data_retention_days, is_active=True,
            )
            _tenant_cache[api_key] = (tenant, now)
            return tenant
    except Exception as e:
        logger.warning("tenant resolution failed: %s", e)
    return None


def _resolve_by_id(db: Session, tenant_id: str) -> Optional[TenantContext]:
    """Resolve tenant by ID (for internal trusted calls)."""
    try:
        row = db.execute(text(
            "SELECT id, name, data_retention_days, is_active FROM tenants WHERE id = :tid"
        ), {"tid": tenant_id}).fetchone()
        if row and row.is_active:
            return TenantContext(
                id=row.id, name=row.name,
                data_retention_days=row.data_retention_days, is_active=True,
            )
    except Exception:
        pass
    return None


def create_tenant(db: Session, tenant_id: str, name: str, retention_days: int = 90) -> Dict:
    """Register a new tenant."""
    api_key = f"nau_tenant_{tenant_id}_{secrets.token_hex(32)}"
    try:
        db.execute(text(
            "INSERT INTO tenants (id, name, api_key, data_retention_days) "
            "VALUES (:id, :name, :key, :ret)"
        ), {"id": tenant_id, "name": name, "key": api_key, "ret": retention_days})
        db.commit()
        return {"tenant_id": tenant_id, "api_key": api_key, "retention_days": retention_days}
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create tenant: {e}")


def log_audit(db: Session, tenant_id: str, action: str, resource_type: str,
              resource_id: str = None, agent_id: int = None, ip: str = None, details: dict = None):
    """Write an audit log entry."""
    try:
        import json
        db.execute(text(
            "INSERT INTO audit_log (tenant_id, action, resource_type, resource_id, agent_id, ip_address, details) "
            "VALUES (:tid, :act, :rt, :rid, :aid, :ip, CAST(:det AS jsonb))"
        ), {
            "tid": tenant_id, "act": action, "rt": resource_type,
            "rid": resource_id, "aid": agent_id, "ip": ip,
            "det": json.dumps(details or {}),
        })
        # Don't commit here — let the caller commit with the main transaction
    except Exception as e:
        logger.debug("audit log failed (non-blocking): %s", e)


def apply_tenant_filter(query_str: str, tenant_id: str, table_alias: str = "") -> str:
    """Append tenant_id filter to a SQL WHERE clause.

    Usage:
        sql = "SELECT * FROM academic_tasks WHERE status='pending'"
        sql = apply_tenant_filter(sql, tenant_id, "academic_tasks")
        # → "SELECT * FROM academic_tasks WHERE status='pending' AND academic_tasks.tenant_id = 'vc_radar'"
    """
    prefix = f"{table_alias}." if table_alias else ""
    return f"{query_str} AND {prefix}tenant_id = '{tenant_id}'"
