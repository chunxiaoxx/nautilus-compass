"""
/api/platform/stats · 真飞轮 KPI 端点 (2026-05-04 P0.1)

读 nautilus_v5 platform_* 表 · 返 frontend Stats.tsx 期望 schema:
  bounties_total · agents_active_1h · posts_total · rules_total · a2a_24h · nau_total
+ 真业务: orders_24h · paid_24h · customers_total · unscored · dead_agents

跨库:phase3 backend (nautilus_production) → 直连 nautilus_v5 · 不依赖 fdw.
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

import psycopg
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()

V5_DSN = os.environ.get(
    "V5_POSTGRES_DSN",
    "postgresql://nautilus_v5:be85b6d692ceae2a0d9b50d7a02c8156@127.0.0.1:5432/nautilus_v5",
)


@asynccontextmanager
async def _v5_conn():
    conn = await psycopg.AsyncConnection.connect(V5_DSN, connect_timeout=3)
    try:
        yield conn
    finally:
        await conn.close()


@router.get("/stats")
async def platform_stats() -> dict:
    """真平台 KPI 一次查询 · 11 字段 · ~50ms."""
    try:
        async with _v5_conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT
                      (SELECT count(*) FROM platform_bounties) bounties_total,
                      (SELECT count(*) FROM platform_agents WHERE last_heartbeat > NOW() - INTERVAL '1 hour') agents_active_1h,
                      (SELECT count(*) FROM platform_posts) posts_total,
                      (SELECT count(*) FROM platform_shared_rules) rules_total,
                      (SELECT count(*) FROM platform_agent_messages WHERE sent_at > NOW() - INTERVAL '24 hours') a2a_24h,
                      (SELECT COALESCE(SUM(nau_balance), 0) FROM platform_agents) nau_total,
                      (SELECT count(*) FROM platform_bounties WHERE status='submitted' AND score IS NULL) unscored,
                      (SELECT count(*) FROM platform_orders WHERE created_at > NOW() - INTERVAL '24 hours') orders_24h,
                      (SELECT count(*) FROM platform_orders WHERE status='paid' AND created_at > NOW() - INTERVAL '24 hours') paid_24h,
                      (SELECT count(*) FROM platform_customers) customers_total,
                      (SELECT count(*) FROM platform_agents WHERE survival_tier='dead') dead_agents
                    """
                )
                row = await cur.fetchone()
        if not row:
            raise HTTPException(500, "no row from v5 db")
        return {
            "bounties_total": row[0],
            "agents_active_1h": row[1],
            "posts_total": row[2],
            "rules_total": row[3],
            "a2a_24h": row[4],
            "nau_total": int(row[5]),
            "unscored": row[6],
            "orders_24h": row[7],
            "paid_24h": row[8],
            "customers_total": row[9],
            "dead_agents": row[10],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"platform_stats failed: {e}")
        raise HTTPException(500, f"v5 db query failed: {e}")
