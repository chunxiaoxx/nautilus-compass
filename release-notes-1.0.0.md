## [1.0.0] · 2026-05-08 — "stable · promote rc2 verbatim"

`1.0.0-rc2` (2026-05-07) ships unchanged as `1.0.0`. No code or test
changes since rc2; this entry exists to mark the stable cut and bump
version strings (`pyproject.toml`, `package.json`, `.claude-plugin/plugin.json`,
`mcp_server.SERVER_VERSION`) from `1.0.0-rc2` to `1.0.0`.

The full feature surface — MCP A2A protocol with TLS/mTLS, per-token RBAC,
per-token rate limiting, auto-reconnect client with `-32029` backoff,
`resources/*` for session-log streaming, `notifications/{progress,cancelled,message}`,
`logging/setLevel`, third-party stdio shim, plus the slash-command plugin
surface — is unchanged from rc2. See `release-notes-1.0.0-rc2.md` for
the full per-feature breakdown.

### Eval headlines (locked)

- LongMemEval-S n=500: **56.6%** (v0.8 · 2026-05-04 lock)
- EverMemBench-Dynamic n=500: **44.4%** e2e · recall@30 97.6% · tops every
  reported Table 4 baseline (vs MemOS 42.55, Mem0 39.0, A-Mem 35.4)
- Drift detector: **AUC 0.83** held-out (50/50 aligned/deviation, 2026-04-29) ·
  0.92 in-set
- V4-pro full-500: **56.4%** (-0.2 vs v0.8, 8× compute, shipped as Appendix C
  negative result)

### Tests

187 passing · 0 flake · 0 regression.

### Install

    pip install nautilus-compass==1.0.0
    npm install -g @nautilus/compass-mcp@1.0.0

### Known non-blocking deferrals

- Tier 2 #19 · v1 vs v2 driver ablation
- Tier 3 · Gate48 Run C' at temp=0.7

### Compatibility

Wire format and on-disk schemas are unchanged from rc2. rc2 clients
talk to 1.0.0 servers and vice-versa with no migration step.
