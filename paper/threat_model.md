# compass · Threat Model

> Status: 2026-05-05 · v0.9.0-dev · for security review · pre-v1.0 GA
> Methodology: STRIDE per Microsoft TM template · adapted for AI memory systems

## Trust boundaries

```
┌─────────────────────────────────────────────────────────────┐
│ User device (trusted by user · trusted by compass mostly)   │
│  · IDE / Claude Desktop / browser                           │
│  · MCP server (compass-mcp · stdio · same machine)          │
│  · SDK (compass_client.py)                                  │
│  · master_key (derived from passphrase · client only)       │
└─────────────────────────────────────────────────────────────┘
                           │ HTTPS (TLS 1.3)
                           │
┌─────────────────────────────────────────────────────────────┐
│ Edge (nginx · region-aware routing)                         │
│  · TLS termination                                          │
│  · JWT region claim parsing                                 │
│  · rate limiting · DDoS                                     │
└─────────────────────────────────────────────────────────────┘
                           │ Internal HTTP (region VPC)
                           │
┌─────────────────────────────────────────────────────────────┐
│ FastAPI server (compass_http_v09 · per-region)              │
│  · auth · sqlite reader · obs router                        │
│  · CANNOT decrypt encrypted_body (Pro+)                     │
└─────────────────────────────────────────────────────────────┘
                           │ Local socket
                           │
┌─────────────────────────────────────────────────────────────┐
│ bge-m3 daemon (per-region · GPU)                            │
│  · embedding · drift_check · reranker                       │
│  · meta-only indexing for Pro+ encrypted obs                │
└─────────────────────────────────────────────────────────────┘
```

## STRIDE analysis

### S - Spoofing identity

| Threat | Mitigation | Status |
|---|---|---|
| Attacker impersonates legitimate user | scrypt password hash + JWT signing · 30d expiry | ✅ |
| Attacker forges JWT | HS256 with random NAUTILUS_JWT_SECRET (32+ bytes) · rotate quarterly | ✅ |
| Attacker reuses old session | JWT exp claim · server checks expiration | ✅ |
| Replay attack on auth endpoint | (planned) nonce on /v1/auth/login · v1.0 | 🟡 |
| Spoofed Nautilus-issued JWT | shared secret with Nautilus auth service · in-process verify | ✅ |
| Cross-tenant spoofing (legacy X-Tenant-ID) | tenant config validates api_key per-request | ✅ |

### T - Tampering with data

| Threat | Mitigation | Status |
|---|---|---|
| In-transit modification | TLS 1.3 · HSTS · cert pinning (planned v1.0) | ✅ / 🟡 |
| Encrypted obs tampering | AES-GCM AEAD · InvalidTag on tamper · proven in tests | ✅ |
| Obs ID collision attack | obs_id is client-generated · server stores as PRIMARY KEY · UNIQUE constraint | ✅ |
| SQL injection | parameterized queries everywhere (FastAPI · sqlite3) | ✅ |
| Anchor poisoning (community PRs) | code review + AUC regression test in CI · CC0 license | ✅ |

### R - Repudiation

| Threat | Mitigation | Status |
|---|---|---|
| User claims they didn't make a write | audit_log · 90d retention · IP · UA · request_id | ✅ |
| Server claims it didn't process | per-request request_id in response · in audit | ✅ |
| Drift signal disputed | drift_check returns top_neg_hits + score · auditable | ✅ |
| Stake penalty disputed | drift_event payload includes evidence + signals + scores | ✅ |

### I - Information disclosure

| Threat | Mitigation | Status |
|---|---|---|
| Server reads user content | E2EE Pro+ · server stores encrypted_body · cannot decrypt | ✅ |
| Cross-user data leak via SQL | row-level filter in every query (`WHERE user_id = ?`) | ✅ |
| Cross-region data leak | nginx routes by JWT region claim · isolated upstream pools | ✅ |
| Leaked encryption_salt | salt is per-user · only useful with passphrase · low impact alone | ✅ |
| TLS downgrade | TLS 1.2/1.3 only · weak ciphers excluded | ✅ |
| Cert MITM | Let's Encrypt · cert pinning client-side (planned v1.0) | 🟡 |
| Audit log read by other users | row-level filter on user_id | ✅ |
| Marketplace metrics expose user | only aggregate dist · no user_id · no ts (only 30d window) | ✅ |
| Profile compatibility leaks | only user × agent type aggregate · no obs content | ✅ |
| Backup file exposure | optional GPG encrypt before offsite copy | 🟡 |

### D - Denial of service

| Threat | Mitigation | Status |
|---|---|---|
| Single user exhausts API | per-user rate limit (60/min free · 600/min pro) | ✅ |
| Volumetric DDoS | nginx rate limit + Cloudflare front (planned v1.0) | 🟡 |
| Slow loris on FastAPI | uvicorn timeout · keepalive limit | ✅ |
| LLM API exhaustion (writer) | session_writer cost cap (¥0.50/user/day default) | 🟡 |
| Daemon GPU exhaustion | single eval lock · queue if busy | ✅ |
| Stake event flood | per-agent cap · max 10 events/min then drop | ✅ |
| sqlite WAL bloat | auto-vacuum · backup rotation | ✅ |

### E - Elevation of privilege

| Threat | Mitigation | Status |
|---|---|---|
| User escalates to admin | no admin role in v0.9 · enterprise plan only | ✅ |
| Org member reads other org data | memberships table FK enforced · query joins always check | ✅ |
| Anchor expert injects backdoor | PR review · no auto-merge · CI runs drift AUC regression | ✅ |
| LLM judge bias | cross-judge replication ($10 · planned 1 week) | 🟡 |
| Compromised npm package | @nautilus org · 2FA on npmjs · package-lock.json | 🟡 |
| Compromised Docker image | image signing · SLSA L2 (planned v1.0) | 🔴 |
| Supply chain (PyPI) | dependabot weekly · ignore major bumps for torch/transformers | ✅ |

## Adversary models

### Casual user
- Curious about other users' data
- Mitigation: row-level isolation · no broadcast endpoints

### Malicious user
- Wants to spoof identity / DoS / exfil
- Mitigation: JWT · rate limit · audit log · all standard

### Compromised SDK / extension
- Signs requests with stolen master_key locally
- Mitigation: client-side audit (we can't fully prevent) · v1.0 hardware token (planned)

### Hostile platform (e.g., compromised Anthropic / OpenAI route)
- Sees plain prompt content (we send obs through them)
- Mitigation: don't route content through 3rd party · session_writer goes direct to Volc Ark · MCP server is local stdio

### Server compromise
- Attacker reads sqlite directly
- Mitigation: encrypted_body Pro+ · meta in plaintext (acceptable · no PII)
- Backup encrypted with GPG (optional)

### Government data request
- Country forces server data handover
- Mitigation: data sharded by region · local compliance only · encrypted_body cannot be decrypted server-side
- Public response: post warrant canary if forced

## Open issues / known gaps

```
🔴 Cert pinning client-side (planned v1.0)
🔴 SLSA L2 image signing (planned v1.0)
🔴 Cloudflare front for volumetric DDoS (planned v0.9.5)
🔴 LLM API cost cap per user (planned v0.9.5)
🔴 Hardware token for high-stakes encryption (planned post-v1.0)

🟡 Cross-judge replication on full 500 ($10 cost · in-progress now)
🟡 Penetration test by external party (planned pre-v1.0 GA)
🟡 Formal cryptographic audit of compass_crypto (peer review · planned pre-v1.0 GA)
```

## Compliance assertion

Compass v0.9.0-dev meets the following:
- ✅ Confidentiality: E2EE Pro+ default (v1.0) · TLS in-transit
- ✅ Integrity: AES-GCM AEAD · audit log · SQL parameterized queries
- ✅ Availability: per-user rate limit · region failover (v1.0)
- ✅ Authentication: scrypt + JWT · OAuth2 PKCE planned (v0.9.2)
- ✅ Authorization: row-level user_id check · org membership FK
- ✅ Auditability: 90-day audit log · request_id tracing
- ✅ Compliance: GDPR/CCPA/PIPL notices (template in COMPLIANCE_NOTICE.md)

## Review

This document MUST be reviewed before v1.0 GA by:
- [ ] Internal security reviewer (chunxiaoxx)
- [ ] External pen tester (TBD · pre-GA)
- [ ] Cryptographic peer (compass_crypto module · libsodium expert)
- [ ] Legal counsel (PIPL · GDPR · CCPA · all 3 jurisdictions)

Last updated: 2026-05-05 · review cycle quarterly
