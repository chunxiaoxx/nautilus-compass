# compass v0.9 · Server-side API spec

> 状态: design · 2026-05-05 · 实施在 v0.9.0 · 部署 compass.nautilus.social
> 目标: 让 SDK · MCP wrapper · A2A adapter 都有真 server 写入路径
> 当前: SDK 已写 · MCP server 已写 · A2A adapter 已写 · 但 server `/v1/observations` 是 404 (前端在 buffer)

## 现状 (v0.7.2 已部署)

```
GET  /healthz                       → 200 ok
GET  /                              → landing page (HTML)
POST /v1/recall                     → 召回 memory (X-Tenant-ID + X-Api-Key)
```

## v0.9 必须新加 (按 SDK 已设计的 contract)

### `POST /v1/observations`

```http
POST /v1/observations
Content-Type: application/json
Authorization: Bearer <jwt>           # v0.9.1+ · 现在用 X-User-ID + X-Api-Key
X-User-ID: u_xxx
X-Agent-ID: ag_xxx
X-Agent-Type: claude-code|openclaw|hermes|cursor|codex|zenmind|nautilus|caishen|custom

{
  "obs_id": "ob_xxx",                  // client 生成 · server 校验唯一
  "user_id": "u_xxx",                  // 必须跟 header 一致
  "agent_id": "ag_xxx",
  "agent_type": "claude-code",
  "ts": "2026-05-05T10:00:00Z",
  "meta": {
    "type": "discovery",
    "concept": "trade-off",
    "drift": "green",
    "drift_signals": []
  },
  "content": {                          // plan=free 时明文
    "name": "...",
    "description": "...",
    "body": "..."
  }
  // OR
  "encrypted_body": "<base64 AES-GCM>", // plan=pro+ 时加密
  "encryption_version": "v1"
}

Response 201:
{
  "ok": true,
  "obs_id": "ob_xxx",
  "indexed_at": "2026-05-05T10:00:01Z"
}

Response 400/401/409 errors as standard.
```

### `POST /v1/observations/batch`

```http
POST /v1/observations/batch
{
  "observations": [{...}, {...}]   // 最多 100 条
}

Response 200:
{
  "ok": true,
  "accepted": 95,
  "rejected": 5,
  "rejected_ids": ["ob_xxx", ...],
  "errors": [{"obs_id": "ob_xxx", "code": "DUPLICATE", "message": "..."}]
}
```

### `GET /v1/recall` (扩展 v0.7.2)

```http
GET /v1/recall?q=<query>&top_k=5&cross_agent=true&drift=red&agent_id=ag_xxx
Authorization: Bearer <jwt>

Response 200:
{
  "tenant": "...",                  // 兼容老 client
  "user_id": "u_xxx",               // 新加
  "query": "...",
  "hits": [
    {
      "obs_id": "ob_xxx",
      "agent_id": "ag_xxx",
      "agent_type": "claude-code",
      "score": 0.87,
      "ts": "...",
      "age_seconds": 3600,
      "age_str": "1h",
      "meta": {...},
      "content_or_encrypted": {...}
    }
  ],
  "fresh_extra": [...],             // 兼容
  "profile_hint": "..."             // v1.0 · 推荐
}
```

### `GET /v1/agents`

```http
GET /v1/agents
Authorization: Bearer <jwt>

Response 200:
[
  {"agent_id": "ag_xxx", "agent_type": "claude-code", "workspace": "...", "last_seen_at": "...", "obs_count_30d": 42}
]
```

### `POST /v1/agents/register`

```http
POST /v1/agents/register
{
  "agent_type": "openclaw",
  "workspace": "/home/ubuntu/openclaw",
  "device_id": "d_xxx",
  "metadata": {...}
}

Response 201:
{"agent_id": "ag_xxx"}
```

### `GET /v1/profile`

```http
GET /v1/profile?days=90
Authorization: Bearer <jwt>

Response 200:
{
  "user_id": "u_xxx",
  "days": 90,
  "encrypted_facts": "<base64>",        // plan=pro+ · client 解密
  "derived_at": "...",
  "source_obs_count": 142,
  "summary": {                          // 明文 metadata 聚合 · 不含 PII
    "top_agent_types": [{"type": "claude-code", "count": 80}, ...],
    "top_projects": [...],
    "drift_distribution": {"green": 95, "yellow": 38, "red": 9}
  }
}
```

### `POST /v1/auth/signup` (v0.9.1)

```http
POST /v1/auth/signup
{
  "email": "x@y.com",
  "passphrase": "...",
  "region": "cn-shanghai"
}

Response 201:
{
  "user_id": "u_xxx",
  "token": "<jwt 30d>",
  "encryption_salt": "<base64>"     // client side derive E2EE master key
}
```

### `POST /v1/auth/login`

```http
POST /v1/auth/login
{"email": "x@y.com", "passphrase": "..."}

Response 200:
{"user_id": "u_xxx", "token": "..."}
```

## 实施 (Python · FastAPI 推荐)

```python
# compass_http_v09.py · 替代 compass_http.py

from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
import sqlite3
from contextlib import contextmanager

app = FastAPI(title="compass-gateway", version="0.9.0-dev")

DB_PATH = Path("/var/lib/compass/compass.db")

class ObservationIn(BaseModel):
    obs_id: str
    user_id: str
    agent_id: str
    agent_type: str
    ts: str
    meta: dict
    content: dict | None = None
    encrypted_body: str | None = None
    encryption_version: str | None = None

@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def auth_user(authorization: str | None = Header(None),
              x_user_id: str | None = Header(None),
              x_api_key: str | None = Header(None)) -> str:
    """v0.9 兼容 v0.7.2 · 优先 JWT · fallback X-User-ID + X-Api-Key (legacy tenant)."""
    if authorization and authorization.startswith("Bearer "):
        # decode JWT · return user_id
        return decode_jwt(authorization[7:])
    if x_user_id:
        # legacy compat (no auth · v0.7.2 demo tenant)
        return x_user_id
    raise HTTPException(401, "auth required")

@app.post("/v1/observations", status_code=201)
def ingest(obs: ObservationIn, user_id: str = Depends(auth_user)):
    if obs.user_id != user_id:
        raise HTTPException(403, "user_id mismatch")
    if not (obs.content or obs.encrypted_body):
        raise HTTPException(400, "content or encrypted_body required")
    with db() as conn:
        try:
            conn.execute("""
                INSERT INTO observations (obs_id, user_id, agent_id, agent_type, ts,
                  type, concept, drift, drift_signals, content, encrypted_body, encryption_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [obs.obs_id, obs.user_id, obs.agent_id, obs.agent_type, obs.ts,
                  obs.meta.get("type"), obs.meta.get("concept"), obs.meta.get("drift"),
                  json.dumps(obs.meta.get("drift_signals", []), ensure_ascii=False),
                  json.dumps(obs.content, ensure_ascii=False) if obs.content else None,
                  obs.encrypted_body, obs.encryption_version])
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise HTTPException(409, f"duplicate obs_id: {obs.obs_id}")
    # async: enqueue for bge-m3 indexing
    enqueue_index(obs.obs_id)
    return {"ok": True, "obs_id": obs.obs_id, "indexed_at": now_iso()}
```

## SQLite schema (v0.9 单 region)

见 `paper/V09_USER_SCHEMA.md` §3.

## v1.0 sharding (region)

```
nginx route by JWT.region:
  cn-shanghai  → backend-cn-1.compass.nautilus.social
  eu-frankfurt → backend-eu-1.compass.nautilus.social
  us-virginia  → backend-us-1.compass.nautilus.social

per region: independent sqlite + bge-m3 daemon · 不跨境同步
```

## 上线 checklist (v0.9.0)

```
✓ schema migration script (memory/*.md → observations table · 一次性)
✓ /v1/observations + /v1/observations/batch
✓ /v1/recall extended (cross_agent · agent_id filter · drift filter)
✓ /v1/agents + /v1/agents/register
✓ /v1/profile (基础版 · v1.0 加 encrypted_facts)
✓ /healthz extended (return version · sqlite count · daemon status)
✓ rate limit by user_id (60/min free · 600/min pro)
✓ HTTPS only (cert renew via certbot)
✓ Sentry / Loki 日志 (PII 脱敏)
✓ Prometheus metrics (request count · p95 latency · error rate)
✓ smoke test 自动跑 (selftest endpoint)
```

## 当前 (v0.7.2 → v0.9.0) 平滑迁移

```
Phase 1 · 双轨 · 老 endpoint 保留
  v0.7.2: X-Tenant-ID + X-Api-Key + tenant=demo|caishen|...
  v0.9.0: 新加 /v1/observations + Bearer JWT · 老 client 不破

Phase 2 · 推 client 升级 · 1 个月观察期

Phase 3 · 弃用老 endpoint · 强制 JWT
```
