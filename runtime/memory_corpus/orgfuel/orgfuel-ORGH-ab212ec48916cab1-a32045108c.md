---
name: orgfuel-ORGH-ab212ec48916cab1-a32045108c
description: "commit 24c2b7a707a9 2026-05-07 version: bump runtime SERVER_"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-ab212ec48916cab1
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 24c2b7a707a9 2026-05-07
version: bump runtime SERVER_VERSION 0.9.0-dev → 0.9.5
pyproject.toml has been on 0.9.5 since the npm/PyPI release, but the runtime
SERVER_VERSION constants in mcp_server.py, compass_http_v09.py, and the
Dockerfile OCI label were stuck on 0.9.0-dev. MCP clients that inspect
serverInfo.version (Cline / Cursor / Claude Desktop) would have seen the
mismatch on initialize handshake.

Verified end-to-end: piping initialize JSON-RPC into mcp_server.py now returns
serverInfo.version=0.9.5.
