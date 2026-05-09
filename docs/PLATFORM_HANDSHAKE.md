# Platform handshake · OSS dialog ↔ SaaS dialog · 2026-05-08

> Coordination contract between the **OSS / paper / protocol dialog** (this repo)
> and the **Nautilus platform dialog** (compass.nautilus.social SaaS,
> billing, tenant management).
>
> Authoritative for: API contract, OAuth2 endpoints, user data schema,
> handoff points. Either dialog reads this; either may propose changes via PR.

---

## 1 · Boundary of responsibility

### OSS dialog owns

- `nautilus-compass` Python plugin + Node MCP wrapper (this repo)
- All `mcp_server.py` / `compass_http_v09.py` source code
- MCP / A2A protocol compliance (TLS, mTLS, RBAC, rate-limit, notifications, logging, resources)
- LongMemEval / EverMemBench benchmarks + papers (paper1 + paper2)
- BGE-m3 daemon (port 9876) + drift anchors + Merkle hash chain
- `docs/AGENT_ONBOARDING.md` + `scripts/install_to_agent.py` (developer-side onboarding)
- arxiv submissions, GitHub Releases, OSS metrics (stars / forks / installs)
- Anchor pack design (vertical anchors for legal / medical / finance — when sold as a deliverable, the schema is mine to design)
- `release-notes-*.md`, `CHANGELOG.md`, `LICENSE`, `LICENSE-ANCHORS`

### SaaS dialog owns

- `compass.nautilus.social` deployment, supervision, alerting
- Multi-tenant database, user accounts, OAuth2 server, refresh tokens
- Billing layer (Stripe / Alipay / Wechat Pay), tier gating, quotas
- User dashboard, signup flow, in-app onboarding
- Customer support, NPS surveys, churn analytics, SLO / SLA
- Marketing pages on nautilus.social, landing-page copy, growth
- Enterprise sales (SOW, MSAs, compliance attestations)
- Per-region infrastructure (cn-shanghai today; eu / us future)
- Monitoring dashboards, on-call rotation, incident response
- A2A registry commercialisation (`a2a-registry.nautilus.social`) when launched

### Shared (read-mostly · write requires the other dialog's ack)

- `/.well-known/agent.json` content (advertises capabilities + auth — both dialogs care)
- API endpoint contracts at `compass.nautilus.social/v1/*` (this doc, §3)
- User data schema (this doc, §4)
- Privacy / GDPR / PIPL notices (`paper/COMPLIANCE_NOTICE.md`)

---

## 2 · Handoff points

### A · OSS user → SaaS user (top-of-funnel conversion)

Trigger: user has installed the OSS plugin locally and hits a friction point
(needs cross-machine sync, multi-user collaboration, audit trail for
compliance, etc.) and clicks the README "Try hosted: compass.nautilus.social"
link.

| Step | Owner | Action |
|---|---|---|
| 1 | OSS  | README + `INSTALL.md` link to `https://compass.nautilus.social/signup` |
| 2 | SaaS | Signup page · email + verify · OAuth2 client created · token issued |
| 3 | SaaS | Dashboard onboarding tour (3 cards: ingest / recall / drift) |
| 4 | OSS  | Post-signup, plugin auto-detects token presence and offers "sync local memory to cloud?" prompt (script lives in OSS repo) |
| 5 | SaaS | Background sync workers, billing meter starts at first 100 obs |

### B · SaaS user reports a bug

| Bug class | Triage | Routing |
|---|---|---|
| SaaS UI / billing / OAuth | SaaS | SaaS dialog · use SaaS internal tracker |
| Memory layer logic / drift / MCP | OSS  | open GitHub issue at chunxiaoxx/nautilus-compass · OSS dialog assigns + fixes |
| Spans both (SaaS UI shows wrong drift score) | both | SaaS opens GitHub issue tagged `saas-coupled` · OSS investigates `compass_http_v09.py` |

### C · Enterprise inbound

Always routes to SaaS dialog first (contracts, NDAs, MSAs are SaaS scope).
SaaS may pull OSS dialog in for technical Q&A or anchor-pack-design SOW.

### D · Anchor pack consulting (custom verticals)

Order intake: SaaS dialog
Schema design + delivery: OSS dialog
Format: ~50-anchor JSON file under `anchors/<vertical>.json` plus a 2-page README
Pricing reference (initial · adjust per scope): legal $5k / medical $5k / finance $5k

### E · Press / paper inbound

OSS dialog handles paper questions (methodology, reproduction, citations).
SaaS dialog handles vendor-relations / partnership / co-marketing.

---

## 3 · API contract (compass.nautilus.social)

Endpoints SaaS dialog implements; OSS dialog consumes from plugin code.

### Public (no auth)

```
GET  /healthz                        → {"status","version","region","users","observations"}
GET  /.well-known/agent.json         → A2A discovery descriptor (per A2A spec v0.0.1)
```

### OAuth2

```
POST /v1/auth/signup                 → email/password sign-up · returns token + user_id
POST /v1/auth/signin                 → email/password sign-in
GET  /v1/oauth/authorize?client_id=  → start OAuth2 authorization-code flow
POST /v1/oauth/token                 → exchange code → access + refresh token
POST /v1/auth/refresh                → refresh access token
```

### Memory (Bearer auth required)

```
POST /v1/observations  body: {name, body, agent_id?, ts?, anchor?}    → 201 {obs_id}
POST /v1/recall        body: {query, top_k?, project?, since?}        → 200 {results: [{obs, score}]}
GET  /v1/profile?user_id=                                              → 200 {topics, agents, drift_trend}
GET  /v1/drift?agent_id=&since=                                        → 200 {events: [{ts, score, anchor}]}
POST /v1/feedback      body: {direction, reason, obs_id?}              → 201
```

### Errors (uniform across endpoints)

```
401 unauthenticated     missing or invalid token
403 forbidden           valid token, insufficient scope
404 not found           endpoint does not exist OR resource not found (per RFC nuance)
429 too many requests   rate-limited; X-RateLimit-Reset header carries seconds
500 server error        retry with exponential backoff
```

### Wire-format guarantees

- All bodies are JSON. UTF-8.
- Timestamps are ISO 8601 in UTC with `Z` suffix (`2026-05-08T16:35:56Z`).
- Cursor-paginated responses use `next_cursor` (not page numbers).
- Idempotency keys for POST /v1/observations: `Idempotency-Key: <uuidv4>` header optional.

### Stability promise

- Wire format frozen at `v1`; breaking changes go to `v2` (parallel deployment, 6-month overlap).
- Adding new optional fields is non-breaking and may ship in patch releases.

---

## 4 · User data schema (single source of truth)

Both dialogs reference this schema. SaaS dialog owns the `user`, `org`,
`subscription` tables. OSS dialog code reads/writes `observations`,
`anchors`, `drift_events` via the API.

```sql
-- SaaS-owned tables
user (id, email, hashed_pw, created_at, region, locale)
org  (id, name, owner_user_id, plan, created_at)
subscription (id, org_id, tier, started_at, ended_at, stripe_id)

-- OSS-format-defined tables (managed by SaaS deploy)
observations (
  id              text primary key,
  user_id         text references user(id),
  agent_id        text,
  name            text,
  body            text,
  anchor          text,
  drift_score     float,
  created_at      timestamptz,
  ts              timestamptz,
  embedding       vector(1024),
  encryption_version text,
  merkle_prev     text,
  merkle_self     text
)

anchors (
  id              text primary key,
  user_id         text,
  vertical        text,
  positive        bool,
  text            text,
  embedding       vector(1024)
)

drift_events (
  id              text primary key,
  user_id         text,
  agent_id        text,
  ts              timestamptz,
  score           float,
  anchor          text
)
```

### Encryption at rest

- `encryption_version=null` → plaintext (free / Pro tiers)
- `encryption_version=e2ee-v1` → client-side AES-256-GCM with per-user salt (Pro+ tier; SaaS server cannot decrypt body)

### Merkle chain

OSS plugin stores `merkle_prev` / `merkle_self` per write (`session_writer.py`).
SaaS replicates the chain on ingest. Clients can audit by walking the chain
back to a published anchor (paper2 §6 + §7 cover the protocol).

---

## 5 · Weekly status protocol

Each dialog writes a 5-line summary every Monday in this file under `## 6`:

```
### YYYY-MM-DD · OSS dialog
- Stars: NN (+M w/w)
- Open issues: K · merged PRs this week: J
- Releases: vX.Y.Z (or "no release this week")
- Anchor packs delivered: <list or "none">
- Blockers from SaaS dialog: <list or "none">

### YYYY-MM-DD · SaaS dialog
- DAU: NN (+M w/w) · MAU: NN
- Tier conversions free→Pro: K · churn: J
- MRR: $NNNN  ARR: $NNNN
- Incidents this week: <list or "clean">
- Blockers from OSS dialog: <list or "none">
```

Either dialog reads the other's section before starting work each week.
Blockers in either column stop their owner until cleared.

---

## 6 · Status log (append below)

(empty — first entries seed Monday 2026-05-12)

---

## 7 · Bidirectional flywheel · pending API contract

Status as of 2026-05-08 evening: SaaS dialog has identified **3 flywheel
breakpoints** between compass dialog (this side) and platform / V5 cycle
(SaaS side):

| BP  | Description                                              | Owner          | Status |
|-----|----------------------------------------------------------|----------------|--------|
| BP1 | compass dialog → platform task channel missing           | **OSS · this** | 🟢 stub shipped, see below |
| BP2 | V5 publishing claim cycle hook — agent claim rate low    | SaaS · #419    | 🟡 in progress |
| BP3 | task completion → memory ingest loop missing             | **both**       | 🟢 stub shipped, see below |

### BP1 — `submit_platform_task` (compass → platform)

OSS dialog ships a new MCP tool in `mcp_server.py` (commit 2026-05-08)
that any compass dialog can call to push a task into the platform task
queue. Default mode is **file-based**: writes a JSON spec to
`~/.claude/projects/_platform_queue/<task_id>.json`. The platform V5
cycle (SaaS side) polls that directory.

When SaaS endpoint is live, set env on the compass side:

```bash
export COMPASS_PLATFORM_QUEUE_URL=https://compass.nautilus.social/v1/tasks/queue
export COMPASS_PLATFORM_TOKEN=<bearer>
```

Then the same tool also POSTs to the HTTP endpoint (file remains as audit fallback).

**Wire format** (compass writes / platform reads):

```json
{
  "task_id": "tk_<unix_ms>",
  "name": "publish-dev-to-launch-post",
  "channels": ["dev.to", "x"],
  "anchor_pack_hint": "marketing/dev-tools",
  "priority": "normal",
  "payload": { "title": "...", "body_md": "...", "..." : "..." },
  "submitted_at": "2026-05-08T13:00:00Z",
  "submitted_by": "<COMPASS_DIALOG_ID env>",
  "compass_session_id": "<CLAUDE_SESSION_ID env>",
  "callback_url": "<COMPASS_CALLBACK_URL env, optional>",
  "status": "queued"
}
```

**SaaS side TODO** (platform dialog):
1. Add poller / webhook handler at `~/.claude/projects/_platform_queue/`
2. (Eventually) implement `POST /v1/tasks/queue` that accepts this same JSON
3. V5 cycle hook (#419) claims by `priority` desc + `anchor_pack_hint` → matching `platform_anchor_packs`
4. After claim, set `status` field in the file (`queued` → `claimed` → `running` → `done`)
5. Call `ingest_platform_task_result` on completion (BP3 below)

### BP3 — `ingest_platform_task_result` (platform → compass)

Closes the loop. Platform agent (or platform-side callback handler) calls
this MCP tool when a task completes. It writes:

1. JSON archive to `~/.claude/projects/_platform_results/<task_id>_result.json`
2. A `session_*.md` to the user's compass memory dir → searchable cross-session

**Wire format** (platform writes / compass ingests):

```json
{
  "task_id": "tk_<unix_ms>",
  "result_summary": "≤1000 char what-was-done",
  "channels_published": [
    {"channel": "dev.to",  "url": "https://dev.to/u/post-slug", "status": "success"},
    {"channel": "x",       "url": "https://x.com/u/status/123", "status": "success"}
  ],
  "drift": "green | yellow | red",
  "agent_id": "platform_agents.agent_id of who completed"
}
```

**Why this matters**: once a platform task result lands as a `session_*.md`,
the next time *any* compass dialog (this one, the platform dialog, or
a third agent on a different machine) calls `session_search` or
`recall`, the platform's output is treated as first-class memory. That
is the second half of the flywheel — platform output becomes input for
the next cross-session reasoning loop.

### Smoke verification (already done OSS-side)

```
$ python -m nautilus_compass.mcp_server  # initialize → tools/list → tools/call
TOOLS (10): [..., 'submit_platform_task', 'ingest_platform_task_result']
SUBMIT: task queued · id=tk_… · file-only (no COMPASS_PLATFORM_QUEUE_URL)
INGEST: result ingested · session=session_…_platform_tk_….md · drift=green
$ python session_search.py "platform task"
[12.2] (top hit, freshly ingested smoke result)
```

End-to-end submit → file → ingest → session_search round-trip verified.

### Open coordination questions for SaaS dialog

1. Should `_platform_queue` live in `~/.claude/projects/` (current — works for single-host dev), or move to a Redis / Postgres queue once SaaS is involved?
2. Does V5 cycle want the `payload` blob opaque, or do we add a typed schema per `anchor_pack_hint` so the cycle can validate before claiming?
3. For multi-tenant SaaS, the task spec will need a `tenant_id` field — OK to add now, or wait until SaaS multi-tenancy lands?
4. `callback_url` is OAuth2-bearer authenticated. Compass side needs to mint short-lived tokens. Spec out the token exchange — is `/v1/oauth/callback-tokens` the right endpoint name?

OSS dialog will not block on these — defaults are reasonable. Mark them
in §5 status log with proposed answers when SaaS dialog has cycles.

---

## 8 · Change log of this contract

- 2026-05-08 · OSS dialog seeds initial version after `gh repo edit --visibility public`. Boundaries, handoff points, API contract, schema all written from current code reality. SaaS dialog to ratify / amend before first weekly cycle.
- 2026-05-08 · OSS dialog adds §7 (flywheel · pending API contract) after reading SaaS dialog's BP1/BP2/BP3 analysis from `session_20260508-1901_营销文章质量评估与平台-代理飞轮断点分析`. Ships file-based stubs for BP1+BP3 in `mcp_server.py` so SaaS V5 cycle has a concrete wire to consume.
