# Security Policy

## Reporting a vulnerability

Please report security issues privately. Do NOT open a public issue.

- **Email**: security@nautilus.social (PGP key on `nautilus.social/security`)
- **Backup**: file an issue with the label `security:embargo` (we'll respond and move discussion privately)

We aim to respond within 72 hours.

## Supported versions

| Version | Supported | Notes |
|---|---|---|
| 0.9.0-dev | ✅ | active development |
| 0.7.x | ✅ | bug fixes only · EOL 2026-06-01 |
| < 0.7.0 | ❌ | upgrade required |

## Threat model

compass handles sensitive memory data. Our threat model assumes:

### Trusted

- The local machine running the plugin (we don't defend against local
  malware that could read `.cache/` directly)
- The bge-m3 daemon (local Unix socket)
- Volc Ark / Anthropic / similar LLM providers (in their security domain)

### Untrusted

- Network in transit (compass.nautilus.social uses HTTPS)
- Other tenants on shared infrastructure
- Disk persistence on cloud (we plan E2EE in v1.0)
- Backup chain (we don't yet ship encrypted backups)

### Mitigations

| Threat | Mitigation | Status |
|---|---|---|
| TLS interception | HTTPS-only enforce + HSTS | ✅ v0.7.2 |
| Cross-tenant data leak | per-user_id sqlite row filter + JWT verification | ✅ v0.9 (planned) |
| API key theft | scrypt password hash + 30d JWT rotation | ✅ v0.9 (planned) |
| Plaintext disk | E2EE client-side encryption | 🟡 v1.0 |
| Replay attack | nonce on auth endpoints | 🟡 v1.0 |
| Rate exhaustion | per-user_id rate limit (60/min free) | ✅ v0.7.2 |
| Anchor injection | manual review · CC0 license | ✅ |
| MCP server compromise | runs locally · stdio sandbox · no network | ✅ |
| Nautilus JWT secret leak | rotation procedure documented | ✅ v0.9 (planned) |

## Disclosure timeline

We follow a **90-day disclosure** policy:

1. Day 0: report received
2. Day 0-7: acknowledged, severity triaged
3. Day 7-30: fix developed
4. Day 30-90: rolled out · users notified
5. Day 90+: public disclosure if not fixed (or earlier if exploited)

## Known issues / non-goals

### Not security issues (please don't report as such)

- Drift detection false positives: this is a model accuracy issue, not security
- Memory recall false positives: same
- Plugin not running: see INSTALL.md troubleshooting

### Known limitations

- Pre-v1.0 builds store memory in plaintext at rest (encrypted disk
  recommended for sensitive deployments)
- bge-m3 daemon listens on `127.0.0.1:9876` by default · not exposed
  to network · but a local user can read `.cache/`
- No certificate pinning yet (relies on system trust store)
- No content security policy on landing page

## Hall of fame

(Reporters who responsibly disclosed vulnerabilities will be listed
here · with permission.)

- *None yet*

## Bug bounty

We don't run a paid bounty (yet). When the Nautilus platform launches
its public mainnet, we expect to fund one tied to stake economy. Until
then: thanks + GitHub credit.
