# -*- coding: utf-8 -*-
"""统一身份层 M1(用户裁提前,2026-10-08):邮箱码登录+JWT 验签。
三类端点:request-code(Gmail 发码)/verify(码换 JWT 7d)/whoami(验签)。
密钥:IDENTITY_JWT_SECRET 环境变量(缺省时启动报错——禁硬编码)。
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request
import logging

logger = logging.getLogger(__name__)
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import text

from utils.database import get_db

router = APIRouter(prefix="/api/platform/identity", tags=["Identity M1 (unified)"])

_SECRET = None


def _secret() -> bytes:
    global _SECRET
    if _SECRET is None:
        import os
        s = os.environ.get("IDENTITY_JWT_SECRET")
        if not s:
            raise HTTPException(503, "IDENTITY_JWT_SECRET not configured")
        _SECRET = s.encode()
    return _SECRET


def _ensure(db) -> None:
    db.execute(text("""CREATE TABLE IF NOT EXISTS identity_codes (
        email varchar(200) PRIMARY KEY, code varchar(6) NOT NULL,
        expires_at timestamptz NOT NULL, created_at timestamptz DEFAULT now())"""))
    db.execute(text("""CREATE TABLE IF NOT EXISTS identity_users (
        email varchar(200) PRIMARY KEY, subject uuid NOT NULL DEFAULT gen_random_uuid(),
        type varchar(10) NOT NULL DEFAULT 'human', created_at timestamptz DEFAULT now())"""))
    db.commit()


def _jwt(payload: dict, days: int = 7) -> str:
    body = dict(payload, exp=int(time.time()) + days * 86400, jti=uuid.uuid4().hex)
    head = base64.urlsafe_b64encode(json.dumps({"alg": "HS256"}).encode()).rstrip(b"=")
    body_b = base64.urlsafe_b64encode(json.dumps(body).encode()).rstrip(b"=")
    sig = hmac.new(_secret(), head + b"." + body_b, hashlib.sha256).hexdigest()
    return f"{head.decode()}.{body_b.decode()}.{sig}"


def verify_jwt(token: str) -> dict:
    try:
        h, b, sig = token.split(".")
        expect = hmac.new(_secret(), f"{h}.{b}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expect):
            raise ValueError("bad sig")
        payload = json.loads(base64.urlsafe_b64decode(b + "=" * (-len(b) % 4)))
        if payload.get("exp", 0) < time.time():
            raise ValueError("expired")
        return payload
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(401, f"invalid token: {e}")


class CodeReq(BaseModel):
    email: EmailStr


class VerifyReq(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


_RATE: dict = {}

@router.post("/request-code")
def request_code(req: CodeReq, request: Request, db=Depends(get_db)):
    """发 6 位码(Gmail 通道)。P0:dev_code 已移除;IP 限流 10/h 防码轰炸。"""
    _ensure(db)
    import time as _t
    from fastapi import Request as _R
    ip = request.client.host if (request and request.client) else "?"
    now = _t.time()
    win = [t for t in _RATE.get(ip, []) if now - t < 3600]
    if len(win) >= 10:
        raise HTTPException(429, "rate limited (10/h per IP)")
    win.append(now); _RATE[ip] = win
    code = f"{secrets.randbelow(1000000):06d}"
    db.execute(text(
        "INSERT INTO identity_codes (email, code, expires_at) VALUES (:e,:c,now()+interval '10 min') "
        "ON CONFLICT (email) DO UPDATE SET code=:c, expires_at=now()+interval '10 min'"),
        {"e": req.email, "c": code})
    db.commit()
    sent = False
    try:  # Gmail 通道(agent_mail.py);失败用户可重试,P0 后不再回码(compass #10833:
        # dev_code 明文回码=任意邮箱账户接管链,开业即关)
        import subprocess
        r = subprocess.run(
            ["python3", "ops/agent_mail.py", "--to", req.email,
             "--subject", "Nautilus 登录验证码",
             "--body", f"你的登录验证码:{code}(10 分钟内有效)。若非本人操作请忽略。"],
            capture_output=True, text=True, timeout=30)
        sent = r.returncode == 0
    except Exception:
        sent = False
    if not sent:
        logger.warning(f"request-code: mail delivery FAILED for {req.email} (no dev_code returned)")
    return {"ok": True, "email_sent": sent}


@router.post("/verify")
def verify(req: VerifyReq, db=Depends(get_db)):
    _ensure(db)
    row = db.execute(text(
        "SELECT code, expires_at > now() FROM identity_codes WHERE email=:e"),
        {"e": req.email}).first()
    if not row or row[0] != req.code or not row[1]:
        raise HTTPException(401, "invalid or expired code")
    db.execute(text("DELETE FROM identity_codes WHERE email=:e"), {"e": req.email})
    u = db.execute(text(
        "INSERT INTO identity_users (email) VALUES (:e) "
        "ON CONFLICT (email) DO UPDATE SET email=EXCLUDED.email RETURNING subject, type"),
        {"e": req.email}).first()
    db.commit()
    token = _jwt({"sub": str(u[0]), "email": req.email, "type": u[1]})
    return {"access_token": token, "token_type": "bearer", "expires_in": 7 * 86400}


@router.get("/whoami")
def whoami(authorization: str = Header("")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing bearer token")
    p = verify_jwt(authorization[7:])
    return {"subject": p.get("sub"), "email": p.get("email"), "type": p.get("type"),
            "expires": p.get("exp")}
