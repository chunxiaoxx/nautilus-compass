---
name: orgfuel-ORGM-gmail-verify-production--218652c335
description: "--- name: gmail-verify-production-20260906 description: Gmai"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-gmail-verify-production-
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: gmail-verify-production-20260906
description: Gmail 邮箱验证生产链 9/6 定案——production refresh_token+四坑(CRLF 401/nginx 漏 verify 路由/probe env 配方)+signup e2e 全绿+FOUR-GREEN
metadata: 
  node_type: memory
  type: project
  originSessionId: 803cee4f-6f04-4ee0-92fd-3ce055d70a29
  modified: 2026-09-07T14:45:09.242Z
---

Gmail 邮箱验证生产链 2026-09-06 上线定案(任务 #43 完结):

**定案链(全部实测)**:GCP consent screen 转 **In production**(7 天死根因=Testing 状态轮换,项目级状态管所有客户端,新建客户端不解决)→ 新 client `318623800596-ehjjf3j9…`(installed,redirect=http://localhost)授权 → refresh_token(103 字符,scope gmail.modify+gmail.settings.basic,长期)→ 云端 `/etc/compass/mail.env` 四键 `COMPASS_GMAIL_CLIENT_ID/CLIENT_SECRET/REFRESH_TOKEN/FROM`(FROM=chunxiaoxx@gmail.com)→ 实弹发码 Gmail API 读回确认 → `COMPASS_EMAIL_REQUIRED=1` → **signup e2e 全绿**(signup 发码→收件箱读回真码
