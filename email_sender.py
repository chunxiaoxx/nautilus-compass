"""Verification-email sender for the hosted signup flow (pre-launch hardening).

Stdlib smtplib only, zero new dependencies. Config via environment:
    COMPASS_SMTP_HOST   e.g. smtp.qq.com (empty = sending unavailable)
    COMPASS_SMTP_PORT   587 STARTTLS (default) or 465 SSL
    COMPASS_SMTP_USER   login username (usually the from-address)
    COMPASS_SMTP_PASS   login password / provider authorization code
    COMPASS_SMTP_FROM   From header, defaults to COMPASS_SMTP_USER
"""
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

_TIMEOUT_S = 15


class EmailSendError(Exception):
    """SMTP send failed (maps to 503 at the HTTP layer)."""


class EmailNotConfigured(Exception):
    """COMPASS_SMTP_HOST unset while verification is required."""


def _body(code: str) -> str:
    return (
        f"Your nautilus-compass verification code: {code}\n\n"
        "It expires in 30 minutes. If you did not sign up, ignore this "
        "email.\n\nnautilus-compass · local-first agent memory\n"
        "https://compass.nautilus.social\n")


def send_verification_email(email: str, code: str) -> None:
    host = os.environ.get("COMPASS_SMTP_HOST", "")
    if not host:
        raise EmailNotConfigured("COMPASS_SMTP_HOST is not set")
    user = os.environ.get("COMPASS_SMTP_USER", "")
    password = os.environ.get("COMPASS_SMTP_PASS", "")
    sender = os.environ.get("COMPASS_SMTP_FROM") or user
    port = int(os.environ.get("COMPASS_SMTP_PORT", "587"))

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = email
    msg["Subject"] = "nautilus-compass · your verification code"
    msg.set_content(_body(code))

    try:
        if port == 465:
            smtp: smtplib.SMTP = smtplib.SMTP_SSL(host, port, timeout=_TIMEOUT_S)
        else:
            smtp = smtplib.SMTP(host, port, timeout=_TIMEOUT_S)
        with smtp:
            if port != 465:
                smtp.starttls()
            if user:
                smtp.login(user, password)
            smtp.send_message(msg)
    except (smtplib.SMTPException, OSError) as e:
        raise EmailSendError(f"smtp send failed: {e}") from e
