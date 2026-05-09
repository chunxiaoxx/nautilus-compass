## [1.0.0] · 2026-05-08 — stable · public open-source release

`1.0.0-rc2` (2026-05-07) shipped unchanged as `1.0.0`. No code or test
changes since rc2; the version bump exists to mark the stable cut and
align all version strings (`pyproject.toml`, `package.json`,
`.claude-plugin/plugin.json`, `mcp_server.SERVER_VERSION`).

The repository went **public** on 2026-05-08 — code, anchors, frozen
test data, and audit-log tooling are MIT-licensed (CC0 for anchor
files) at https://github.com/chunxiaoxx/nautilus-compass.

### Eval headlines (locked)

- **LongMemEval-S** n=500: **56.6%** (v0.8 · 2026-05-04 lock)
- **EverMemBench-Dynamic** n=500: **44.4% (Run 1)** / **47.3% (Run 2, n=497)**
  · cross-run mean **45.84%** · 95% CI on Run 2: [42.9%, 51.7%] (B=10000 bootstrap)
  · tops every reported Table 4 baseline (Mem0 37.09, Zep 39.97, MemOS 42.55)
- **Drift detector**: **AUC 0.83** held-out (50/50 aligned/deviation, 2026-04-29)
  · 0.92 in-set
- **V4-pro full-500**: **56.4%** (-0.2 vs v0.8, 8× compute, shipped as
  Appendix C negative result)

### Cross-judge sensitivity (Paper 2 §6.5)

Gemini 2.5 Pro on a stratified n=100 subsample of Run 2:
- DeepSeek V4-flash judge: 42.0% · Gemini 2.5 Pro judge: 28.0%
- Cohen's κ = 0.70 (substantial)
- 14 disagreements all DS=Y/Gemini=N (Gemini consistently stricter)
- Manual inspection: both judges have systematic biases; true accuracy
  on this subsample sits in [28%, 42%], balanced-judge mid ~35-40%
- Honest framing: future EverMemBench reproductions should publish at
  least two judge-family numbers per run

Raw per-question logs ship in the repo:
`paper/results/em_bge_v3_per_question.jsonl`,
`paper/results/em_cross_judge_gemini_per_question.jsonl`.

### Tests · 228 passing · 0 flake · 0 regression

### Install

    pip install nautilus-compass==1.0.0
    npm install -g @nautilus/compass-mcp@1.0.0

Or one-line auto-install for any of 6 supported MCP clients
(Claude Code, Claude Desktop, Cursor, Cline, Continue.dev, Zed):

    python scripts/install_to_agent.py

### What ships in v1.0.0

- Full **MCP A2A protocol surface**: stdio + TCP + TLS + mTLS, per-token
  RBAC, per-token rate limiting, auto-reconnect client with `-32029`
  backoff, `notifications/{progress,cancelled,message}`, `logging/setLevel`,
  `resources/*` for session-log streaming, third-party stdio shim.
- **5 user-facing slash commands** in Claude Code: `/compass-verify`,
  `/compass-drift`, `/compass-recall`, `/compass-search`, `/compass-status`.
- **Merkle hash chain** for tamper-evident audit log on every observation
  write (`session_writer.py`).
- **Cloud gateway** at `compass.nautilus.social` (cn-shanghai, 305 users),
  `/healthz` reports `version=1.0.0`, `/.well-known/agent.json` advertises
  v1.0 capabilities.

### Documentation

- [`README.md`](README.md) — English-first overview (international default)
- [`README.zh-CN.md`](README.zh-CN.md) — 中文版
- [`docs/AGENT_ONBOARDING.md`](docs/AGENT_ONBOARDING.md) — per-agent install configs (6 platforms + 3 frameworks)
- [`docs/REPRODUCE.md`](docs/REPRODUCE.md) — paper + benchmark replication guide
- [`docs/PLATFORM_HANDSHAKE.md`](docs/PLATFORM_HANDSHAKE.md) — OSS↔SaaS coordination contract
- [`docs/SAAS_OPERATIONS.md`](docs/SAAS_OPERATIONS.md) — SaaS-side operational template
- [`docs/mcp-usage.md`](docs/mcp-usage.md) — raw MCP protocol guide

### Known non-blocking deferrals

- Tier 2 #19 · v1 vs v2 driver ablation
- Tier 3 · Gate48 Run C' at temp=0.7

### Compatibility

Wire format and on-disk schemas are unchanged from rc2. rc2 clients talk
to 1.0.0 servers and vice-versa with no migration step.

### Upgrade path

From `1.0.0-rc2`:

    pip install --upgrade nautilus-compass
    # or
    npm install -g @nautilus/compass-mcp@1.0.0

No data migration. Restart your MCP client to pick up the new server
version string in `/.well-known/agent.json`.

From `0.9.x`:

    bash daemon_start.sh   # restart daemon for v1.0 anchors + Merkle chain
