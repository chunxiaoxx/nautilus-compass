# SaaS operations · compass.nautilus.social · template (2026-05-08)

> Mirror of `docs/PLATFORM_HANDSHAKE.md` from the **SaaS dialog** side.
> Boundary owners and handoff points are defined in `PLATFORM_HANDSHAKE.md`
> §1-2; this file fills in the SaaS-side operational details that are out
> of scope for the OSS dialog. Either dialog reads both.
>
> **Status: template** — populated with current production state where
> known; placeholders (`[TODO: ...]`) where the SaaS dialog needs to write
> in concrete values, owners, and procedures.

---

## 1 · Production topology

| Component | Status | Detail |
|---|---|---|
| Region | cn-shanghai | Single region as of 2026-05-08 · eu/us deferred |
| Compute | 1 × Tencent Cloud VM (43.160.239.61) | 4 GB / 4 vCPU baseline; uvicorn 4 workers |
| API service | `compass.service` (systemd) | `python3 uvicorn compass_http_v09:app --host 0.0.0.0 --port 8770 --workers 4` |
| Reverse proxy | nginx 1.18 | `/v9/*` → `localhost:8770/*` (strip prefix) |
| TLS | Let's Encrypt | auto-renew via certbot |
| Database | [TODO: confirm — sqlite? postgres?] | observations · anchors · drift_events tables per `PLATFORM_HANDSHAKE.md` §4 |
| Embedder | local BGE-m3 daemon | port 9876 · same VM |
| Auth | OAuth2 + email/password | tokens issued by service · stored in [TODO: token store] |
| Versioning | v1.0.0 stable since 2026-05-08 | promoted from 0.9.0-dev with `compass_http_v09.py.bak.pre-v1.0` rollback artefact |

### Known operational quirks

- `/v1/version` returns 404 (endpoint not implemented). `/healthz` already
  exposes the version field. Either implement `/v1/version` or remove
  references in OSS docs (low priority).
- `/.well-known/agent.json` is a hand-coded JSON literal in
  `compass_http_v09.py` (line ~1057). Updating capabilities requires a
  code edit + service restart. Could move to a YAML config in v1.1.

---

## 2 · Tier definitions (proposed · please ratify)

| Tier | Price | Quotas | Target |
|---|---|---|---|
| Free | $0 | 1k obs / mo, 100 recall / mo, 1 agent_id | Funnel · solo dev evaluation |
| Pro | $19 / mo | 50k obs / mo, 5k recall / mo, multi-agent, drift API | Individual paying user |
| Team | $99 / mo | 500k obs / mo, 50k recall / mo, A2A 5 peers, Merkle audit | Small team (2-10) |
| Enterprise | Contact sales | Unlimited, on-prem option, SOC 2 attestation, private anchor pack | Regulated industry |

Quota enforcement is via per-token rate limiter (already shipped in OSS code).

[TODO: lock prices · seed Stripe/Alipay product IDs · write tier-gating config]

---

## 3 · Billing flow

[TODO: payment provider — Stripe vs Alipay vs Wechat Pay vs all three]

Lifecycle:
1. User signs up → free tier auto-assigned · token issued
2. Quota threshold (e.g. 80%) → in-app upsell prompt + email
3. Upgrade clicked → payment flow → webhook updates `subscription.tier` row
4. Renewal: monthly auto-charge · failure → grace 7 days → downgrade to free
5. Cancellation: continues until period end · then downgrade

Webhook idempotency: use Stripe event ID as primary key in `processed_events` table.

[TODO: write specific webhook handler · test against Stripe sandbox]

---

## 4 · Customer support

| Channel | Owner | SLO |
|---|---|---|
| `chunxiaoxx@gmail.com` (general) | OSS dialog (escalate to SaaS for billing) | 24 h response |
| `support@nautilus.social` [TODO: enable] | SaaS dialog | 8 h response (Pro+) / 24 h (Free) |
| GitHub issues at chunxiaoxx/nautilus-compass | OSS dialog | 48 h triage |
| In-app chat (Intercom or similar) | SaaS dialog | 4 h business hours |

[TODO: write canned responses for top 10 expected questions]

---

## 5 · Monitoring & SLO

### SLI targets (proposed)

- API availability (`/healthz` 200): **99.5%** monthly
- API latency p95: **500 ms** for `/v1/recall`, **150 ms` for `/v1/observations` POST
- Drift score consistency: ±0.02 vs golden anchor set (canary check daily)

### Current monitoring

- [TODO: dashboards · Grafana? Datadog? Tencent Cloud Monitor?]
- [TODO: alerting · who gets paged on `/healthz` 500 / 5xx rate spike]
- [TODO: log aggregation · journalctl on VM only as of 2026-05-08]

### On-call

- [TODO: rotation? solo? after-hours coverage?]
- [TODO: incident runbook for: BGE-m3 daemon down, certbot renewal failed, DB lock, OAuth token leak]

---

## 6 · Compliance roadmap

| Standard | Status | Owner | Target |
|---|---|---|---|
| GDPR (EU) | partial | SaaS | Article 33 breach notif workflow [TODO] |
| PIPL (China) | partial | SaaS | data-export-region API per `paper/COMPLIANCE_NOTICE.md` |
| CCPA (California) | partial | SaaS | `ccpa@` mailbox forwarding to chunxiaoxx@gmail.com |
| SOC 2 Type I | not started | SaaS | 12-month attestation cycle · Year 1 ARR threshold [TODO: when to start] |
| HIPAA | not in scope | — | Only if medical anchor pack customers ask |
| ISO 27001 | not in scope | — | Same as above |

`paper/COMPLIANCE_NOTICE.md` already drafts notice text (GDPR/PIPL/CCPA);
SaaS dialog ratifies and enables the email aliases.

---

## 7 · Marketing / growth

### Funnel (current best understanding)

```
GitHub stars / arxiv reads / HN mention
        │
        ▼
README "Try hosted" CTA  →  /signup  →  free tier auto-assigned
        │
        ▼
Quota / sync / audit friction  →  Pro upgrade prompt
        │
        ▼
Pro paid user
        │
        ▼
Team trial (refer colleagues)  →  Team paid
        │
        ▼
Enterprise inbound (compliance + custom anchor pack)
```

### Content plan (SaaS dialog drafts · OSS dialog reviews technical claims)

- [TODO: blog post 1 · "How drift detection caught X real failures in production"]
- [TODO: blog post 2 · "Self-host vs hosted: when does each make sense?"]
- [TODO: blog post 3 · "Anchor schema design for legal vertical"]
- [TODO: case study 1 · first paying enterprise customer]
- [TODO: comparison page · vs Mem0 / Letta / Zep]

### Channels

- HN / Reddit / Twitter — OSS dialog seeds (paper drops)
- Vendor partnerships — SaaS dialog (Anthropic / OpenAI / Cursor / Cline integration listings)
- Conference talks — both dialogs collaborate (paper2 first author = Chunxiao Wang)

---

## 8 · Status log (mirror of PLATFORM_HANDSHAKE.md §6)

(empty — first entry seeds Mon 2026-05-12 by SaaS dialog)

---

## 9 · Change log of this template

- 2026-05-08 · OSS dialog seeds template after `gh repo edit --visibility public`
  to give SaaS dialog a starting structure. SaaS dialog ratifies, fills in
  TODOs, and owns this file going forward.
