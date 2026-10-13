---
name: orgfuel-ORGG-714aaa0f3e375281-30a653f96e
description: "判读档判例 2026-08-30-multi-tenant-memory-design · 3. 地基实物(全部已在产,"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-714aaa0f3e375281
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-08-30-multi-tenant-memory-design · 3. 地基实物(全部已在产,不重造)
## 3. 地基实物(全部已在产,不重造)

| 件 | 位置 | 状态 |
|---|---|---|
| scoped token 机制(`read:<p>`/`write:<p>`/`read:*`,fail-closed) | 8097 HTTP + 9877 TCP 共用 `/etc/compass/tokens.json` | ✅ 8/30 六项 DENY/ALLOW 矩阵实测通过 |
| 多用户数据模型(users/agents/observations 按 user_id 外键) | 8770 v0.9(9/15 退役,模型随迁) | ✅ 已是完整多租户形态 |
| JWT 签发/校验 | 8770 signup/login + NAUTILUS_JWT_SECRET | ✅ 五项矩阵含合法 JWT 200 |
| token 签发/撤销工具 | `ops/compass_token_admin.py` + agent_quickstart 默认 scoped | ✅ 8/28 起新 token 默认最小权限 |
