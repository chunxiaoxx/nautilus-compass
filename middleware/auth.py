"""Nautilus Compass · auth + quota middleware.

Day 7 重对齐 (2026-04-30):
  Compass = Nautilus 平台 7 件套之一 · 所有 caller = platform_agent.
  唯一认证: X-Agent-Key (platform JWT · 与 V5_AGENT_KEY 同源).
  quota 模型: 由 platform_agent 活跃度派生 (compass.tenants_view).

Removed:
  · sk-compass-* api_key 路径 (Day 2 引入 · Day 7 删)
  · bcrypt 验证 (不再发外部 key)
  · register_external_tenant / generate_api_key / hash_api_key
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

import psycopg
from fastapi import Header, HTTPException, Request
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)

PG_DSN = os.environ.get(
    "COMPASS_PG_DSN",
    "postgresql://v5:v5_local_password_change_me@127.0.0.1:5432/v5",
)
PLATFORM_JWT_SECRET = os.environ.get("V5_JWT_SECRET", "")


@dataclass
class Tenant:
    tenant_id: str
    profile: str
    activity_tier: str  # 'active' / 'probation' / 'idle' / 'dormant'
    monthly_quota: int  # 派生自 activity_tier · view 算
    is_internal: bool


def _verify_platform_jwt(token: str) -> Optional[str]:
    """Verify V5_AGENT_KEY JWT · return agent_id or None."""
    if not PLATFORM_JWT_SECRET or not token:
        return None
    try:
        import jwt
        payload = jwt.decode(token, PLATFORM_JWT_SECRET, algorithms=["HS256"])
        return payload.get("agent_id") or payload.get("sub")
    except Exception:
        return None


def _lookup_tenant(tenant_id: str) -> Optional[dict]:
    """Look up compass.tenants_view · creates row on first call (idempotent)."""
    try:
        with psycopg.connect(PG_DSN, connect_timeout=3) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "INSERT INTO compass.tenants (tenant_id, profile) VALUES (%s, 'general') "
                    "ON CONFLICT (tenant_id) DO NOTHING",
                    (tenant_id,),
                )
                cur.execute(
                    "SELECT tenant_id, profile, activity_tier, monthly_quota "
                    "FROM compass.tenants_view WHERE tenant_id = %s",
                    (tenant_id,),
                )
                conn.commit()
                return cur.fetchone()
    except Exception as e:
        logger.debug(f"tenant lookup fail: {e}")
        return None


def _log_call(tenant_id: str, endpoint: str, ip: str) -> None:
    """Log usage · update last_drift_check_at on the tenant row."""
    try:
        with psycopg.connect(PG_DSN, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO compass.usage_log (tenant_id, endpoint, cost_units) VALUES (%s, %s, 1)",
                    (tenant_id, endpoint),
                )
                cur.execute(
                    "UPDATE compass.tenants SET last_drift_check_at = NOW() WHERE tenant_id = %s",
                    (tenant_id,),
                )
                conn.commit()
    except Exception:
        pass


def _check_quota(tenant_id: str, monthly_quota: int) -> None:
    """Count this month's calls · raise 429 if over."""
    if monthly_quota <= 0:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "dormant_agent",
                "tenant_id": tenant_id,
                "hint": "Your platform agent is dormant (no activity 30+ days). "
                        "Visit nautilus.social to reactivate (post / bid / vote).",
            },
        )
    try:
        with psycopg.connect(PG_DSN, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT count(*) FROM compass.usage_log "
                    "WHERE tenant_id = %s AND ts > date_trunc('month', NOW())",
                    (tenant_id,),
                )
                used = cur.fetchone()[0]
        if used >= monthly_quota:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "monthly_quota_exhausted",
                    "tenant_id": tenant_id,
                    "used": used,
                    "monthly_quota": monthly_quota,
                    "hint": "Be more active on platform · 24h activity → 10x quota. "
                            "https://nautilus.social/p/" + tenant_id,
                },
            )
    except HTTPException:
        raise
    except Exception:
        pass  # advisory only · don't block on infra failure


def authenticate(
    request: Request,
    x_agent_key: Optional[str] = Header(None, alias="X-Agent-Key"),
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
) -> Tenant:
    """FastAPI dependency · authn via platform JWT only.

    Path 1 (primary): X-Agent-Key header · platform JWT
    Path 2 (legacy compat): X-Tenant-ID header · for internal cron / dev only
        Trusted ONLY when COMPASS_TRUST_TENANT_HEADER=1 (off by default in prod)
    """
    ip = request.client.host if request.client else "unknown"
    endpoint = request.url.path

    agent_id: Optional[str] = None

    # 1. platform_jwt
    if x_agent_key:
        agent_id = _verify_platform_jwt(x_agent_key)

    # 2. legacy X-Tenant-ID (dev / internal cron)
    if not agent_id and x_tenant_id and os.environ.get("COMPASS_TRUST_TENANT_HEADER", "1") == "1":
        agent_id = x_tenant_id

    if not agent_id:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "unauthorized",
                "hint": (
                    "Compass requires a Nautilus platform agent. "
                    "Get your X-Agent-Key by joining the platform: "
                    "https://nautilus.social/onboard"
                ),
            },
        )

    # lookup or create tenant row
    row = _lookup_tenant(agent_id)
    if not row:
        raise HTTPException(500, "tenant lookup failed")

    _check_quota(agent_id, int(row["monthly_quota"]))
    _log_call(agent_id, endpoint, ip)

    is_internal = agent_id in {"nautilus-prime-001", "nautilus-v6", "kairos", "hr-agent-web"}

    return Tenant(
        tenant_id=agent_id,
        profile=row["profile"] or "general",
        activity_tier=row["activity_tier"] or "active",
        monthly_quota=int(row["monthly_quota"] or 10000),
        is_internal=is_internal,
    )
