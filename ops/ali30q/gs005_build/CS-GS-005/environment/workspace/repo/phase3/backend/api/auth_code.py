"""
Email/Phone verification code login.
No password needed. Works for both Chinese and international users.

Flow:
1. POST /api/auth/send-code {email: "xxx"} -> sends 6-digit code
2. POST /api/auth/verify-code {email: "xxx", code: "123456"} -> returns JWT
"""
import dns.resolver
import logging
import os
import random
import smtplib
import socket
import time
from datetime import timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from models.database import User
from utils.auth import create_access_token, hash_password
from utils.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory code store (production: use Redis)
_code_store: dict[str, tuple[str, float]] = {}  # email -> (code, expiry_timestamp)
CODE_EXPIRY = 300  # 5 minutes
CODE_LENGTH = 6

# SMTP config (optional - if not set, falls back to direct MX delivery)
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@nautilus.social")

# Direct MX delivery sender address
MX_FROM = os.getenv("MX_FROM", "noreply@nautilus.social")


def _generate_code() -> str:
    return str(random.randint(100000, 999999))


def _build_email_message(to: str, code: str, sender: str) -> MIMEMultipart:
    """Build a well-formatted verification email."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Nautilus - Your verification code: {code}"
    msg["From"] = f"Nautilus <{sender}>"
    msg["To"] = to
    msg["X-Mailer"] = "Nautilus Platform"

    text_body = (
        f"Your Nautilus verification code is: {code}\n\n"
        f"This code is valid for 5 minutes. Do not share it with anyone.\n\n"
        f"If you did not request this code, please ignore this email.\n\n"
        f"---\n"
        f"Nautilus - AI Agent Platform\n"
        f"https://nautilus.social"
    )

    html_body = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 480px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #1a1a2e; margin-bottom: 8px;">Nautilus</h2>
        <p style="color: #666; font-size: 14px;">Your verification code:</p>
        <div style="background: #f0f4ff; border-radius: 8px; padding: 20px; text-align: center; margin: 16px 0;">
            <span style="font-size: 32px; font-weight: bold; letter-spacing: 6px; color: #1a1a2e;">{code}</span>
        </div>
        <p style="color: #999; font-size: 12px;">Valid for 5 minutes. Do not share this code.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #bbb; font-size: 11px;">Nautilus - AI Agent Platform</p>
    </div>
    """

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    return msg


def _send_via_smtp(to: str, code: str) -> bool:
    """Send via configured SMTP relay. Returns False if not configured."""
    if not SMTP_HOST or not SMTP_USER:
        return False
    try:
        msg = _build_email_message(to, code, SMTP_FROM or SMTP_USER)
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(msg["From"], [to], msg.as_string())
        logger.info("Verification code sent via SMTP to %s", to)
        return True
    except Exception:
        logger.exception("SMTP send failed for %s", to)
        return False


def _send_via_mx(to: str, code: str) -> bool:
    """
    Send email directly by resolving MX record of recipient domain.
    This is a best-effort approach - may be rejected by some providers.
    """
    try:
        domain = to.split("@")[1]

        # Resolve MX records
        try:
            mx_records = dns.resolver.resolve(domain, "MX")
            mx_host = str(sorted(mx_records, key=lambda r: r.preference)[0].exchange).rstrip(".")
        except Exception:
            logger.warning("Could not resolve MX for %s, trying direct", domain)
            mx_host = domain

        msg = _build_email_message(to, code, MX_FROM)

        # Try to connect to MX server on port 25
        server = smtplib.SMTP(mx_host, 25, timeout=15)
        server.ehlo(socket.getfqdn())

        # Try STARTTLS if available
        try:
            server.starttls()
            server.ehlo(socket.getfqdn())
        except smtplib.SMTPException:
            pass  # Continue without TLS if not supported

        server.sendmail(MX_FROM, [to], msg.as_string())
        server.quit()

        logger.info("Verification code sent via MX to %s (mx=%s)", to, mx_host)
        return True
    except Exception:
        logger.exception("MX send failed for %s", to)
        return False


def _send_email(to: str, code: str) -> bool:
    """Send verification code via email. Tries SMTP relay first, then direct MX."""
    # Try SMTP relay first
    if _send_via_smtp(to, code):
        return True

    # Fall back to direct MX delivery
    if _send_via_mx(to, code):
        return True

    return False


class SendCodeRequest(BaseModel):
    email: EmailStr


class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str


@router.post("/send-code")
async def send_code(request: Request, data: SendCodeRequest):
    """Send a 6-digit verification code to the email address."""
    email = data.email.lower().strip()

    # Rate limit: max 1 code per 60 seconds per email
    existing = _code_store.get(email)
    if existing and time.time() - (existing[1] - CODE_EXPIRY) < 60:
        raise HTTPException(
            status_code=429,
            detail="请等待60秒后再发送验证码 / Please wait 60 seconds"
        )

    code = _generate_code()
    _code_store[email] = (code, time.time() + CODE_EXPIRY)

    email_sent = _send_email(email, code)

    response: dict = {
        "success": True,
        "message": "验证码已发送，请查收邮件" if email_sent else "验证码已生成",
        "email": email,
    }

    # If email not sent, return code directly (for testing / fallback)
    if not email_sent:
        response["code"] = code
        response["note"] = "邮件发送失败，验证码直接返回（测试模式）"

    return response


@router.post("/verify-code")
async def verify_code(request: Request, data: VerifyCodeRequest):
    """Verify the code and return a JWT token. Auto-creates account if needed."""
    email = data.email.lower().strip()
    code = data.code.strip()

    stored = _code_store.get(email)
    if not stored:
        raise HTTPException(status_code=400, detail="请先获取验证码")

    stored_code, expiry = stored
    if time.time() > expiry:
        _code_store.pop(email, None)
        raise HTTPException(status_code=400, detail="验证码已过期，请重新获取")

    if code != stored_code:
        raise HTTPException(status_code=400, detail="验证码错误")

    # Code verified, clean up
    _code_store.pop(email, None)

    # Find or create user
    db = next(get_db())
    try:
        user = db.query(User).filter(User.email == email).first()

        if not user:
            # Auto-create account
            username = email.split("@")[0]
            # Ensure unique username
            existing = db.query(User).filter(User.username == username).first()
            if existing:
                username = f"{username}_{random.randint(1000, 9999)}"

            user = User(
                username=username,
                email=email,
                hashed_password=hash_password(f"auto_{random.randint(100000, 999999)}"),
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("Auto-created user for email %s: username=%s", email, username)

        # Generate JWT
        token = create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(days=7),
        )

        return {
            "success": True,
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },
        }
    finally:
        db.close()
