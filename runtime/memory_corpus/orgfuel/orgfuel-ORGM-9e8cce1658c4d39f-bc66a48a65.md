---
name: orgfuel-ORGM-9e8cce1658c4d39f-bc66a48a65
description: "记忆条目 session_20260722-1257_client-auto-reconnect-shipped.md "
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-9e8cce1658c4d39f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 session_20260722-1257_client-auto-reconnect-shipped.md
# client auto-reconnect shipped

## 上下文
MCPClient transparent reconnect + backoff

## 内容
mcp_client.MCPClient wraps I/O errors (ConnectionReset / BrokenPipe / timeout) with exponential backoff reconnect and re-runs initialize before replaying the request. Hard failures like bad-token surface immediately as MCPClientError.
