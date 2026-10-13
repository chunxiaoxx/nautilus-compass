---
name: orgfuel-ORGM-86699e51ae35d53d-5c7a148c3e
description: "记忆条目 security-v09-xuserid-impersonation-20260830.md --- name"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-86699e51ae35d53d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 security-v09-xuserid-impersonation-20260830.md
---
name: security-v09-xuserid-impersonation-20260830
description: 8/30 重大洞修复:8770(v0.9)X-User-ID header-only 身份=公网可冒充任意用户读记忆+投毒写;三处改 Bearer JWT-only+五项矩阵验证;生产版在 /home/ubuntu/compass 与 repo 版分叉的部署陷阱
metadata: 
  node_type: memory
  type: project
  originSessionId: 803cee4f-6f04-4ee0-92fd-3ce055d70a29
  fact_status: measured
---

# v0.9 X-User-ID 冒充洞 · 修复定案(2026-08-30)

用户问"其他任何人接入 MCP 都能获得我个人的记忆吗" → 查出两通道答案相反:
- **8097 新 MCP 通道:不能**(scoped token fail-closed,见 [[security-workbuddy-token-scoping-20260830]])。
- **8770 老 v0.9 服务:能**——`auth_user` 的 legacy 分支 `if x_user_id: return x_user_id` 无任何验证(注释承诺的 user-exists 校验从未实现),且 nginx `location ~ ^/(v1|healthz|readyz)` + `/v9/` 把 8770 **全量代理到公网 443**。实测 `curl https://compass.nautilus.social/v1/rec
