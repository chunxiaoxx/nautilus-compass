---
name: orgfuel-ORGM-3af2014d6c6c58bf-3d86f30034
description: "记忆条目 gmail-verify-production-20260906.md Gmail 邮箱验证生产链 2026-"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-3af2014d6c6c58bf
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 gmail-verify-production-20260906.md
Gmail 邮箱验证生产链 2026-09-06 上线定案(任务 #43 完结):

**定案链(全部实测)**:GCP consent screen 转 **In production**(7 天死根因=Testing 状态轮换,项目级状态管所有客户端,新建客户端不解决)→ 新 client `318623800596-ehjjf3j9…`(installed,redirect=http://localhost)授权 → refresh_token(103 字符,scope gmail.modify+gmail.settings.basic,长期)→ 云端 `/etc/compass/mail.env` 四键 `COMPASS_GMAIL_CLIENT_ID/CLIENT_SECRET/REFRESH_TOKEN/FROM`(FROM=chunxiaoxx@gmail.com)→ 实弹发码 Gmail API 读回确认 → `COMPASS_EMAIL_REQUIRED=1` → **signup e2e 全绿**(signup 发码→收件箱读回真码→verify→login→cmp_live 签发)+四探针 FOUR-GREEN。顺序红线执行:凭证先落→实弹验证→最后开门禁。

**四坑**:
1. Windows 上传 env 片段带 CRLF → 值尾粘 `\r` → token endpoint 401(`mail.env: line 12: $'\r': command not found` 是 giveaway)。修复 `sudo sed -i 's/\r$//'`。**上传 env 一律先 LF**。
2. nginx sites-enabled/compass 只代理 `si
