## [1.0.0-rc2] · 2026-05-07 — "MCP A2A production-hardened · TLS · RBAC · rate limit"

rc1 shipped the MCP surface as **preview**. rc2 promotes it to
production-ready: TLS + mTLS, per-token RBAC, per-token rate limiting,
an auto-reconnect client with -32029 backoff, a three-peer scoped A2A
demo, and `resources/*` for streaming session logs. 110 new tests
(77 → 187), 0 flake, 0 regression.

### 🎯 Highlights since rc1

- 🔐 **TLS + optional mTLS for TCP transport** (Task #53) ·
  `--tls-cert / --tls-key / --tls-client-ca` on server · `tls=True` +
  `tls_ca_cert` + `tls_client_cert/key` on client · banner prints
  `(tcp)` vs `(tls)` · 10 tests incl. full mTLS round-trip + bad-CA /
  missing-cert rejection
- 🛡️ **Token-scoped RBAC** (Task #49) · per-token scope sets
  (`tools.read` / `tools.write` / `resources.read` / `*`) ·
  `--token-file TOKENS.json` for out-of-band rotation · tools/list
  now scope-filtered · 21 tests
- 🎚️ **Per-token rate limit** (Task #51) · classic token-bucket ·
  `--rate-limit TOKEN=rps/burst` · returns -32029 with exact retry-in
  delay · 23 tests
- ♻️ **Client auto-backoff on -32029** (Task #52) · `MCPClient(...
  rate_limit_retries=N)` parses the server's retry-in and sleeps
  automatically · opt-in (default 0 preserves strict behaviour) ·
  16 tests
- 📡 **MCP resources/\*** (Task #48) · `compass://session/...`
  URIs · `resources/list` + `resources/read` · session-log
  streaming for peers · 16 tests
- 🔁 **MCPClient with transparent reconnect** (Task #46) ·
  exponential backoff · reconnect telemetry · 6 tests
- 🤝 **A2A demo v2** (Task #50) · three scoped peers
  (observer / reasoner / admin) · real RBAC denial surfaced in the
  demo · resources round-trip end-to-end · 4 tests
- 🩺 **server/status endpoint** (Task #45) · active connections,
  bytes in/out, per-token call counts, uptime · thread-safe
- 🔑 **TCP transport with token auth** (Task #42) · `authToken` on
  initialize · shipped baseline before RBAC/TLS layered on top

### Changed

- `pyproject.toml` · v1.0.0-rc1 → v1.0.0-rc2
- `mcp_server.py` gained TLS plumbing, RBAC enforcement, rate-limit
  dispatch gating. Banner now announces transport variant.
- `mcp_client.py` promoted to a library surface · TLS + backoff +
  reconnect telemetry · `MCPClientError` kept for callers.
- A2A demo rewritten around scoped tokens + resources.

### Tech debt closed

- MCP surface is no longer "preview" · TCP transport API frozen for
  1.0.0 final (stdio was already stable).
- Release automation still the rc1 machinery (`.github/workflows/
  release.yml` + `scripts/release_notes_extract.py`) · rc2 slice
  extraction verified.

### Known gaps · remaining v1.0 blockers

- full-500 re-run with V4-pro (Task #27 · running on T4)
- v1 vs v2 driver ablation (Task #20 · blocked on #27)
- notifications/progress + cancelled (deferred · no current consumer)

### Notes

- Plaintext TCP remains the default for localhost dev. TLS is opt-in ·
  enable it whenever the server binds to a non-loopback interface.
- Rate limit and RBAC compose: RBAC decides *can*, rate limit decides
  *how much*. A token with `*` scope but a 1 rps / 1 burst bucket is a
  valid production pattern for emergency admin access.
- Test count on this branch: **187 passed · 56s** on Python 3.13.

