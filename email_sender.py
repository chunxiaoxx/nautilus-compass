"""Verification-email sender for the hosted signup flow (pre-launch hardening).

Two backends, chosen by env (stdlib only, zero new dependencies):

Gmail API (preferred in prod; reuse of the gmail-mcp OAuth grant, scope
gmail.modify which includes messages.send):
    COMPASS_GMAIL_REFRESH_TOKEN  OAuth refresh token
    COMPASS_GMAIL_CLIENT_ID / COMPASS_GMAIL_CLIENT_SECRET
    COMPASS_GMAIL_FROM           the Gmail address sending

SMTP fallback:
    COMPASS_SMTP_HOST   e.g. smtp.qq.com (empty = sending unavailable)
    COMPASS_SMTP_PORT   587 STARTTLS (default) or 465 SSL
    COMPASS_SMTP_USER   login username (usually the from-address)
    COMPASS_SMTP_PASS   login password / provider authorization code
    COMPASS_SMTP_FROM   From header, defaults to COMPASS_SMTP_USER
"""
from __future__ import annotations

import base64
import json
import os
import smtplib
import urllib.parse
import urllib.request
from email.message import EmailMessage

_TIMEOUT_S = 15

_GMAIL_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

urllib_request_urlopen = urllib.request.urlopen   # mock seam for tests


class EmailSendError(Exception):
    """Send failed (maps to 503 at the HTTP layer)."""


class EmailNotConfigured(Exception):
    """Neither Gmail nor SMTP env is configured."""


def _body(code: str) -> str:
    return (
        f"Your nautilus-compass verification code: {code}\n\n"
        "It expires in 30 minutes. If you did not sign up, ignore this "
        "email.\n\nnautilus-compass · local-first agent memory\n"
        "https://compass.nautilus.social\n")


def _send_via_gmail(msg: EmailMessage) -> None:
    """Refresh the OAuth grant and POST the MIME as Gmail API `raw`."""
    data = urllib.parse.urlencode({
        "client_id": os.environ["COMPASS_GMAIL_CLIENT_ID"],
        "client_secret": os.environ["COMPASS_GMAIL_CLIENT_SECRET"],
        "refresh_token": os.environ["COMPASS_GMAIL_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    try:
        with urllib_request_urlopen(_GMAIL_TOKEN_URL, data=data,
                                    timeout=_TIMEOUT_S) as resp:
            access = json.load(resp).get("access_token")
        if not access:
            raise EmailSendError("gmail token refresh returned no access_token")
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        req = urllib.request.Request(
            _GMAIL_SEND_URL, data=json.dumps({"raw": raw}).encode(),
            headers={"Authorization": f"Bearer {access}",
                     "Content-Type": "application/json"})
        with urllib_request_urlopen(req, timeout=_TIMEOUT_S) as resp:
            if resp.status != 200:
                raise EmailSendError(f"gmail send returned {resp.status}")
    except EmailSendError:
        raise
    except Exception as e:                    # URLError / HTTPError / JSONDecode
        raise EmailSendError(f"gmail api send failed: {e}") from e


def _send_via_smtp(msg: EmailMessage) -> None:
    host = os.environ["COMPASS_SMTP_HOST"]
    user = os.environ.get("COMPASS_SMTP_USER", "")
    password = os.environ.get("COMPASS_SMTP_PASS", "")
    port = int(os.environ.get("COMPASS_SMTP_PORT", "587"))
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


def send_verification_email(email: str, code: str) -> None:
    gmail_mode = bool(os.environ.get("COMPASS_GMAIL_REFRESH_TOKEN"))
    if not gmail_mode and not os.environ.get("COMPASS_SMTP_HOST"):
        raise EmailNotConfigured("no COMPASS_GMAIL_* or COMPASS_SMTP_* env")

    sender = (os.environ.get("COMPASS_GMAIL_FROM")
              or os.environ.get("COMPASS_SMTP_FROM")
              or os.environ.get("COMPASS_SMTP_USER") or "")
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = email
    msg["Subject"] = "nautilus-compass · your verification code"
    msg.set_content(_body(code))

    if gmail_mode:
        _send_via_gmail(msg)
    else:
        _send_via_smtp(msg)
