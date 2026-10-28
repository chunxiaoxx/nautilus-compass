# -*- coding: utf-8 -*-
"""Users API(2026-10-09 · 网站 B 档恢复 R3 · 用户拍 SPA auth 主通道)
SPA 用户中心 12 端点 + auth 会话补端点 5 个。
纪律:只读自己(公开档白字段);rate limit 同 auth.py;role 三档
(member=人类成员白名单 / admin=agent 管理员 / user=普通)随本文件落地。"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBasicCredentials  # noqa: F401 (与 auth.py 同款依赖面)
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from models.database import User
from utils.auth import get_current_user, hash_password, verify_password, create_access_token
from utils.database import get_db

users_router = APIRouter()
auth_session_router = APIRouter()

_BOOTED = False
# M2 三档:人类成员白名单(与平台 admin 一致)——role 列落地后按此初始化
_MEMBER_EMAILS = {"chunxiaoxx@gmail.com", "chunxiaoxx+external@gmail.com"}


def _ensure(db: Session) -> None:
    """加列自愈(users 表 9 月已在,avatar_url/role 为 R3 新增)。"""
    global _BOOTED
    if _BOOTED:
        return
    db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(400)"))
    db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'user'"))
    # 白名单人类成员升 member
    for em in _MEMBER_EMAILS:
        db.execute(text("UPDATE users SET role='member' WHERE email=:e AND role='user'"), {"e": em})
    db.commit()
    _BOOTED = True


def _public(u: User) -> dict:
    return {"id": u.id, "username": u.username, "email": u.email,
            "wallet_address": u.wallet_address, "avatar_url": getattr(u, "avatar_url", None),
            "role": getattr(u, "role", "user"), "is_admin": bool(u.is_admin),
            "created_at": u.created_at.isoformat() if u.created_at else None}


def _me_priv(u: User) -> dict:
    d = _public(u)
    d["is_active"] = bool(u.is_active)
    return d


def _agent_of(db: Session, u: User):
    """钱包地址↔platform_agents 映射(取第一个命中;无则 None)。"""
    if not u.wallet_address:
        return None
    row = db.execute(text(
        "SELECT agent_id FROM platform_agents "
        "WHERE lower(wallet_address)=lower(:w) OR lower(owner)=lower(:w) LIMIT 1"),
        {"w": u.wallet_address}).first()
    return row[0] if row else None


# ───────────────────────── /api/users ─────────────────────────

@users_router.get("/profile")
def profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _ensure(db)
    return {"success": True, "data": {"user": _me_priv(current_user)}}


@users_router.get("/stats")
def stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _ensure(db)
    ag = _agent_of(db, current_user)
    bounties_done = assays = nau = 0
    if ag:
        r = db.execute(text(
            "SELECT count(*) FILTER (WHERE status IN ('completed','settled')), "
            "COALESCE((SELECT nau_balance FROM platform_agents WHERE agent_id=:a),0) "
            "FROM platform_bounties WHERE claimed_by=:a"), {"a": ag}).first()
        bounties_done, nau = int(r[0] or 0), int(r[1] or 0)
    ar = db.execute(text(
        "SELECT count(*) FROM assay_submissions WHERE lower(contact)=lower(:e)"),
        {"e": current_user.email or ""}).first()
    assays = int(ar[0] or 0)
    return {"success": True, "data": {"bounties_completed": bounties_done,
            "assay_submissions": assays, "nau_balance": nau,
            "mapped_agent": ag}}


@users_router.get("/leaderboard")
def leaderboard(db: Session = Depends(get_db)):
    _ensure(db)
    rows = db.execute(text(
        "SELECT agent_id, name, nau_balance, reputation FROM platform_agents "
        "WHERE nau_balance > 0 ORDER BY nau_balance DESC LIMIT 50")).fetchall()
    return {"success": True, "data": {"leaderboard": [
        {"rank": i + 1, "agent_id": r[0], "name": r[1],
         "nau_balance": int(r[2] or 0), "reputation": int(r[3] or 0)}
        for i, r in enumerate(rows)]}}


@users_router.get("/history")
def history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _ensure(db)
    ag = _agent_of(db, current_user)
    items = []
    if ag:
        rows = db.execute(text(
            "SELECT bounty_id, title, status, reward_nau, created_at FROM platform_bounties "
            "WHERE claimed_by=:a ORDER BY created_at DESC LIMIT 25"), {"a": ag}).fetchall()
        items += [{"type": "bounty", "id": r[0], "title": r[1], "status": r[2],
                   "reward": int(r[3] or 0),
                   "at": r[4].isoformat() if r[4] else None} for r in rows]
    rows = db.execute(text(
        "SELECT id, harness, lane, status, created_at FROM assay_submissions "
        "WHERE lower(contact)=lower(:e) ORDER BY created_at DESC LIMIT 25"),
        {"e": current_user.email or ""}).fetchall()
    items += [{"type": "assay", "id": r[0], "title": r[1], "lane": r[2], "status": r[3],
               "at": r[4].isoformat() if r[4] else None} for r in rows]
    items.sort(key=lambda x: x.get("at") or "", reverse=True)
    return {"success": True, "data": {"history": items[:40]}}


@users_router.get("/me/summary")
def me_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"success": True, "data": {"user": _me_priv(current_user), "stats": stats(current_user, db)["data"]}}


@users_router.get("/{user_id}")
def public_profile(user_id: int, db: Session = Depends(get_db)):
    _ensure(db)
    u = db.query(User).filter(User.id == user_id, User.is_active == True).first()  # noqa: E712
    if not u:
        raise HTTPException(404, "user not found")
    return {"success": True, "data": {"user": _public(u)}}


@users_router.get("/{user_id}/stats")
def public_stats(user_id: int, db: Session = Depends(get_db)):
    _ensure(db)
    u = db.query(User).filter(User.id == user_id, User.is_active == True).first()  # noqa: E712
    if not u:
        raise HTTPException(404, "user not found")
    return {"success": True, "data": {"user_id": user_id, "username": u.username,
            "member_since": u.created_at.isoformat() if u.created_at else None}}


class AvatarReq(BaseModel):
    avatar_url: str = Field(max_length=400)


@users_router.post("/avatar")
def set_avatar(req: AvatarReq, current_user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    _ensure(db)
    if not req.avatar_url.startswith(("http://", "https://")):
        raise HTTPException(422, "avatar_url must be http(s) URL")
    db.execute(text("UPDATE users SET avatar_url=:a WHERE id=:i"),
               {"a": req.avatar_url[:400], "i": current_user.id})
    db.commit()
    return {"success": True, "data": {"avatar_url": req.avatar_url[:400]}}


class ChangePwdReq(BaseModel):
    old_password: str = Field(min_length=6, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


@users_router.post("/change-password")
def change_password(req: ChangePwdReq, current_user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if not verify_password(req.old_password, current_user.hashed_password):
        raise HTTPException(401, "old password incorrect")
    db.execute(text("UPDATE users SET hashed_password=:h, updated_at=NOW() WHERE id=:i"),
               {"h": hash_password(req.new_password), "i": current_user.id})
    db.commit()
    return {"success": True, "data": {"changed": True}}


@users_router.delete("/delete-account")
def delete_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.execute(text("UPDATE users SET is_active=false, updated_at=NOW() WHERE id=:i"),
               {"i": current_user.id})
    db.commit()
    return {"success": True, "data": {"deleted": True, "note": "软删(可恢复);数据保留"}}


# ───────────────────────── /api/auth 会话补端点 ─────────────────────────

@auth_session_router.post("/logout")
def logout():
    """无状态 JWT:客户端清 token 即登出;服务端返回 ok(v2 可选黑名单)。"""
    return {"success": True, "data": {"message": "logged out (clear token client-side)"}}


@auth_session_router.post("/refresh")
def refresh(current_user: User = Depends(get_current_user)):
    token = create_access_token(data={"sub": str(current_user.id)})
    return {"success": True, "data": {"access_token": token, "token_type": "bearer"}}


@auth_session_router.get("/profile")
def auth_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _ensure(db)
    return {"success": True, "data": {"user": _me_priv(current_user)}}


class ResetReq(BaseModel):
    email: str = Field(max_length=200)


@auth_session_router.post("/password-reset/request")
def reset_request(req: ResetReq, db: Session = Depends(get_db)):
    _ensure(db)
    u = db.query(User).filter(User.email == req.email).first()
    # 不存在也返回 ok(防枚举);存在则发 M1 验证码通道
    if u:
        import httpx
        import os
        try:
            httpx.post(
                f"{os.getenv('SELF_BASE', 'http://localhost:8000')}/api/platform/identity/request-code",
                json={"email": req.email}, timeout=8)
        except Exception:
            pass
    return {"success": True, "data": {"sent": True}}


class ResetConfirmReq(BaseModel):
    email: str = Field(max_length=200)
    code: str = Field(min_length=4, max_length=8)
    new_password: str = Field(min_length=8, max_length=128)


@auth_session_router.post("/password-reset/confirm")
def reset_confirm(req: ResetConfirmReq, db: Session = Depends(get_db)):
    """验 M1 码(identity_codes 明文码,email 主键单行)后改密;用后删=消费。"""
    row = db.execute(text(
        "SELECT code, expires_at FROM identity_codes "
        "WHERE email=:e ORDER BY created_at DESC LIMIT 1"),
        {"e": req.email}).first()
    if not row or row[1] < datetime.now(timezone.utc):
        raise HTTPException(401, "code expired or not found")
    if str(row[0]).strip() != req.code.strip():
        raise HTTPException(401, "code incorrect")
    u = db.query(User).filter(User.email == req.email).first()
    if not u:
        raise HTTPException(404, "user not found")
    db.execute(text("UPDATE users SET hashed_password=:h, updated_at=NOW() WHERE id=:i"),
               {"h": hash_password(req.new_password), "i": u.id})
    db.execute(text("DELETE FROM identity_codes WHERE email=:e"), {"e": req.email})
    db.commit()
    return {"success": True, "data": {"reset": True}}
