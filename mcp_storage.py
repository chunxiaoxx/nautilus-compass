"""MVP-1 storage layer: users / agents / observations (SQLite).

Schema mirrors the 8770 v0.9 reference design (model only, not code):
  users        user_id, email UNIQUE, region, passphrase_hash, encryption_salt,
               plan, created_ts
  agents       agent_id, user_id -> users, agent_type, device_id, workspace,
               metadata, created_ts
  observations obs_id, user_id -> users, agent_id -> agents, ts, type,
               concept, payload, created_ts

All queries parameterized. Connection uses FK enforcement + Row factory.
"""
from __future__ import annotations

import sqlite3
import uuid
from typing import Any

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id         TEXT PRIMARY KEY,
    email           TEXT NOT NULL UNIQUE,
    region          TEXT DEFAULT '',
    passphrase_hash TEXT NOT NULL,
    encryption_salt TEXT DEFAULT '',
    plan            TEXT NOT NULL DEFAULT 'free',
    verified        INTEGER NOT NULL DEFAULT 0,
    created_ts      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS agents (
    agent_id    TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES users(user_id),
    agent_type  TEXT NOT NULL,
    device_id   TEXT DEFAULT '',
    workspace   TEXT DEFAULT '',
    metadata    TEXT DEFAULT '{}',
    created_ts  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS observations (
    obs_id     TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL REFERENCES users(user_id),
    agent_id   TEXT REFERENCES agents(agent_id),
    ts         TEXT NOT NULL,
    type       TEXT NOT NULL,
    concept    TEXT NOT NULL,
    payload    TEXT DEFAULT '{}',
    created_ts TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_obs_user_type ON observations(user_id, type, ts);
CREATE TABLE IF NOT EXISTS mcp_tokens (
    token_id   TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL REFERENCES users(user_id),
    token_hash TEXT NOT NULL UNIQUE,
    prefix     TEXT NOT NULL,
    name       TEXT DEFAULT '',
    scopes     TEXT NOT NULL DEFAULT '',
    created_ts TEXT NOT NULL,
    revoked_ts TEXT
);
CREATE TABLE IF NOT EXISTS email_verifications (
    email        TEXT PRIMARY KEY,
    code_hash    TEXT NOT NULL,
    expires_ts   TEXT NOT NULL,
    attempts     INTEGER NOT NULL DEFAULT 0,
    last_sent_ts TEXT NOT NULL
);
"""


class StorageError(Exception):
    """Base storage-layer error."""


class UserExistsError(StorageError):
    """Email already registered."""


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def init_db(path: Any) -> sqlite3.Connection:
    """Open (creating if needed) the DB and apply the schema. Returns conn."""
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(_SCHEMA)
    _migrate(conn)
    conn.commit()
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Add users.verified on first run after the gate ships. One-time
    backfill marks pre-existing accounts verified (ops/probe users must
    not be locked out; brand-new signups start at 0 via INSERT)."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
    if "verified" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN"
                     " verified INTEGER NOT NULL DEFAULT 0")
        conn.execute("UPDATE users SET verified = 1")


def create_user(conn: sqlite3.Connection, *, email: str, passphrase_hash: str,
                region: str = "", encryption_salt: str = "",
                plan: str = "free", verified: int = 0) -> str:
    user_id = uuid.uuid4().hex
    try:
        conn.execute(
            "INSERT INTO users (user_id, email, region, passphrase_hash,"
            " encryption_salt, plan, verified, created_ts)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (user_id, email, region, passphrase_hash, encryption_salt,
             plan, verified, _now()))
        conn.commit()
    except sqlite3.IntegrityError as e:
        raise UserExistsError(email) from e
    return user_id


def get_user_by_email(conn: sqlite3.Connection, email: str) -> sqlite3.Row | None:
    cur = conn.execute("SELECT * FROM users WHERE email = ?", (email,))
    return cur.fetchone()


# ── email verification (pre-launch gate, 2026-09-05) ────────────────

def store_verification_code(conn: sqlite3.Connection, *, email: str,
                            code_hash: str, expires_ts: str) -> None:
    conn.execute(
        "INSERT INTO email_verifications (email, code_hash, expires_ts,"
        " attempts, last_sent_ts) VALUES (?,?,?,0,?)"
        " ON CONFLICT(email) DO UPDATE SET code_hash=excluded.code_hash,"
        " expires_ts=excluded.expires_ts, attempts=0,"
        " last_sent_ts=excluded.last_sent_ts",
        (email, code_hash, expires_ts, _now()))
    conn.commit()


def get_verification(conn: sqlite3.Connection,
                     email: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM email_verifications WHERE email = ?",
                        (email,)).fetchone()


def bump_verification_attempts(conn: sqlite3.Connection, email: str,
                               attempts: int) -> None:
    conn.execute("UPDATE email_verifications SET attempts = ? WHERE email = ?",
                 (attempts, email))
    conn.commit()


def delete_verification(conn: sqlite3.Connection, email: str) -> None:
    conn.execute("DELETE FROM email_verifications WHERE email = ?", (email,))
    conn.commit()


def mark_verified(conn: sqlite3.Connection, email: str) -> None:
    conn.execute("UPDATE users SET verified = 1 WHERE email = ?", (email,))
    conn.commit()


def delete_user(conn: sqlite3.Connection, user_id: str) -> None:
    """Signup rollback only: drop an account that never got verified."""
    conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()


def register_agent(conn: sqlite3.Connection, *, user_id: str, agent_type: str,
                   device_id: str = "", workspace: str = "",
                   metadata: str = "{}") -> str:
    agent_id = uuid.uuid4().hex
    try:
        conn.execute(
            "INSERT INTO agents (agent_id, user_id, agent_type, device_id,"
            " workspace, metadata, created_ts) VALUES (?,?,?,?,?,?,?)",
            (agent_id, user_id, agent_type, device_id, workspace, metadata,
             _now()))
        conn.commit()
    except sqlite3.IntegrityError as e:
        raise StorageError(f"agent registration failed: {e}") from e
    return agent_id


def list_agents(conn: sqlite3.Connection, user_id: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM agents WHERE user_id = ? ORDER BY created_ts",
        (user_id,)).fetchall()


def add_observation(conn: sqlite3.Connection, *, user_id: str, agent_id: str,
                    ts: str, type: str, concept: str,
                    payload: str = "{}") -> str:
    obs_id = uuid.uuid4().hex
    try:
        conn.execute(
            "INSERT INTO observations (obs_id, user_id, agent_id, ts, type,"
            " concept, payload, created_ts) VALUES (?,?,?,?,?,?,?,?)",
            (obs_id, user_id, agent_id, ts, type, concept, payload, _now()))
        conn.commit()
    except sqlite3.IntegrityError as e:
        raise StorageError(f"observation insert failed: {e}") from e
    return obs_id


def list_observations(conn: sqlite3.Connection, user_id: str,
                      obs_type: str | None = None,
                      since_ts: str | None = None,
                      limit: int = 100) -> list[sqlite3.Row]:
    sql = "SELECT * FROM observations WHERE user_id = ?"
    args: list[Any] = [user_id]
    if obs_type is not None:
        sql += " AND type = ?"
        args.append(obs_type)
    if since_ts is not None:
        sql += " AND ts >= ?"
        args.append(since_ts)
    sql += " ORDER BY ts DESC LIMIT ?"
    args.append(int(limit))
    return conn.execute(sql, args).fetchall()


def create_token(conn: sqlite3.Connection, *, user_id: str, token_hash: str,
                 prefix: str, name: str = "", scopes: str = "") -> str:
    token_id = uuid.uuid4().hex
    try:
        conn.execute(
            "INSERT INTO mcp_tokens (token_id, user_id, token_hash, prefix,"
            " name, scopes, created_ts) VALUES (?,?,?,?,?,?,?)",
            (token_id, user_id, token_hash, prefix, name, scopes, _now()))
        conn.commit()
    except sqlite3.IntegrityError as e:
        raise StorageError(f"token insert failed: {e}") from e
    return token_id


def list_tokens(conn: sqlite3.Connection, user_id: str) -> list[sqlite3.Row]:
    """All tokens owned by the user, including revoked (UI shows history)."""
    return conn.execute(
        "SELECT * FROM mcp_tokens WHERE user_id = ? ORDER BY created_ts",
        (user_id,)).fetchall()


def find_token_by_hash(conn: sqlite3.Connection, token_hash: str) -> sqlite3.Row | None:
    cur = conn.execute(
        "SELECT * FROM mcp_tokens WHERE token_hash = ? AND revoked_ts IS NULL",
        (token_hash,))
    return cur.fetchone()


def revoke_token(conn: sqlite3.Connection, user_id: str, token_id: str) -> bool:
    """Soft-revoke scoped to the owning user. True if a row was updated."""
    cur = conn.execute(
        "UPDATE mcp_tokens SET revoked_ts = ? WHERE token_id = ? AND"
        " user_id = ? AND revoked_ts IS NULL", (_now(), token_id, user_id))
    conn.commit()
    return cur.rowcount > 0
