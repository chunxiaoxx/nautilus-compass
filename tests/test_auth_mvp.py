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

@pytest.fixture(scope="module")
def client(http_client):
    """Shared session client (the app's session manager is single-lifespan);
    isolation via unique emails. See tests/conftest.py."""
    return http_client


def _mk_user(client, email):
    client.post("/signup", json={"email": email, "passphrase": "pw"})
    r = client.post("/login", json={"email": email, "passphrase": "pw"})
    return r.json()["user_id"], {"Authorization": f"Bearer {r.json()['token']}"}


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


# ── MVP-3: self-service token API over JWT ───────────────────────────

def test_http_token_lifecycle(client):
    uid, hdr = _mk_user(client, "t1@x.io")

    r = client.post("/tokens", json={"name": "ci"}, headers=hdr)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["token"].startswith("cmp_live_")
    assert body["scopes"] == f"read:{uid},write:{uid}"   # own space, read+write
    assert len(body["token"]) > len(body["token_id"])   # plaintext only here

    r = client.get("/tokens", headers=hdr)
    assert r.status_code == 200
    rows = r.json()["tokens"]
    assert len(rows) == 1 and rows[0]["revoked"] is False
    assert "token" not in rows[0]                       # never echoed back

    r = client.delete(f"/tokens/{rows[0]['token_id']}", headers=hdr)
    assert r.status_code == 200
    assert client.get("/tokens", headers=hdr).json()["tokens"][0]["revoked"] is True


def test_http_tokens_require_valid_jwt(client):
    assert client.get("/tokens",
                      headers={"Authorization": "Bearer nope"}).status_code == 401
    assert client.post("/tokens", json={}).status_code == 401


# ── MVP-4: pages ─────────────────────────────────────────────────────

def test_http_pages_served(client):
    r = client.get("/signup")
    assert r.status_code == 200
    assert "<form" in r.text and "doSignup" in r.text
    r = client.get("/console")
    assert r.status_code == 200
    assert "doLogin" in r.text and "revoke" in r.text


# ── MVP-6: four-probe auth self-check (HANDOFF_20260831 #6) ──────────

def _rpc(client, token, tool, args):
    return client.post(
        "/mcp",
        headers={"Authorization": f"Bearer {token}",
                 "Accept": "application/json, text/event-stream"},
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
              "params": {"name": tool, "arguments": args}},
    )


def test_four_probes(client):
    uid_a, hdr_a = _mk_user(client, "pa@x.io")
    uid_b, _ = _mk_user(client, "pb@x.io")
    tok = client.post("/tokens", json={"name": "probe"},
                      headers=hdr_a).json()["token"]

    # P1 cross-user read DENY
    r = _rpc(client, tok, "recall", {"project": uid_b, "query": "q"})
    assert r.status_code == 200 and "forbidden" in r.text, r.text

    # P2 cross-user write DENY
    r = _rpc(client, tok, "ingest_obs", {"project": uid_b, "name": "x", "concept": "gotcha"})
    assert r.status_code == 200 and "forbidden" in r.text, r.text

    # P3 same-user own space NOT scope-denied (read AND write)
    r = _rpc(client, tok, "recall", {"project": uid_a, "query": "q"})
    assert r.status_code == 200 and "forbidden" not in r.text, r.text
    r = _rpc(client, tok, "ingest_obs",
             {"project": uid_a, "name": "probe-own", "concept": "gotcha"})
    assert r.status_code == 200 and "forbidden" not in r.text, r.text

    # P4 revoke → immediate 401
    tid = client.get("/tokens", headers=hdr_a).json()["tokens"][0]["token_id"]
    assert client.delete(f"/tokens/{tid}", headers=hdr_a).status_code == 200
    r = _rpc(client, tok, "recall", {"project": uid_a, "query": "q"})
    assert r.status_code == 401, r.status_code
