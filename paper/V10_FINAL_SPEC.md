# compass v1.0 · Final Specification

> Status: aggregated spec · 2026-05-05
> Target GA: 2027-05 (12 months from now)
> Single source of truth for v1.0 expectations · supersedes individual phase docs at GA

This document is the **canonical specification** for Compass v1.0.
It aggregates and harmonizes:

- [V09_USER_SCHEMA.md](V09_USER_SCHEMA.md) → multi-user/region/E2EE schema
- [V09_API_SPEC.md](V09_API_SPEC.md) → server endpoint contract
- [V10_ROADMAP.md](V10_ROADMAP.md) → 17-phase plan
- [PLATFORM_FUSION.md](PLATFORM_FUSION.md) → 8 Nautilus integration points
- [STAKE_DRIFT_COUPLING.md](STAKE_DRIFT_COUPLING.md) → economic protocol
- [REGION_SHARDING.md](REGION_SHARDING.md) → multi-region deployment
- [LICENSE_DECISION.md](LICENSE_DECISION.md) → license evolution

If any of those documents disagree with this one (post-2026-05-05),
the others are out of date.

---

## 1. v1.0 product surface

### 1.1 What it is

Compass v1.0 is a **cross-agent · cross-device · cross-region memory layer**
for AI agents, deployed as:

- **Open-source plugin** (MIT or Apache 2.0 · TBD per LICENSE_DECISION) ·
  installable via `pip` / `uv tool` / `npx`
- **Hosted SaaS** at `compass.nautilus.social` (3 regions · cn-shanghai ·
  eu-frankfurt · us-virginia) · default tier free
- **Standalone Docker compose** for enterprise self-hosting
- **MCP server** (7+ tools · stdio JSON-RPC)
- **A2A adapter** (4+ capabilities · HTTP)
- **npm wrapper** (`@nautilus/compass-mcp`)
- **VS Code / Cursor extension** (5 commands)

### 1.2 What it solves

| Problem | v1.0 solution |
|---|---|
| AI forgets long-session rules | drift detection · AUC=0.92 · hook-time |
| Memory fragmented across tools | cross-agent federation · same user_id |
| Manual memory writing | session_writer · auto-distill ¥0.05/session |
| Memory accuracy poor | LongMemEval-S 56.6% · paper SOTA tier |
| Vendor lock-in | provider-neutral · MCP/A2A standards |
| Privacy concerns | E2EE default · region sharding · self-host option |
| Cost prohibitive | local bge-m3 · ¥10/run · 1/15 of commercial APIs |

---

## 2. Identity & Auth (#1 #2 fusion)

### 2.1 User identity model

```sql
users (
  user_id TEXT PRIMARY KEY,        -- u_<10 hex>
  email TEXT UNIQUE,
  region TEXT NOT NULL,            -- cn-shanghai | eu-frankfurt | us-virginia
  passphrase_hash TEXT NOT NULL,   -- scrypt(passphrase, salt) hex
  encryption_salt BLOB NOT NULL,   -- 32 bytes · for E2EE master key derive
  plan TEXT DEFAULT 'free',        -- free | pro | team | enterprise
  created_at TEXT NOT NULL,
  last_login_at TEXT
);
```

### 2.2 SSO with Nautilus platform (#1 fusion)

```
nautilus.social JWT.user_id → compass.users.user_id (1:1)
nautilus.social JWT.region  → compass.users.region (1:1)

Shared JWT secret: NAUTILUS_JWT_SECRET (env)
Token TTL: 30 days (refresh on use)
```

### 2.3 OAuth2 PKCE for 3rd-party agents (#2 fusion)

```
3rd-party agent (Cursor / OpenClaw fork / Hermes / etc.)
  → redirect user to nautilus.social/oauth/authorize?client_id=compass
  → user 同意
  → callback compass with code
  → exchange → access_token + refresh_token
```

---

## 3. Schema (post-v0.9 final)

### 3.1 agents

```sql
agents (
  agent_id TEXT PRIMARY KEY,       -- ag_<type>_<8 hex>
  user_id TEXT NOT NULL FK,
  agent_type TEXT NOT NULL,        -- claude-code | openclaw | hermes | cursor | codex | zenmind | nautilus | caishen | custom
  device_id TEXT,                  -- d_<10 hex>
  workspace TEXT,                  -- e.g. "C--Users-chunx"
  metadata JSON,
  created_at TEXT NOT NULL,
  last_seen_at TEXT
);
```

### 3.2 observations (E2EE-aware)

```sql
observations (
  obs_id TEXT PRIMARY KEY,         -- ob_<10 hex>
  user_id TEXT NOT NULL FK,
  agent_id TEXT NOT NULL FK,
  ts TEXT NOT NULL,                -- ISO 8601

  -- 明文 metadata (server 索引用)
  type TEXT,                       -- bugfix | feature | refactor | discovery | decision | change
  concept TEXT,                    -- gotcha | pattern | trade-off | how-it-works | why-it-exists | problem-solution | what-changed
  drift TEXT,                      -- green | yellow | red
  drift_signals JSON,              -- ["..."]
  region TEXT NOT NULL,

  -- 内容 (free 明文 · pro+ 加密)
  content_plain JSON,              -- {name, description, body} · plan=free
  encrypted_body BLOB,             -- AES-GCM(content) · plan=pro+
  encryption_version TEXT,         -- "v1"

  -- 索引状态
  indexed BOOLEAN DEFAULT 0,       -- bge-m3 是否已 embed
  embedding BLOB                   -- 1024 dim float16 · 索引完后存
);
```

### 3.3 organizations + memberships (Team/Enterprise)

```sql
organizations (
  org_id TEXT PRIMARY KEY,         -- o_<10 hex>
  name TEXT NOT NULL,
  plan TEXT NOT NULL,              -- team | enterprise
  shared_key BLOB,                 -- group key · admin holds
  created_at TEXT NOT NULL
);

memberships (
  user_id TEXT FK,
  org_id TEXT FK,
  role TEXT NOT NULL,              -- admin | member
  joined_at TEXT NOT NULL,
  PRIMARY KEY (user_id, org_id)
);
```

### 3.4 profiles (E2EE aggregate)

```sql
profiles (
  user_id TEXT PRIMARY KEY FK,
  encrypted_facts BLOB,            -- AES-GCM([...]) · client computes · server stores
  derived_at TEXT,
  source_obs_count INTEGER,
  version INTEGER DEFAULT 1
);
```

---

## 4. API surface (v1.0 stable)

### 4.1 Auth

```
POST /v1/auth/signup         {email, passphrase, region} → {user_id, token, encryption_salt}
POST /v1/auth/login          {email, passphrase} → {user_id, token}
POST /v1/auth/refresh        Bearer expiring → {token}
POST /v1/auth/logout         Bearer → {}
DELETE /v1/users/me          Bearer → {} (right-to-be-forgotten · 30d soft-delete)
```

### 4.2 Observations

```
POST /v1/observations              Bearer · single obs
POST /v1/observations/batch        Bearer · ≤100
GET  /v1/observations              Bearer · pagination · since/agent_id/drift filters
DELETE /v1/observations/<obs_id>   Bearer · only owner
```

### 4.3 Recall + Profile + Agents

```
GET  /v1/recall?q=<>&top_k=5&cross_agent=true&drift=red&agent_id=ag_x
GET  /v1/profile?days=90
POST /v1/profile/derive            client-side encrypted_facts upload
GET  /v1/agents
POST /v1/agents/register
```

### 4.4 Org / Team

```
POST /v1/orgs                      {name, plan} → {org_id}
POST /v1/orgs/<o>/members          {user_id, role}
GET  /v1/orgs/<o>/recall?q=<>
DELETE /v1/orgs/<o>/members/<u>
```

### 4.5 A2A (separate /a2a/* namespace)

```
GET  /a2a/capabilities             A2A discovery
POST /a2a/messages                 A2A protocol envelope (STORE_OBS / RETRIEVE_MEMORY / QUERY_PROFILE / QUERY_DRIFT_HISTORY)
POST /a2a/register                 Register self in nautilus a2a-registry
```

### 4.6 Stake (#4 fusion · economic protocol)

```
GET  /stake/events?since=<ts>        Pull pending drift events (consumed by Nautilus stake module)
POST /stake/ack                     Mark drift event as processed (with stake action result)
```

---

## 5. Encryption (E2EE · #1.0 default)

### 5.1 Client-side key derivation

```
master_key = scrypt(passphrase, encryption_salt, n=16384, r=8, p=1, dklen=32)
per_obs_key = HKDF-SHA256(master_key, obs_id_bytes, salt="compass.v1")
```

### 5.2 Encryption flow

```
Client side (writing obs):
  content_json = {name, description, body}
  ciphertext = AES-GCM(per_obs_key, content_json) → encrypted_body
  POST /v1/observations  {meta, encrypted_body}

Server side:
  Stores encrypted_body without decrypting.
  Indexes only meta fields (type, concept, drift, drift_signals · timestamp)
  bge-m3 embedding is computed client-side (when E2EE on)

Client side (reading obs):
  GET /v1/recall returns hits with encrypted_body
  Client decrypts using local master_key
  Result presented to LLM context
```

### 5.3 Key recovery

```
User loses passphrase → data lost (no server-side recovery)
Pro+ tier: optional recovery seed phrase (24 words · BIP39) on signup
Team: org admin holds group_key for shared rooms
```

---

## 6. Multi-region (#1.0 · #合规)

```
cn-shanghai  → Tencent Cloud 上海 · PIPL · 数据不出境
eu-frankfurt → AWS Frankfurt · GDPR · DPA template
us-virginia  → AWS US East · CCPA

JWT carries region claim · nginx routes by region.
Cross-region not synchronized by default · explicit user opt-in via /v1/auth/export-region.
```

详见 [REGION_SHARDING.md](REGION_SHARDING.md).

---

## 7. Stake × Drift coupling (#4 fusion)

```
Drift events (compass → stake module · A2A protocol):

drift=red    → 1% locked stake penalty · burn USDC
drift=green  → 0.1% locked stake bonus
drift=yellow → no action

Anti-cheat:
  · red drift 必须有 ≥1 drift_signals · 否则 downgrade yellow
  · 平台层 drift 抽查 (1% obs · server 重算 · 差距 > 0.3 flag)
  · 单 agent green 100% > 30d → 抽查
  · 单 agent red 80% > 7d → auto deactivate
  · per-user agent 上限 (free 5 · pro 20)
```

详见 [STAKE_DRIFT_COUPLING.md](STAKE_DRIFT_COUPLING.md).

---

## 8. RAID-2 (#7 fusion · v1.0 default for org plan)

```
RAID-2 = Read-Audit-In-Drift · 写入前 reviewer agent 把关

free / pro: RAID-1 (writer 直写)
team / enterprise: RAID-2 default
  · writer 提交 obs
  · reviewer (compass anchor + LLM judge) 评估
    · drift=green → 通过 · 入库
    · drift=red → 退回 writer · 必须改 + 报 drift_signals
  · 类似 git pre-commit hook
```

---

## 9. Marketplace 信任层 (#5 fusion)

```
Nautilus marketplace lists agents:
  · agent_id · description · price
  + drift_history (last 30d · % green/yellow/red)
  + profile_compatibility (该 agent 跟当前 user 历史风格的匹配度)

用户买 agent 前看 compass-derived metrics
= compass 是 marketplace 信任层

Endpoint:
  GET /v1/agents/<id>/public-metrics  (anonymized · for marketplace UI)
```

---

## 10. Adapter ecosystem (multi-protocol)

| Protocol | Status | Notes |
|---|---|---|
| Claude Code hook | ✅ v0.7+ | UserPromptSubmit · Stop · PostToolUse |
| MCP server | ✅ v0.9 | 7 tools · stdio JSON-RPC · Claude Desktop · Cline · Cursor compatible |
| A2A adapter | ✅ v0.9 | 4 capabilities · HTTP service · `a2a-registry.nautilus.social` |
| Direct SDK | ✅ v0.9 | `compass_client.py` · `attach_memory.py` · for fork-and-modify |
| npm wrapper | ✅ v0.9 | `@nautilus/compass-mcp` · `npx -y` ready |
| VS Code/Cursor extension | 🟡 v0.9.3 | `cursor-extension/` · marketplace pending |
| Browser extension | 🟡 v0.9.5+ | for ChatGPT · Codex (DOM scraping) |

---

## 11. CLI ecosystem

```
nautilus-compass            Main CLI (recall · drift · feedback)
compass-mcp                 MCP server · stdio JSON-RPC
compass-a2a                 A2A HTTP service (default :8765)
compass-drift-history       Cross-project drift timeline · ASCII
compass-session-search      Cross-project keyword search
compass-session-writer      Manual session distill trigger
```

---

## 12. Performance & cost targets

| Metric | v0.8 actual | v1.0 target |
|---|---|---|
| LongMemEval-S accuracy | 56.6% (Zep SOTA tier) | ≥56.6% (no regression) |
| Drift detection AUC | 0.92 | ≥0.90 (cross-domain) |
| Drift hook latency p95 | 47 ms | ≤50 ms |
| Reproduction cost (500 q) | $3.50 USD | ≤$5 USD |
| session_writer cost | ¥0.05/session | ≤¥0.10 |
| 24/7 hook deployment cost | ¥350/mo | ≤¥500/mo |
| Concurrent users on single region | unmeasured | ≥10K MAU |

---

## 13. Compliance posture

```
PIPL (China):
  ✅ data not exported by default
  ✅ user-authorized export uses cross-border data transfer 申报
  ✅ right to delete (hard delete + 30d soft retention)
  ✅ data minimization (no PII beyond email)
  ✅ Tencent / Aliyun 上海 (备案 ICP)

GDPR (EU):
  ✅ Privacy by design (E2EE default at v1.0)
  ✅ Right to erasure (DELETE /v1/users/me)
  ✅ Data portability (export endpoint · v1.0)
  ✅ DPA template for enterprise
  ✅ EU servers (Frankfurt) · default region

CCPA (California):
  ✅ Opt-out of data sale (we don't sell)
  ✅ Right to know what's collected (GET /v1/profile)
  ✅ Right to delete

Audit:
  · /v1/audit_log endpoint (Pro+)
  · all hook · all ingest · all recall · all auth event tracked
  · 90 days retention · client can export
```

---

## 14. Backward compatibility

```
v0.7.x → v0.9.x: dual-track period · 1 month
  · v0.7.2 endpoint preserves · all clients work
  · v0.9 endpoint added with new schema
  · client opt-in to v0.9 by sending Bearer JWT (legacy X-Tenant-ID still accepted)

v0.9.x → v1.0: announced 30 days before deprecation
  · X-Tenant-ID header removed (Bearer required)
  · CHANGELOG migration script provided

Schema migration (v0.9 → v1.0):
  · automatic on startup · no manual step
  · old observations preserved · new fields nullable
```

---

## 15. Release checklist (v1.0 GA · 2027-05)

```
Code:
  □ All tests passing (≥90% coverage)
  □ LongMemEval-S regression suite ≥56.6%
  □ Drift AUC regression suite ≥0.90 cross-domain
  □ A2A protocol roundtrip pass
  □ MCP smoke pass on all 4 clients (Claude Desktop · Cline · Cursor · Codex)

Infra:
  □ 3 regions deployed + healthy (cn · eu · us)
  □ E2EE encryption · client lib audited
  □ Backup tested (recovery RTO ≤ 4 hours)
  □ Region sharding nginx config in production
  □ Monitoring (Prometheus + Sentry) wired

Documentation:
  □ Paper 2 published (arXiv minimum · venue TBD)
  □ User guide complete (RU/EN/ZH)
  □ API reference (auto-generated from OpenAPI)
  □ Self-host guide (docker-compose ready)

Compliance:
  □ PIPL legal review
  □ GDPR DPA template signed off by counsel
  □ CCPA notice published
  □ Audit log retention working

Business:
  □ Pricing page live (free · pro · team · enterprise · with placeholders)
  □ Pro tier billing infrastructure (Stripe · Paddle · etc.)
  □ Open source release (Apache 2.0 or MIT · per LICENSE_DECISION.md)
  □ npm + pip + uv tool · all package indexes updated
  □ Release blog post + paper announcement
```

---

## 16. Stretch goals (post-v1.0)

```
v1.1: Cross-region encrypted backup (user-managed · IPFS / Arweave option)
v1.2: Federated learning across users (without raw data exchange)
v1.3: Voice / image obs (multi-modal memory)
v1.4: Local LLM mode (Ollama · LM Studio · for self-host paranoid users)
v2.0: On-chain anchor governance (DAO votes on platform anchors)
```

---

## 17. References (within this repo)

- [paper/V09_USER_SCHEMA.md](V09_USER_SCHEMA.md)
- [paper/V09_API_SPEC.md](V09_API_SPEC.md)
- [paper/V10_ROADMAP.md](V10_ROADMAP.md)
- [paper/PLATFORM_FUSION.md](PLATFORM_FUSION.md)
- [paper/STAKE_DRIFT_COUPLING.md](STAKE_DRIFT_COUPLING.md)
- [paper/REGION_SHARDING.md](REGION_SHARDING.md)
- [paper/RESULTS_v0.8.md](RESULTS_v0.8.md)
- [paper/LICENSE_DECISION.md](LICENSE_DECISION.md)
- [paper/RELEASE_READINESS.md](RELEASE_READINESS.md)
- [paper/sections/paper2_*.tex](sections/) (8 sections + 1 appendix)
