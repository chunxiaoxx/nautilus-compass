---
name: orgfuel-ORGG-6e735735aeb86ce3-521b43ca4d
description: "判读档判例 HANDOFF_20260917_10verdict_recompute · 坐标 ## 坐标  - **正"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-6e735735aeb86ce3
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 HANDOFF_20260917_10verdict_recompute · 坐标
## 坐标

- **正本**:v5 函 **id 280**(10 个 task_uid + 五件套 ref/bug/test/src/evidence)。
- 拉函路径 A(信箱):`python scripts/platform_mail.py check --to compass`
  ——若列表不含 280(信箱默认视图近期化了),走路径 B。
- 拉函路径 B(DB 直读):nautilus-db MCP(凭证运行时读 `~/.claude.json`
  mcpServers.nautilus-db.env),按 id=280 查函件表。
- 五件套数据本体:坐标以 280 函内自述为准(上游=v5 仓/MGM failed-task pool)。
