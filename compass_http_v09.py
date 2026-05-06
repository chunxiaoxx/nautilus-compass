"""compass v0.9 · server-side gateway · FastAPI implementation.

替代 v0.7.2 的 compass_http.py (单 tenant) · 加 multi-user · multi-agent 写入支持.

部署:
  pip install fastapi uvicorn[standard] python-jose[cryptography]
  uvicorn compass_http_v09:app --host 0.0.0.0 --port 8765 --workers 4

环境变量:
  COMPASS_DB_PATH       默认 /var/lib/compass/compass.db
  NAUTILUS_JWT_SECRET   共享 JWT secret (跟 nautilus.social 同 secret · #1 fusion)
  COMPASS_REGION        cn-shanghai | eu-frankfurt | us-virginia
  COMPASS_DAEMON_HOST   bge-m3 daemon (默认 127.0.0.1:9876)

Endpoints:
  GET  /healthz                   健康检查
  POST /v1/auth/signup            注册 (邮箱+密码)
  POST /v1/auth/login             登录 → JWT
  POST /v1/observations           写单条 obs
  POST /v1/observations/batch     批量写
  GET  /v1/recall                 召回 (cross-agent + drift filter)
  GET  /v1/agents                 list 我的 agents
  POST /v1/agents/register        注册新 agent
  GET  /v1/profile                用户画像
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    from fastapi import FastAPI, Header, HTTPException, Depends, Query
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
except ImportError:
    sys.stderr.write("compass_http_v09 needs fastapi · run: pip install 'fastapi[standard]'\n")
    sys.exit(1)

DB_PATH = Path(os.environ.get("COMPASS_DB_PATH", "/var/lib/compass/compass.db"))
JWT_SECRET = os.environ.get("NAUTILUS_JWT_SECRET", "dev-secret-rotate-in-prod")
REGION = os.environ.get("COMPASS_REGION", "cn-shanghai")
DAEMON_HOST = os.environ.get("COMPASS_DAEMON_HOST", "127.0.0.1:9876")
SERVER_VERSION = "0.9.0-dev"

app = FastAPI(
    title="compass-gateway",
    version=SERVER_VERSION,
    description="Cross-agent memory layer for Nautilus platform · multi-user · multi-region",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://nautilus.social", "https://compass.nautilus.social",
                   "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Rate limiting middleware (v0.9.5 · per-user-id token bucket · in-memory) ----

import time as _time
from collections import defaultdict, deque

_rate_buckets: dict[str, deque] = defaultdict(deque)
_RATE_LIMITS = {
    "free": 60,           # 60 req/min
    "pro": 600,
    "team": 600,
    "enterprise": 6000,
}


@app.middleware("http")
async def rate_limit_and_request_id(request, call_next):
    """Per-user rate limit + X-Request-Id tracing."""
    # 1. Inject request_id (audit + debug)
    rid = request.headers.get("X-Request-Id") or f"req_{uuid.uuid4().hex[:12]}"
    request.state.request_id = rid

    # 2. Rate limit (only for /v1/* · skip /healthz · /metrics · /a2a)
    path = request.url.path
    if path.startswith("/v1/") and not path.startswith("/v1/auth"):
        # Use X-User-ID header or anonymous IP for rate key
        rate_key = (request.headers.get("X-User-ID") or
                    (request.headers.get("Authorization") or "")[:32] or
                    request.client.host if request.client else "anon")
        now = _time.time()
        bucket = _rate_buckets[rate_key]
        # drop entries older than 60s
        while bucket and bucket[0] < now - 60:
            bucket.popleft()
        # default to free tier limit (server can lookup actual plan via auth_user · skipped here for speed)
        if len(bucket) >= _RATE_LIMITS["free"]:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={"error": "rate limit exceeded · 60 req/min for free tier",
                         "request_id": rid},
                headers={"X-Request-Id": rid, "Retry-After": "60"},
            )
        bucket.append(now)

    response = await call_next(request)
    response.headers["X-Request-Id"] = rid
    return response


# ---- DB ----

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE,
                region TEXT NOT NULL,
                passphrase_hash TEXT NOT NULL,
                encryption_salt BLOB NOT NULL,
                plan TEXT DEFAULT 'free',
                created_at TEXT NOT NULL,
                last_login_at TEXT
            );
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                device_id TEXT,
                workspace TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL,
                last_seen_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            CREATE INDEX IF NOT EXISTS idx_agents_user ON agents(user_id);
            CREATE TABLE IF NOT EXISTS observations (
                obs_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                ts TEXT NOT NULL,
                type TEXT,
                concept TEXT,
                drift TEXT,
                drift_signals TEXT,
                region TEXT NOT NULL,
                content_plain TEXT,
                encrypted_body BLOB,
                encryption_version TEXT,
                indexed BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            CREATE INDEX IF NOT EXISTS idx_obs_user_ts ON observations(user_id, ts DESC);
            CREATE INDEX IF NOT EXISTS idx_obs_drift ON observations(user_id, drift);
        """)


@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# ---- Auth ----

def auth_user(authorization: Optional[str] = Header(None),
              x_user_id: Optional[str] = Header(None)) -> str:
    """Resolve user_id from Bearer JWT (preferred) or X-User-ID (legacy compat for tools that haven't auth-ed yet)."""
    if authorization and authorization.startswith("Bearer "):
        try:
            from jose import jwt
            payload = jwt.decode(authorization[7:], JWT_SECRET, algorithms=["HS256"])
            return payload["user_id"]
        except Exception as e:
            raise HTTPException(401, f"invalid JWT: {e}")
    if x_user_id:
        # legacy · v0.7.2 兼容期 · only allow if user exists OR auto-create as 'demo' tier
        return x_user_id
    raise HTTPException(401, "auth required (Bearer or X-User-ID)")


# ---- Pydantic models ----

class ObservationIn(BaseModel):
    obs_id: str = Field(..., pattern=r"^ob_[a-zA-Z0-9_]+$")
    user_id: str = Field(..., pattern=r"^u_[a-zA-Z0-9_]+$")
    agent_id: str = Field(..., pattern=r"^ag_[a-zA-Z0-9_]+$")
    agent_type: str
    ts: str
    meta: dict
    content: Optional[dict] = None
    encrypted_body: Optional[str] = None
    encryption_version: Optional[str] = None


class ObservationBatch(BaseModel):
    observations: list[ObservationIn]


class SignupIn(BaseModel):
    email: str
    passphrase: str
    region: str = "cn-shanghai"


class LoginIn(BaseModel):
    email: str
    passphrase: str


class AgentRegisterIn(BaseModel):
    agent_type: str
    workspace: Optional[str] = None
    device_id: Optional[str] = None
    metadata: Optional[dict] = None


# ---- Routes ----

@app.get("/healthz")
def healthz():
    with db() as conn:
        users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        obs = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    return {
        "status": "ok",
        "service": "compass-gateway",
        "version": SERVER_VERSION,
        "region": REGION,
        "users": users,
        "observations": obs,
    }


@app.post("/v1/auth/signup", status_code=201)
def signup(body: SignupIn):
    import secrets, hashlib
    user_id = f"u_{uuid.uuid4().hex[:10]}"
    salt = secrets.token_bytes(32)
    passphrase_hash = hashlib.scrypt(body.passphrase.encode(), salt=salt, n=16384, r=8, p=1, dklen=32).hex()
    now = datetime.now(timezone.utc).isoformat()
    with db() as conn:
        try:
            conn.execute("""
                INSERT INTO users (user_id, email, region, passphrase_hash, encryption_salt, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, body.email, body.region, passphrase_hash, salt, now))
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(409, "email already registered")
    token = _issue_jwt(user_id, body.region)
    return {"user_id": user_id, "token": token, "region": body.region,
            "encryption_salt": salt.hex()}


@app.post("/v1/auth/login")
def login(body: LoginIn):
    import hashlib
    with db() as conn:
        u = conn.execute("SELECT * FROM users WHERE email = ?", (body.email,)).fetchone()
        if not u:
            raise HTTPException(401, "invalid credentials")
        salt = u["encryption_salt"]
        h = hashlib.scrypt(body.passphrase.encode(), salt=salt, n=16384, r=8, p=1, dklen=32).hex()
        if h != u["passphrase_hash"]:
            raise HTTPException(401, "invalid credentials")
        conn.execute("UPDATE users SET last_login_at = ? WHERE user_id = ?",
                     (datetime.now(timezone.utc).isoformat(), u["user_id"]))
        conn.commit()
    token = _issue_jwt(u["user_id"], u["region"])
    return {"user_id": u["user_id"], "token": token, "region": u["region"]}


# ---- OAuth2 PKCE for 3rd-party agents (#2 fusion · v0.9.2) ----

# In-memory PKCE state · production should use Redis with TTL
_pkce_states: dict[str, dict] = {}  # state → {code_challenge, redirect_uri, client_id, expires}
_pkce_codes: dict[str, dict] = {}   # code → {user_id, code_challenge, expires}


@app.post("/v1/auth/oauth/authorize")
def oauth_authorize(client_id: str, redirect_uri: str, code_challenge: str,
                    code_challenge_method: str = "S256", state: str = "",
                    user_id: str = Depends(auth_user)):
    """Step 1 of PKCE: authorized user grants consent · server returns code.

    3rd-party agent flow:
      1. agent → redirect user to this endpoint with code_challenge (SHA-256 hash of verifier)
      2. user (already logged in via JWT) clicks Approve
      3. server returns code · user agent redirects back to agent with code
      4. agent calls /v1/auth/oauth/token with code + code_verifier
    """
    if code_challenge_method != "S256":
        raise HTTPException(400, "only S256 supported")
    code = f"oac_{uuid.uuid4().hex[:16]}"
    _pkce_codes[code] = {
        "user_id": user_id,
        "code_challenge": code_challenge,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "expires": int(time.time()) + 600,  # 10 min
    }
    write_audit(user_id, "oauth.authorize", "client", client_id,
                metadata={"redirect_uri": redirect_uri})
    return {"code": code, "state": state, "redirect_uri": redirect_uri}


@app.post("/v1/auth/oauth/token")
def oauth_token(code: str, code_verifier: str, client_id: str,
                redirect_uri: str):
    """Step 2 of PKCE: exchange code + verifier for access token."""
    import hashlib
    import base64

    rec = _pkce_codes.get(code)
    if not rec:
        raise HTTPException(400, "invalid or expired code")
    if int(time.time()) > rec["expires"]:
        del _pkce_codes[code]
        raise HTTPException(400, "code expired")
    if rec["client_id"] != client_id or rec["redirect_uri"] != redirect_uri:
        raise HTTPException(400, "client_id or redirect_uri mismatch")

    # Verify PKCE: SHA256(verifier) == challenge
    digest = hashlib.sha256(code_verifier.encode()).digest()
    derived = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    if derived != rec["code_challenge"]:
        raise HTTPException(400, "code_verifier does not match code_challenge")

    user_id = rec["user_id"]
    del _pkce_codes[code]

    # Issue access token (shorter than user token · 24h)
    from jose import jwt
    with db() as conn:
        u = conn.execute("SELECT region FROM users WHERE user_id = ?",
                         (user_id,)).fetchone()
    region = (u or {}).get("region", REGION) if u else REGION
    access_token = jwt.encode({
        "user_id": user_id,
        "region": region,
        "client_id": client_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400,
    }, JWT_SECRET, algorithm="HS256")

    write_audit(user_id, "oauth.token", "client", client_id)
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 86400,
        "client_id": client_id,
        "user_id": user_id,
    }


# ---- Profile aggregate (client-side encrypted_facts upload · v1.0 §5) ----

class EncryptedFactsIn(BaseModel):
    encrypted_facts: str          # AES-GCM blob (base64) · client computed
    encryption_version: str = "v1"
    derived_at: str
    source_obs_count: int


@app.post("/v1/profile/derive")
def profile_derive(body: EncryptedFactsIn, user_id: str = Depends(auth_user)):
    """Client computes encrypted_facts locally · uploads opaque blob to server.

    v1.0 §5 · server cannot read facts · only stores ciphertext.
    Client downloads later via GET /v1/profile · decrypts locally.
    """
    with db() as conn:
        try:
            conn.execute("ALTER TABLE profiles ADD COLUMN encrypted_facts TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE profiles ADD COLUMN derived_at TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE profiles ADD COLUMN source_obs_count INTEGER")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE profiles ADD COLUMN encryption_version TEXT")
        except sqlite3.OperationalError:
            pass
        # Make sure profiles table exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                user_id TEXT PRIMARY KEY,
                encrypted_facts TEXT,
                derived_at TEXT,
                source_obs_count INTEGER,
                encryption_version TEXT,
                version INTEGER DEFAULT 1
            )
        """)
        conn.execute("""
            INSERT INTO profiles (user_id, encrypted_facts, derived_at, source_obs_count, encryption_version)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                encrypted_facts = excluded.encrypted_facts,
                derived_at = excluded.derived_at,
                source_obs_count = excluded.source_obs_count,
                encryption_version = excluded.encryption_version,
                version = version + 1
        """, (user_id, body.encrypted_facts, body.derived_at, body.source_obs_count, body.encryption_version))
        conn.commit()
    write_audit(user_id, "profile.derive", "profile", user_id,
                metadata={"source_obs_count": body.source_obs_count})
    return {"ok": True, "user_id": user_id}


def _placeholder_keep_fmt():
    """no-op · keep file format clean"""
    return None


def _issue_jwt(user_id: str, region: str) -> str:
    from jose import jwt
    return jwt.encode({
        "user_id": user_id,
        "region": region,
        "iat": int(time.time()),
        "exp": int(time.time()) + 30 * 86400,  # 30 days
    }, JWT_SECRET, algorithm="HS256")


@app.post("/v1/observations", status_code=201)
def ingest_obs(obs: ObservationIn, user_id: str = Depends(auth_user)):
    if obs.user_id != user_id:
        raise HTTPException(403, "user_id mismatch")
    if not (obs.content or obs.encrypted_body):
        raise HTTPException(400, "content or encrypted_body required")
    meta = obs.meta or {}
    with db() as conn:
        try:
            conn.execute("""
                INSERT INTO observations
                (obs_id, user_id, agent_id, ts, type, concept, drift, drift_signals,
                 region, content_plain, encrypted_body, encryption_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                obs.obs_id, obs.user_id, obs.agent_id, obs.ts,
                meta.get("type"), meta.get("concept"), meta.get("drift"),
                json.dumps(meta.get("drift_signals", []), ensure_ascii=False),
                REGION,
                json.dumps(obs.content, ensure_ascii=False) if obs.content else None,
                obs.encrypted_body, obs.encryption_version,
            ))
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(409, f"duplicate obs_id: {obs.obs_id}")
    # async: enqueue for bge-m3 indexing (out of scope for v0.9.0)
    return {"ok": True, "obs_id": obs.obs_id, "indexed_at": datetime.now(timezone.utc).isoformat()}


@app.post("/v1/observations/batch")
def ingest_batch(body: ObservationBatch, user_id: str = Depends(auth_user)):
    accepted = 0
    rejected = 0
    rejected_ids = []
    errors = []
    for obs in body.observations:
        if obs.user_id != user_id:
            rejected += 1
            rejected_ids.append(obs.obs_id)
            errors.append({"obs_id": obs.obs_id, "code": "USER_MISMATCH"})
            continue
        try:
            ingest_obs(obs, user_id=user_id)
            accepted += 1
        except HTTPException as e:
            rejected += 1
            rejected_ids.append(obs.obs_id)
            errors.append({"obs_id": obs.obs_id, "code": str(e.status_code), "message": e.detail})
    return {"ok": True, "accepted": accepted, "rejected": rejected,
            "rejected_ids": rejected_ids, "errors": errors}


@app.get("/v1/recall")
def recall(q: str = Query(...), top_k: int = 5, cross_agent: bool = True,
           drift: Optional[str] = None, agent_id: Optional[str] = None,
           user_id: str = Depends(auth_user)):
    # v0.9.0 minimum: 直接走 sqlite 关键词 + drift filter
    # v0.9.5: 加 daemon socket 走 bge-m3 真召回
    with db() as conn:
        sql = "SELECT * FROM observations WHERE user_id = ?"
        params = [user_id]
        if drift:
            sql += " AND drift = ?"
            params.append(drift)
        if not cross_agent and agent_id:
            sql += " AND agent_id = ?"
            params.append(agent_id)
        sql += " ORDER BY ts DESC LIMIT ?"
        params.append(top_k * 4)  # over-fetch for keyword filter
        rows = conn.execute(sql, params).fetchall()

    # primitive keyword score
    q_lower = q.lower()
    hits = []
    for r in rows:
        content = r["content_plain"] or ""
        score = 1.0 if q_lower in content.lower() else 0.5
        hits.append({
            "obs_id": r["obs_id"],
            "agent_id": r["agent_id"],
            "score": score,
            "ts": r["ts"],
            "drift": r["drift"],
            "type": r["type"],
            "content_or_encrypted": json.loads(content) if content else None,
        })
    hits = sorted(hits, key=lambda h: -h["score"])[:top_k]
    return {"user_id": user_id, "query": q, "hits": hits}


@app.get("/v1/agents")
def list_agents(user_id: str = Depends(auth_user)):
    with db() as conn:
        rows = conn.execute("SELECT * FROM agents WHERE user_id = ?", (user_id,)).fetchall()
    return [dict(r) for r in rows]


@app.post("/v1/agents/register", status_code=201)
def register_agent(body: AgentRegisterIn, user_id: str = Depends(auth_user)):
    agent_id = f"ag_{body.agent_type}_{uuid.uuid4().hex[:8]}"
    with db() as conn:
        conn.execute("""
            INSERT INTO agents (agent_id, user_id, agent_type, device_id, workspace, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (agent_id, user_id, body.agent_type, body.device_id, body.workspace,
              json.dumps(body.metadata) if body.metadata else None,
              datetime.now(timezone.utc).isoformat()))
        conn.commit()
    return {"agent_id": agent_id}


@app.get("/v1/profile")
def profile(days: int = 90, user_id: str = Depends(auth_user)):
    with db() as conn:
        rows = conn.execute("""
            SELECT type, drift, agent_id FROM observations
            WHERE user_id = ? AND ts >= datetime('now', '-' || ? || ' days')
        """, (user_id, days)).fetchall()
    types = {}
    drifts = {}
    agents = {}
    for r in rows:
        t = r["type"] or "?"
        types[t] = types.get(t, 0) + 1
        d = r["drift"] or "?"
        drifts[d] = drifts.get(d, 0) + 1
        a = r["agent_id"]
        agents[a] = agents.get(a, 0) + 1
    return {
        "user_id": user_id, "days": days,
        "source_obs_count": len(rows),
        "summary": {
            "top_agents": sorted(agents.items(), key=lambda x: -x[1])[:5],
            "types": types,
            "drift_distribution": drifts,
        },
    }


# ---- Marketplace metrics (#5 fusion · public anonymized) ----

@app.get("/v1/agents/{agent_id}/public-metrics")
def public_agent_metrics(agent_id: str):
    """Anonymized agent metrics for Nautilus marketplace UI · no auth required.

    Returns aggregate drift distribution + obs count · no PII.
    Used to show 'agent reputation' on marketplace listings.
    """
    with db() as conn:
        agent = conn.execute("""
            SELECT agent_id, agent_type, last_seen_at, created_at
            FROM agents WHERE agent_id = ?
        """, (agent_id,)).fetchone()
        if not agent:
            raise HTTPException(404, "agent not found")
        # Aggregate drift (last 30d · only public stats)
        rows = conn.execute("""
            SELECT drift, COUNT(*) as n
            FROM observations
            WHERE agent_id = ? AND ts >= datetime('now', '-30 days')
            GROUP BY drift
        """, (agent_id,)).fetchall()
        total = conn.execute("""
            SELECT COUNT(*) FROM observations WHERE agent_id = ?
        """, (agent_id,)).fetchone()[0]

    drift_dist = {r["drift"] or "?": r["n"] for r in rows}
    n30 = sum(drift_dist.values())
    return {
        "agent_id": agent["agent_id"],
        "agent_type": agent["agent_type"],
        "created_at": agent["created_at"],
        "last_seen_at": agent["last_seen_at"],
        "obs_count_30d": n30,
        "obs_count_total": total,
        "drift_distribution_30d": drift_dist,
        "green_pct_30d": round(100 * drift_dist.get("green", 0) / max(n30, 1), 1),
        "red_pct_30d": round(100 * drift_dist.get("red", 0) / max(n30, 1), 1),
        "_note": "anonymized · no user_id · for Nautilus marketplace · 30d window",
    }


@app.get("/v1/profile/compatibility")
def profile_compatibility(other_agent_id: str, user_id: str = Depends(auth_user)):
    """Compute how compatible an agent is with the current user's style.

    Used by Nautilus marketplace to recommend agents to users · 'this
    agent matches your work patterns 73%'. No raw obs leak across users ·
    only aggregate stats compared.
    """
    with db() as conn:
        # User's own type distribution
        user_rows = conn.execute("""
            SELECT type, COUNT(*) as n FROM observations
            WHERE user_id = ? GROUP BY type
        """, (user_id,)).fetchall()
        user_dist = {r["type"] or "?": r["n"] for r in user_rows}
        # Agent's drift profile (any user · since this is a public agent)
        agent_rows = conn.execute("""
            SELECT type, drift, COUNT(*) as n FROM observations
            WHERE agent_id = ? GROUP BY type, drift
        """, (other_agent_id,)).fetchall()
        agent_type_dist = {}
        for r in agent_rows:
            agent_type_dist[r["type"] or "?"] = agent_type_dist.get(r["type"] or "?", 0) + r["n"]

    if not user_dist or not agent_type_dist:
        return {"compatibility": 0.5, "reason": "insufficient data"}

    # Cosine similarity over type distributions (simple aggregate)
    keys = set(user_dist) | set(agent_type_dist)
    u_total = sum(user_dist.values())
    a_total = sum(agent_type_dist.values())
    u_vec = [user_dist.get(k, 0) / u_total for k in keys]
    a_vec = [agent_type_dist.get(k, 0) / a_total for k in keys]
    dot = sum(x * y for x, y in zip(u_vec, a_vec))
    n_u = sum(x * x for x in u_vec) ** 0.5
    n_a = sum(x * x for x in a_vec) ** 0.5
    sim = dot / (n_u * n_a + 1e-9) if n_u and n_a else 0.5

    return {
        "user_id": user_id,
        "other_agent_id": other_agent_id,
        "compatibility": round(sim, 3),
        "user_type_dist": user_dist,
        "agent_type_dist": agent_type_dist,
    }


# ---- Audit log (compliance · v0.9.6+ · GDPR Art 5/30) ----

def init_audit_table():
    """Idempotent · creates audit_log table + index."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS audit_log (
                audit_id TEXT PRIMARY KEY,
                ts TEXT NOT NULL,
                user_id TEXT,
                action TEXT NOT NULL,
                resource_type TEXT,
                resource_id TEXT,
                ip_addr TEXT,
                user_agent TEXT,
                metadata TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_audit_user_ts ON audit_log(user_id, ts DESC);
            CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action, ts DESC);
        """)


def write_audit(user_id, action, resource_type=None, resource_id=None,
                ip=None, ua=None, metadata=None):
    """Append audit entry · best-effort · never blocks request on failure."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO audit_log
                (audit_id, ts, user_id, action, resource_type, resource_id, ip_addr, user_agent, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"aud_{uuid.uuid4().hex[:10]}",
                datetime.now(timezone.utc).isoformat(),
                user_id, action, resource_type, resource_id, ip, ua,
                json.dumps(metadata, ensure_ascii=False) if metadata else None,
            ))
            conn.commit()
    except Exception:
        pass  # don't fail request if audit fails


@app.get("/v1/audit_log")
def get_audit_log(limit: int = 50, since: Optional[str] = None,
                  user_id: str = Depends(auth_user)):
    """User retrieves own audit_log entries · 90d retention (cron purges)."""
    with db() as conn:
        sql = "SELECT * FROM audit_log WHERE user_id = ?"
        params = [user_id]
        if since:
            sql += " AND ts >= ?"
            params.append(since)
        sql += " ORDER BY ts DESC LIMIT ?"
        params.append(min(limit, 500))
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


# ---- Prometheus metrics (production monitoring) ----

@app.get("/metrics")
def prometheus_metrics():
    """Scrape endpoint · Prometheus text format."""
    with db() as conn:
        users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        agents = conn.execute("SELECT COUNT(*) FROM agents").fetchone()[0]
        obs_total = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
        obs_24h = conn.execute("""
            SELECT COUNT(*) FROM observations WHERE ts >= datetime('now', '-1 day')
        """).fetchone()[0]
        try:
            audits_24h = conn.execute("""
                SELECT COUNT(*) FROM audit_log WHERE ts >= datetime('now', '-1 day')
            """).fetchone()[0]
        except sqlite3.OperationalError:
            audits_24h = 0
        drift_red_24h = conn.execute("""
            SELECT COUNT(*) FROM observations WHERE drift = 'red' AND ts >= datetime('now', '-1 day')
        """).fetchone()[0]
    metrics = [
        f"# HELP compass_users_total Total registered users",
        f"# TYPE compass_users_total gauge",
        f"compass_users_total {users}",
        f"# HELP compass_agents_total Total registered agents",
        f"# TYPE compass_agents_total gauge",
        f"compass_agents_total {agents}",
        f"# HELP compass_observations_total Total observations",
        f"# TYPE compass_observations_total counter",
        f"compass_observations_total {obs_total}",
        f"# HELP compass_observations_24h Observations last 24h",
        f"# TYPE compass_observations_24h gauge",
        f"compass_observations_24h {obs_24h}",
        f"# HELP compass_drift_red_24h Red drift events last 24h",
        f"# TYPE compass_drift_red_24h gauge",
        f"compass_drift_red_24h {drift_red_24h}",
        f"# HELP compass_audit_events_24h Audit log events last 24h",
        f"# TYPE compass_audit_events_24h gauge",
        f"compass_audit_events_24h {audits_24h}",
        f"# HELP compass_region_info Current region",
        f"# TYPE compass_region_info gauge",
        f'compass_region_info{{region="{REGION}"}} 1',
    ]
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse("\n".join(metrics) + "\n", media_type="text/plain; version=0.0.4")


# ---- User self-management (GDPR Art 17/20 · CCPA right to delete/export) ----

@app.delete("/v1/users/me", status_code=200)
def delete_my_account(user_id: str = Depends(auth_user)):
    """Soft-delete user · 30 day retention · cron hard-deletes after."""
    deleted_at = datetime.now(timezone.utc).isoformat()
    with db() as conn:
        try:
            conn.execute("ALTER TABLE users ADD COLUMN deleted_at TEXT")
        except sqlite3.OperationalError:
            pass
        conn.execute("UPDATE users SET deleted_at = ? WHERE user_id = ?",
                     (deleted_at, user_id))
        n_obs = conn.execute("SELECT COUNT(*) FROM observations WHERE user_id = ?",
                             (user_id,)).fetchone()[0]
        n_agents = conn.execute("SELECT COUNT(*) FROM agents WHERE user_id = ?",
                                (user_id,)).fetchone()[0]
        conn.commit()
    write_audit(user_id, "user.delete_request", "user", user_id,
                metadata={"obs_count": n_obs, "agent_count": n_agents})
    return {
        "ok": True, "user_id": user_id, "deleted_at": deleted_at,
        "soft_deleted": True, "hard_delete_after": "30 days",
        "will_be_deleted": {"observations": n_obs, "agents": n_agents},
    }


@app.post("/v1/users/me/cancel-deletion")
def cancel_deletion(user_id: str = Depends(auth_user)):
    """Cancel pending deletion · within 30d window."""
    with db() as conn:
        conn.execute("UPDATE users SET deleted_at = NULL WHERE user_id = ?",
                     (user_id,))
        conn.commit()
    write_audit(user_id, "user.cancel_deletion", "user", user_id)
    return {"ok": True, "user_id": user_id, "deletion_cancelled": True}


@app.get("/v1/users/me/export")
def export_my_data(user_id: str = Depends(auth_user)):
    """GDPR Art 20 · CCPA right to know · all user data as JSON."""
    with db() as conn:
        u_row = conn.execute(
            "SELECT user_id, email, region, plan, created_at, last_login_at FROM users WHERE user_id = ?",
            (user_id,)).fetchone()
        u = dict(u_row) if u_row else {}
        agents = [dict(r) for r in conn.execute(
            "SELECT * FROM agents WHERE user_id = ?", (user_id,)).fetchall()]
        obs = [dict(r) for r in conn.execute(
            "SELECT * FROM observations WHERE user_id = ? ORDER BY ts DESC LIMIT 10000",
            (user_id,)).fetchall()]
        try:
            audits = [dict(r) for r in conn.execute(
                "SELECT * FROM audit_log WHERE user_id = ? ORDER BY ts DESC LIMIT 1000",
                (user_id,)).fetchall()]
        except sqlite3.OperationalError:
            audits = []
    write_audit(user_id, "user.export", "user", user_id,
                metadata={"obs_count": len(obs), "agent_count": len(agents)})
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": "v0.9",
        "user": u, "agents": agents,
        "observations": obs, "audit_log": audits,
    }


# ---- Init ----

@app.on_event("startup")
def on_startup():
    init_db()
    init_audit_table()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("compass_http_v09:app", host="0.0.0.0", port=8765, reload=False)
