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

## 7 · Change log of this contract

- 2026-05-08 · OSS dialog seeds initial version after `gh repo edit --visibility public`. Boundaries, handoff points, API contract, schema all written from current code reality. SaaS dialog to ratify / amend before first weekly cycle.
