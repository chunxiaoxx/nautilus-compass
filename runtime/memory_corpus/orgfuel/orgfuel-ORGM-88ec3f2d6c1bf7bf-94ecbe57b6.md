---
name: orgfuel-ORGM-88ec3f2d6c1bf7bf-94ecbe57b6
description: "记忆条目 session_20260722-1257_MCP-TCP-auth-landed.md # MCP TCP "
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-88ec3f2d6c1bf7bf
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 session_20260722-1257_MCP-TCP-auth-landed.md
# MCP TCP auth landed

## 上下文
token-gated TCP transport for cross-machine A2A

## 内容
mcp_server.py --transport tcp --token SECRET now accepts concurrent JSON-RPC clients. Bad token → -32001. Strips authToken before forwarding to handle_message so it never leaks in logs.
