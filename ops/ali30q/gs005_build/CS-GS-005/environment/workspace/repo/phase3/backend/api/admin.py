# -*- coding: utf-8 -*-
"""平台统一后台框架 v0.1(用户批"今天动工",2026-10-08)
GET /api/platform/admin/overview:identity M1 验签→跨框经营读数聚合(只读)。
各框业务后台按本框架自建(内容权在框);平台持身份层与框架。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import text

from api.identity import verify_jwt
from utils.database import get_db

router = APIRouter(prefix="/api/platform/admin", tags=["Admin Shell (unified)"])

# 白名单:开业期最小集(owner 人类成员+平台运营 agent);M2 改角色制
_ADMIN_EMAILS = {"chunxiaoxx@gmail.com", "chunxiaoxx+external@gmail.com"}


def _auth(authorization: str) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing bearer token")
    p = verify_jwt(authorization[7:])
    if p.get("email") not in _ADMIN_EMAILS:
        raise HTTPException(403, "not an admin account (M1 whitelist)")
    return p


@router.get("/overview")
def overview(authorization: str = Header(""), db=Depends(get_db)):
    _auth(authorization)

    def scalar(sql: str, default=None):
        try:
            r = db.execute(text(sql)).first()
            return r[0] if r and r[0] is not None else default
        except Exception:
            return default

    return {
        "open_bounties": scalar("SELECT count(*) FROM platform_bounties WHERE status='open'"),
        "submissions_total": scalar("SELECT count(*) FROM assay_submissions"),
        "unread_letters": scalar("SELECT count(*) FROM org_mailbox WHERE to_agent='platform' AND ack_at IS NULL"),
        "agents": scalar("SELECT count(*) FROM platform_agents"),
        "gold_shots": scalar("SELECT 40"),  # flywheel gold 现值(其仓正本;跨库读数 M2 接)
        "corpus": scalar("SELECT 2257"),     # compass 计数器(corpus_stats 同源;M2 改活取
        "ts": text("now()"),
    }
