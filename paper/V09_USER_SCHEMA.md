# compass v0.9 · user-as-first-class schema redesign

> 状态: design · 2026-05-05 · 替代 v0.8 的 tenant-as-product 模型
> 决策依据: 用户提出 "跨 agent 融合 · 真正懂用户 · 这是最宝贵资产"
> 商业模式: 平台化 SaaS (Free / Pro / Team / Enterprise) · 暂不变现 · 走融资

## 1. 现状 (v0.8)

```
tenant = 产品维度
  default · caishen · zenxin · demo

每个 tenant:
  api_key · anchors_profile · rate_limit · default_project
```

**痛点**: 1 user 跨多产品时无法融合 · "懂用户"做不到。

## 2. 目标 (v0.9 - v1.0)

```
user = 一等公民 (跨多 agent · 跨多 device · 跨多产品)
agent = 来源标识 (claude-code / openclaw / hermes / cursor / codex / 自家产品)
organization = 团队层 (1 org 多 user · Team/Enterprise plan)
```

## 3. Schema (sqlite for v0.9 · postgres for v1.0)

### 3.1 users

```sql
CREATE TABLE users (
    user_id           TEXT PRIMARY KEY,    -- u_<10 hex>
    email             TEXT UNIQUE,
    region            TEXT NOT NULL,       -- cn-shanghai | eu-frankfurt | us-virginia
    passphrase_hash   TEXT NOT NULL,       -- scrypt
    encryption_salt   BLOB NOT NULL,       -- 32 bytes · for E2EE key derive
    plan              TEXT DEFAULT 'free', -- free | pro | team | enterprise
    created_at        DATETIME NOT NULL,
    last_login_at     DATETIME
);
```

### 3.2 agents

```sql
CREATE TABLE agents (
    agent_id          TEXT PRIMARY KEY,    -- ag_<10 hex>
    user_id           TEXT NOT NULL REFERENCES users(user_id),
    agent_type        TEXT NOT NULL,       -- claude-code | openclaw | hermes | ...
    device_id         TEXT,                -- d_<10 hex> · 多 device 时填
    workspace         TEXT,                -- e.g. "C--Users-chunx" or "/home/ubuntu/openclaw"
    metadata          JSON,
    created_at        DATETIME NOT NULL,
    last_seen_at      DATETIME
);

CREATE INDEX idx_agents_user ON agents(user_id);
```

### 3.3 observations

```sql
CREATE TABLE observations (
    obs_id            TEXT PRIMARY KEY,    -- ob_<10 hex>
    user_id           TEXT NOT NULL REFERENCES users(user_id),
    agent_id          TEXT NOT NULL REFERENCES agents(agent_id),
    ts                DATETIME NOT NULL,

    -- 明文 meta · server 索引用
    type              TEXT,                -- bugfix | feature | refactor | discovery | decision | change
    concept           TEXT,                -- gotcha | pattern | trade-off | how-it-works | why-it-exists | problem-solution | what-changed
    drift             TEXT,                -- green | yellow | red
    drift_signals     JSON,                -- ["..."]
    region            TEXT NOT NULL,

    -- 内容 · E2EE 时加密
    content_plain     JSON,                -- {name, description, body} · plan=free 时
    encrypted_body    BLOB,                -- AES-GCM(content) · plan=pro+ 时

    -- vector for cross-agent recall (bge-m3 维度 = 1024)
    embedding         BLOB                 -- np.float16[1024] flatten
);

CREATE INDEX idx_obs_user_ts ON observations(user_id, ts DESC);
CREATE INDEX idx_obs_drift ON observations(user_id, drift) WHERE drift IS NOT NULL;
CREATE INDEX idx_obs_type ON observations(user_id, type);
```

### 3.4 profiles (聚合画像 · 客户端写入 · server 存)

```sql
CREATE TABLE profiles (
    user_id           TEXT PRIMARY KEY REFERENCES users(user_id),
    encrypted_facts   BLOB,                -- AES-GCM(["他偏好简洁回复", ...])
    derived_at        DATETIME,
    source_obs_count  INTEGER,
    version           INTEGER DEFAULT 1
);
```

### 3.5 organizations + memberships (Team/Ent)

```sql
CREATE TABLE organizations (
    org_id            TEXT PRIMARY KEY,    -- o_<10 hex>
    name              TEXT NOT NULL,
    plan              TEXT NOT NULL,       -- team | enterprise
    shared_key        BLOB,                -- group key · admin holds
    created_at        DATETIME NOT NULL
);

CREATE TABLE memberships (
    user_id           TEXT NOT NULL REFERENCES users(user_id),
    org_id            TEXT NOT NULL REFERENCES organizations(org_id),
    role              TEXT NOT NULL,       -- admin | member
    joined_at         DATETIME NOT NULL,
    PRIMARY KEY (user_id, org_id)
);
```

## 4. API redesign

### 4.1 Auth

```
POST /v1/auth/signup
  body: { email, passphrase, region }
  → { user_id, token (JWT 30d) }

POST /v1/auth/login
  body: { email, passphrase }
  → { user_id, token }

POST /v1/auth/refresh
  Authorization: Bearer <expiring_token>
  → { token }
```

### 4.2 Observations

```
POST /v1/observations
  Authorization: Bearer <jwt>
  body: { obs_id, agent_id, agent_type, ts, meta, content | encrypted_body }
  → { ok: true, obs_id }

POST /v1/observations/batch
  body: { observations: [...] }
  → { ok, count, obs_ids }

GET /v1/observations?since=<ts>&agent_id=<>&type=<>&drift=<>
  → { observations: [...] }   -- 用户取自己历史 · pagination
```

### 4.3 Recall (跨 agent · 默认)

```
GET /v1/recall?q=<query>&top_k=5&cross_agent=true&drift=<>
  → {
      hits: [
        { obs_id, agent_id, agent_type, score, ts, meta, content_or_encrypted }
      ],
      profile_hint: "..."   -- v1.0 · 推荐你历史上对类似问题的偏好
    }

GET /v1/recall?agent_id=ag_<>&q=...
  → 限单 agent
```

### 4.4 Profile (v1.0)

```
GET /v1/profile
  → { encrypted_facts, derived_at, source_obs_count }

POST /v1/profile/derive
  body: { encrypted_facts }   -- client-side 聚合后上传
  → { ok }
```

### 4.5 Agents

```
GET /v1/agents
  → [ { agent_id, agent_type, workspace, last_seen_at } ]

POST /v1/agents/register
  body: { agent_type, workspace, device_id?, metadata? }
  → { agent_id }
```

### 4.6 Org / Team

```
POST /v1/orgs
  body: { name, plan }
  → { org_id }

POST /v1/orgs/<org_id>/members
  body: { user_id, role }

GET /v1/orgs/<org_id>/recall?q=...
  → 在团队共享空间召回
```

## 5. 迁移 (v0.8 → v0.9)

```
Phase 1 · v0.8.x (1 周) - 兼容期
  · tenants.json 增加 user_id 字段 (默认 u_system)
  · compass_http.py 既接受 X-Tenant-ID (旧) · 也接受 X-User-ID (新)
  · 新 obs 写到 sqlite (新表) · 老 recall 走文件 (旧逻辑)

Phase 2 · v0.9.0 (3 周)
  · 上线 auth (邮箱 + scrypt + JWT)
  · sqlite migrate 所有现有 memory/*.md 进 observations 表
  · UserPromptSubmit hook 升级 · 写 obs 而非文件
  · /v1/observations endpoint 上线

Phase 3 · v0.9.x (1 月)
  · OpenClaw / Hermes SDK 接入 (本会话已写 client + 示例)
  · cross_agent recall 上线 (跨多 agent 索引)

Phase 4 · v1.0 (3 月)
  · region sharding (cn / eu / us 三集群)
  · E2EE 默认 (Pro 起)
  · profile 自动浮现
  · Team / Ent plan
```

## 6. E2EE 协议 (v1.0)

```
Client side:
  master_key = scrypt(passphrase, encryption_salt)  -- 30s once on login
  per_obs_key = HKDF(master_key, obs_id)
  encrypted_body = AES-GCM(per_obs_key, content_json)

Server side:
  存 encrypted_body · 不解密 · 只用明文 meta 索引
  recall: 返 encrypted_body · client 用 master_key 解
  profile: client 定期 download all · 本地聚合 · 上传 encrypted_facts

Cross-region 同步:
  默认不跨 region · 用户授权时 · client 重新加密成目标 region key
```

## 7. 当前会话产出

```
✅ sdk/compass_client.py        · client lib · offline buffer
✅ sdk/README.md                · 接入文档
✅ examples/openclaw_integration.py
✅ examples/hermes_integration.py
✅ paper/V09_USER_SCHEMA.md     · 本文 (设计)
🟡 server-side /v1/observations endpoint · 待 v0.9 实施
🟡 sqlite schema migration · 待 v0.9 实施
```

## 9. 协议适配层 · MCP + A2A (Nautilus 平台力推方向)

> **修正 (2026-05-05)**: OpenClaw / Hermes 是开源产品 · 不是自家. 接入路径优先级随之调整: 协议优先 (MCP / A2A) > 直接 SDK.

### 9.1 MCP (Model Context Protocol · Anthropic)

compass 已有 `mcp_server.py` · 升级为 multi-agent ingest:

```
任何 MCP client (Claude Desktop / Cline / Cursor / 自定义 agent)
   配置 mcpServers.compass = "compass-mcp"
   →  调 tool: compass.ingest_obs(...)
   →  调 tool: compass.recall(...)
```

实施 (1 周):
- `mcp_server.py` 加 user_id 概念 (从 X-API-Key 派生 · v0.9 改 OAuth)
- 加新 tool: `compass.ingest_obs` · `compass.recall_cross_agent` · `compass.profile`
- npm publish: `@nautilus/compass-mcp` 包 · 任何人 npx 起

收益: **不写 SDK · 只配 MCP · 任何 client 立刻接入**

### 9.2 A2A (Agent-to-Agent · Google)

compass 作为 A2A 网络的"memory agent":

```
A2A agent network:
  agent_A (e.g. OpenClaw 战略 agent)
    ↓ A2A message: STORE { name, body, drift, ... }
  compass-memory-agent (本服务)
    ↓ index + 召回
  agent_B (e.g. Hermes loop)
    ← A2A message: RETRIEVE { query }  → returns hits
```

实施 (2 周):
- 新 endpoint: `POST /a2a/messages` · 接收 A2A protocol payload
- 实现 A2A capabilities discovery (`/a2a/capabilities` 返 STORE/RETRIEVE/PROFILE)
- 注册到 Nautilus A2A 网络 (`a2a-registry.nautilus.social`)

收益: **任何 A2A 兼容 agent 不改代码就能接 compass**

### 9.3 Adapter 优先级 (修正版)

| 接入方式 | 协议层 | 用户改动 | 适用 agent |
|---|---|---|---|
| **MCP server** ⭐ | 标准协议 | 配 1 行 mcpServers | Claude Desktop / Cline / Cursor / OpenClaw 改造后 / Hermes / 自家产品 |
| **A2A adapter** ⭐ | 标准协议 | 0 (注册到 registry) | Google A2A 兼容生态 · Nautilus 平台 |
| **Direct SDK** | 私有 | 写 3 行 Python | OpenClaw / Hermes (open source · fork 加 SDK call) · 自定义 |
| **Hook** | Claude 私有 | 0 (plugin 自动) | Claude Code (已通) |

### 9.4 Nautilus 平台一体化

```
Nautilus 力推方向:
  · MCP 作为工具调用层 (compass 是 memory tool)
  · A2A 作为 agent 互通层 (compass 是 memory agent)

→ compass 升级: 既是 MCP server (供 agent 调) · 也是 A2A agent (跨 agent 互通)
→ Nautilus 平台: 把 compass 默认装进 agent runtime · 所有 agent 自动有共享 memory
```

## 10. 决策记录

| 问题 | 选项 | 决策 |
|---|---|---|
| 接入优先级 | Claude Code / Codex / Cursor / OpenClaw / Hermes | **协议优先**: MCP server 第 1 · A2A 第 2 · 然后 Cursor extension · Codex 最后. OpenClaw / Hermes 通过 MCP 接入 (它们是开源 · 不是自家 · 可 fork 加 MCP 调用) |
| 存储方式 | 纯本地 / 纯云 / 混合 | 混合分层 · Free 本地 · Pro 云 E2EE · Team 选择性共享 · Ent 自托管 |
| 合规 | 单 region / 多 region | 多 region (cn-shanghai · eu-frankfurt · us-virginia) · 默认不跨境 |
| 盈利节奏 | 立即 / 靠后 | 靠后 · 走融资 · Pro 灰锁让用户感知未来 |
| 时间投入 | 3m / 6m / 12m | 12m 走完 v1.0 · 但 M1 出 demo (OpenClaw + Hermes 接入) |
| tenant model | 单 tenant / multi-user | multi-user (重构 tenant model · user 一等公民) |
