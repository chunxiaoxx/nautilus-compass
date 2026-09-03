"""MVP-1 storage-layer tests (HANDOFF_20260831_MULTITENANT_MVP #1).

Judging criteria: three tables created + read/write smoke. Pure sqlite3,
no HTTP, tmp_path DB per test.

Runs:  pytest tests/test_mcp_storage.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

import pytest  # noqa: E402

import mcp_storage as st  # noqa: E402


@pytest.fixture()
def db(tmp_path):
    conn = st.init_db(tmp_path / "mvp.db")
    yield conn
    conn.close()


def test_init_db_creates_three_tables(db):
    names = {r[0] for r in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"users", "agents", "observations"} <= names


def test_create_and_get_user(db):
    uid = st.create_user(db, email="a@b.c", passphrase_hash="x", region="cn")
    row = st.get_user_by_email(db, "a@b.c")
    assert row["user_id"] == uid
    assert row["plan"] == "free"


def test_duplicate_email_rejected(db):
    st.create_user(db, email="a@b.c", passphrase_hash="x")
    with pytest.raises(st.UserExistsError):
        st.create_user(db, email="a@b.c", passphrase_hash="y")


def test_register_and_list_agents(db):
    uid = st.create_user(db, email="a@b.c", passphrase_hash="x")
    aid = st.register_agent(db, user_id=uid, agent_type="claude-code",
                            device_id="dev1", workspace="w")
    rows = st.list_agents(db, uid)
    assert [r["agent_id"] for r in rows] == [aid]


def test_add_and_query_observations(db):
    uid = st.create_user(db, email="a@b.c", passphrase_hash="x")
    aid = st.register_agent(db, user_id=uid, agent_type="claude-code")
    st.add_observation(db, user_id=uid, agent_id=aid, ts="2026-09-04T00:00:00Z",
                       type="concept", concept="gpu-reuse", payload='{"k":1}')
    rows = st.list_observations(db, uid, obs_type="concept")
    assert len(rows) == 1
    assert rows[0]["concept"] == "gpu-reuse"


def test_foreign_key_enforced(db):
    with pytest.raises(st.StorageError):
        st.register_agent(db, user_id="no-such-user", agent_type="x")


def test_parameterized_query_rejects_injection(db):
    st.create_user(db, email="a@b.c", passphrase_hash="x")
    assert st.get_user_by_email(db, "a@b.c' OR '1'='1") is None


# ── MVP-3: self-service tokens ───────────────────────────────────────

def test_token_table_created(db):
    names = {r[0] for r in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert "mcp_tokens" in names


def test_token_create_list_revoke(db):
    uid = st.create_user(db, email="a@b.c", passphrase_hash="x")
    tid = st.create_token(db, user_id=uid, token_hash="h" * 64,
                          prefix="cmp_live_ab", name="ci", scopes="read:" + uid)
    rows = st.list_tokens(db, uid)
    assert [r["token_id"] for r in rows] == [tid]
    assert rows[0]["revoked_ts"] is None
    st.revoke_token(db, uid, tid)
    rows = st.list_tokens(db, uid)
    assert rows[0]["revoked_ts"] is not None


def test_token_isolated_between_users(db):
    u1 = st.create_user(db, email="a@b.c", passphrase_hash="x")
    u2 = st.create_user(db, email="d@e.f", passphrase_hash="y")
    st.create_token(db, user_id=u1, token_hash="h" * 64,
                    prefix="p1", name="n", scopes="read")
    assert st.list_tokens(db, u2) == []
