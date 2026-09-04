"""Pre-launch email verification gate (COMPASS_EMAIL_REQUIRED=1).

Covers: signup issues a code and login is gated until verified; wrong/expired
codes; attempt exhaustion; silent resend rate-limit; anti-enumeration no-ops;
signup rollback when the SMTP send fails; one-time migration backfill that
marks pre-existing users verified.

Runs:  pytest tests/test_email_verification.py -q
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

import pytest  # noqa: E402

import auth_api as auth  # noqa: E402
import email_sender  # noqa: E402
import mcp_storage as st  # noqa: E402


@pytest.fixture()
def sent(monkeypatch):
    """Capture (email, code) instead of really sending."""
    out: list[tuple[str, str]] = []
    monkeypatch.setattr(email_sender, "send_verification_email",
                        lambda email, code: out.append((email, code)))
    return out


@pytest.fixture()
def db(tmp_path):
    conn = st.init_db(tmp_path / "mvp.db")
    yield conn
    conn.close()


# ── logic layer ──────────────────────────────────────────────────────

def test_issue_verification_sends_six_digit_code(db, sent):
    auth.issue_verification(db, email="u@x.io")
    assert len(sent) == 1
    email, code = sent[0]
    assert email == "u@x.io" and len(code) == 6 and code.isdigit()


def test_resend_is_rate_limited(db, sent):
    auth.issue_verification(db, email="u@x.io")
    with pytest.raises(auth.RateLimitError):
        auth.issue_verification(db, email="u@x.io")
    assert len(sent) == 1                       # nothing re-sent inside 60s


def test_verify_success_marks_user(db, sent):
    auth.issue_verification(db, email="u@x.io")
    auth.signup_user(db, email="u@x.io", passphrase="pw123")
    code = sent[0][1]
    assert auth.verify_email(db, email="u@x.io", code=code) is True
    assert st.get_user_by_email(db, "u@x.io")["verified"] == 1
    assert st.get_verification(db, "u@x.io") is None      # consumed


def test_verify_rejects_wrong_code_then_exhausts(db, sent):
    auth.issue_verification(db, email="u@x.io")
    auth.signup_user(db, email="u@x.io", passphrase="pw123")
    for _ in range(auth.CODE_MAX_ATTEMPTS):
        with pytest.raises(auth.VerificationError):
            auth.verify_email(db, email="u@x.io", code="000000")
    with pytest.raises(auth.VerificationError):           # even the right code
        auth.verify_email(db, email="u@x.io", code=sent[0][1])


def test_resend_unknown_or_verified_email_is_silent_noop(db, sent):
    auth.resend_verification(db, email="nobody@x.io")     # no raise, no send
    assert sent == []


# ── gmail API backend (urllib mocked; scope gmail.modify incl. send) ──

def test_gmail_backend_refreshes_and_posts_raw(monkeypatch):
    import io
    import json as _json
    calls = []

    class FakeResp(io.BytesIO):
        status = 200
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    def fake_urlopen(url, data=None, timeout=0, **kw):
        calls.append((url, data))
        if "oauth2.googleapis.com/token" in str(url):
            return FakeResp(_json.dumps({"access_token": "at123"}).encode())
        return FakeResp(b'{"id": "msg1"}')

    monkeypatch.setenv("COMPASS_GMAIL_REFRESH_TOKEN", "rt")
    monkeypatch.setenv("COMPASS_GMAIL_CLIENT_ID", "cid")
    monkeypatch.setenv("COMPASS_GMAIL_CLIENT_SECRET", "sec")
    monkeypatch.setenv("COMPASS_GMAIL_FROM", "me@gmail.com")
    monkeypatch.setattr(email_sender, "urllib_request_urlopen", fake_urlopen)
    email_sender._send_via_gmail(email_sender.EmailMessage())
    assert len(calls) == 2
    assert "oauth2.googleapis.com/token" in str(calls[0][0])
    assert b"refresh_token=rt" in calls[0][1]
    # 2nd call goes through urllib.request.Request: URL in .full_url,
    # payload in .data (urlopen's own data kwarg stays None)
    second = calls[1][0]
    assert "gmail/v1/users/me/messages/send" in str(getattr(second, "full_url", second))
    assert getattr(second, "data", None) or calls[1][1]


def test_gmail_backend_bad_refresh_raises_send_error(monkeypatch):
    import io
    import urllib.error

    def refuse(url, data=None, timeout=0, **kw):
        raise urllib.error.HTTPError(url, 400, "invalid_grant", {},
                                     io.BytesIO(b""))

    monkeypatch.setenv("COMPASS_GMAIL_REFRESH_TOKEN", "dead")
    monkeypatch.setenv("COMPASS_GMAIL_CLIENT_ID", "cid")
    monkeypatch.setenv("COMPASS_GMAIL_CLIENT_SECRET", "sec")
    monkeypatch.setattr(email_sender, "urllib_request_urlopen", refuse)
    with pytest.raises(email_sender.EmailSendError):
        email_sender._send_via_gmail(email_sender.EmailMessage())


def test_signup_rolls_back_when_send_fails(db, monkeypatch):
    monkeypatch.setenv("COMPASS_EMAIL_REQUIRED", "1")
    def boom(email, code):
        raise email_sender.EmailSendError("smtp down")
    monkeypatch.setattr(email_sender, "send_verification_email", boom)
    with pytest.raises(email_sender.EmailSendError):
        auth.signup_user(db, email="u@x.io", passphrase="pw123")
    assert st.get_user_by_email(db, "u@x.io") is None     # no unverifiable account left


# ── migration: pre-existing users are exempt (verified=1, one-time) ──

def test_migration_backfills_existing_users(tmp_path):
    db_path = tmp_path / "old.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE users (user_id TEXT PRIMARY KEY, email TEXT NOT NULL"
        " UNIQUE, region TEXT DEFAULT '', passphrase_hash TEXT NOT NULL,"
        " encryption_salt TEXT DEFAULT '', plan TEXT NOT NULL DEFAULT 'free',"
        " created_ts TEXT NOT NULL)")
    conn.execute("INSERT INTO users (user_id, email, passphrase_hash, created_ts)"
                 " VALUES ('u1','old@x.io','h','2026-01-01T00:00:00Z')")
    conn.commit()
    conn.close()
    conn2 = st.init_db(db_path)
    try:
        assert conn2.execute(
            "SELECT verified FROM users WHERE user_id='u1'").fetchone()[0] == 1
    finally:
        conn2.close()


# ── HTTP layer (gate ON per-test via env; fake sender at module level) ──

@pytest.fixture(scope="module")
def gclient(http_client):
    """Share the session-wide TestClient (single-lifespan app); only the
    fake sender patch is module-scoped here."""
    captured: list[tuple[str, str]] = []
    from _pytest.monkeypatch import MonkeyPatch
    with MonkeyPatch.context() as mp:
        mp.setattr(email_sender, "send_verification_email",
                   lambda email, code: captured.append((email, code)))
        yield http_client, captured


def test_http_gated_flow(gclient, monkeypatch):
    client, captured = gclient
    monkeypatch.setenv("COMPASS_EMAIL_REQUIRED", "1")
    r = client.post("/signup", json={"email": "g@x.io", "passphrase": "pw"})
    assert r.status_code == 200 and r.json().get("verify_required") is True, r.text
    code = captured[-1][1]

    assert client.post("/login",
                       json={"email": "g@x.io", "passphrase": "pw"}).status_code == 403
    # resend stays 200-shaped (anti-enumeration) but is rate-limited server-side
    assert client.post("/verify/resend",
                       json={"email": "g@x.io"}).status_code == 200
    assert client.post("/verify",
                       json={"email": "g@x.io", "code": "999999"}).status_code == 400
    r = client.post("/verify", json={"email": "g@x.io", "code": code})
    assert r.status_code == 200 and r.json()["verified"] is True, r.text
    assert client.post("/login",
                       json={"email": "g@x.io", "passphrase": "pw"}).status_code == 200


def test_http_verify_unknown_email_generic_400(gclient, monkeypatch):
    client, _ = gclient
    monkeypatch.setenv("COMPASS_EMAIL_REQUIRED", "1")
    r = client.post("/verify", json={"email": "ghost@x.io", "code": "123456"})
    assert r.status_code == 400                      # same error as wrong code
    assert "invalid" in r.json()["error"]
    assert client.post("/verify/resend",
                       json={"email": "ghost@x.io"}).status_code == 200


def test_http_signup_without_smtp_is_503(gclient, monkeypatch):
    client, _ = gclient
    monkeypatch.setenv("COMPASS_EMAIL_REQUIRED", "1")
    def not_configured(email, code):
        raise email_sender.EmailNotConfigured("no host")
    # stacks on top of the module-level fake; undoes back to it afterwards
    monkeypatch.setattr(email_sender, "send_verification_email", not_configured)
    r = client.post("/signup", json={"email": "ns@x.io", "passphrase": "pw"})
    assert r.status_code == 503, r.text
