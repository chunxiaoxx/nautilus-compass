---
name: orgfuel-ORGM-gmail-rest-fallback-reci-05d80ac85a
description: "--- name: gmail-rest-fallback-recipe-20260910 description: ""
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-gmail-rest-fallback-reci
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: gmail-rest-fallback-recipe-20260910
description: "gmail MCP 挂时的 REST 读信 fallback 配方——token 在 ~/.gmail-mcp/(credentials.json refresh_token+client_secret.json),换 access_token 后调 gmail API;Trajko 9/8 ack 已处理确认"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 803cee4f-6f04-4ee0-92fd-3ce055d70a29
  modified: 2026-09-09T19:21:55.111Z
fact_status: inferred
---

# Gmail REST fallback 配方(gmail MCP 连不上时)

- token 目录:`~/.gmail-mcp/`——`credentials.json`(refresh_token)+ `client_secret.json`(client_id/secret 在 `installed` 或 `web` 键下)
- 流程:POST `https://oauth2.googleapis.com/token`(client_id/client_secret/refresh_token/grant_type=refresh_token)→ access_token → `GET https://gmail.googleapis.com/gmail/v1/users/me/messages?q=in:inbox newer_than:3d`(Bearer)→ 逐封 `?format=metadata
