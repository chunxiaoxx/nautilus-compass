---
name: orgfuel-ORGM-8513bff6ffa756ab-ca2afc646f
description: "记忆条目 gmail-rest-fallback-recipe-20260910.md # Gmail REST fal"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-8513bff6ffa756ab
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 gmail-rest-fallback-recipe-20260910.md
# Gmail REST fallback 配方(gmail MCP 连不上时)

- token 目录:`~/.gmail-mcp/`——`credentials.json`(refresh_token)+ `client_secret.json`(client_id/secret 在 `installed` 或 `web` 键下)
- 流程:POST `https://oauth2.googleapis.com/token`(client_id/client_secret/refresh_token/grant_type=refresh_token)→ access_token → `GET https://gmail.googleapis.com/gmail/v1/users/me/messages?q=in:inbox newer_than:3d`(Bearer)→ 逐封 `?format=metadata&metadataHeaders=…` 取头、`format=full` 走 payload.parts 递归 base64.urlsafe_b64decode 取正文
- 重授权:`scripts/gmail_reauth.py`(testing-mode OAuth token 7 天死,invalid_grant 时先 myaccount.google.com/permissions 撤旧授权再跑;长期解=PUBLISH APP)
- 参考实现:`email_sender.py` 的 `_send_via_gmail`(env `COMPASS_GMAIL_REFRESH_TOKEN` 路线)

**2026-09-10 首用读数**:3 天 inbox 8 封,Traj
