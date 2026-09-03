"""MVP-2 auth tests: signup + login (JWT) on the 8097 service.

Logic layer (auth_api) tested directly with a tmp DB; HTTP layer via
Starlette TestClient against the real app routes.

Runs:  pytest tests/test_auth_mvp.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

import jwt as pyjwt  # noqa: E402
import pytest  # noqa: E402

import auth_api as auth  # noqa: E402
import mcp_storage as st  # noqa: E402


@pytest.fixture()
def db(tmp_path):
    conn = st.init_db(tmp_path / "mvp.db")
    yield conn
    conn.close()


# ── logic layer ──────────────────────────────────────────────────────

def test_signup_creates_user_with_scrypt_hash(db):
    out = auth.signup_user(db, email="u@x.io", passphrase="pw123", region="cn")
    row = st.get_user_by_email(db, "u@x.io")
    assert row["user_id"] == out["user_id"]
    assert row["passphrase_hash"] != "pw123"          # hashed, not stored raw
    assert len(row["passphrase_hash"]) == 64           # scrypt dklen=32 hex


def test_signup_duplicate_email_conflict(db):
    auth.signup_user(db, email="u@x.io", passphrase="pw123")
    with pytest.raises(auth.ConflictError):
        auth.signup_user(db, email="u@x.io", passphrase="other")


def test_login_ok_returns_verifiable_jwt(db):
    auth.signup_user(db, email="u@x.io", passphrase="pw123")
    out = auth.login_user(db, email="u@x.io", passphrase="pw123")
    claims = pyjwt.decode(out["token"], auth.jwt_secret(),
                          algorithms=["HS256"])
    assert claims["sub"] == out["user_id"]
    assert claims["exp"] > claims["iat"]


def test_login_wrong_passphrase_rejected(db):
    auth.signup_user(db, email="u@x.io", passphrase="pw123")
    with pytest.raises(auth.AuthError):
        auth.login_user(db, email="u@x.io", passphrase="wrong")
    with pytest.raises(auth.AuthError):               # unknown email: same error
        auth.login_user(db, email="nobody@x.io", passphrase="pw123")


# ── HTTP layer (real routes on the 8097 app) ─────────────────────────

@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("COMPASS_MVP_DB", str(tmp_path / "http.db"))
    from mcp_http_server import app
    from starlette.testclient import TestClient
    with TestClient(app) as c:
        yield c


def test_http_signup_login_flow(client):
    # One TestClient session (the app's session manager is single-lifespan).
    r = client.post("/signup", json={"email": "h@x.io", "passphrase": "pw"})
    assert r.status_code == 200, r.text
    user_id = r.json()["user_id"]

    r = client.post("/login", json={"email": "h@x.io", "passphrase": "pw"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["user_id"] == user_id
    assert body["token"].count(".") == 2               # JWT shape

    # conflict + wrong passphrase + unknown email
    assert client.post("/signup",
                       json={"email": "h@x.io", "passphrase": "pw"}).status_code == 409
    assert client.post("/login",
                       json={"email": "h@x.io", "passphrase": "bad"}).status_code == 401
    assert client.post("/login",
                       json={"email": "nobody@x.io", "passphrase": "pw"}).status_code == 401
