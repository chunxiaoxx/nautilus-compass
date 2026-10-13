---
name: orgfuel-ORGG-f79aade278ed3892-3ef25415f1
description: "判读档判例 CLOUD_RECALL_LIVELOCK_20261012 · 一、链路与症状 ## 一、链路与症状  `"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-f79aade278ed3892
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 CLOUD_RECALL_LIVELOCK_20261012 · 一、链路与症状
## 一、链路与症状

```
Claude Code → https://compass.nautilus.social/mcp/ (Bearer)
  → nginx 8443 → mcp_server.py :9877 (TCP) → daemon_v33.py :9876 (systemd: compass-bge-daemon)
```

- initialize / tools/list 全正常(Bearer 有效,serverInfo 3.1.0)——门与 token 无辜
- `tools/call recall` → **瞬时**(0.0s)返回 `daemon overloaded - retry`,非超时
- ping / status 正常(v3.2 MSG_PEEK 快道,过载时仍可探——该设计生效)
