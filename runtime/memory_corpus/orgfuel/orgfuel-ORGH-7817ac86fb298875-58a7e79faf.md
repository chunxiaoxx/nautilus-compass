---
name: orgfuel-ORGH-7817ac86fb298875-58a7e79faf
description: "commit ec50e7daa103 2026-06-23 fix(v2.3.0 收口): de-flake test"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-7817ac86fb298875
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit ec50e7daa103 2026-06-23
fix(v2.3.0 收口): de-flake test_mcp_client + 版本统一 bump 2.2.0→2.3.0
- systematic-debugging 定根因:_spawn_server 硬等 3.0s 太紧(idle冷启0.7-1.2s·
  全套高负载首spawn超3s·2次全套跑1失1过=flaky·非产品bug)。修=15s deadline+
  EOF早退+超时暴露server stderr(不掩盖真崩)。
- 版本号 6 处散在 2.2.0(pyproject/__init__/mcp_server.SERVER_VERSION/recall.
  PLUGIN_VERSION/package.json/server.json×2)→ 统一 2.3.0(test_version_sync 守卫)。
27 targeted 测绿(version_sync+mcp_server+mcp_client)。
