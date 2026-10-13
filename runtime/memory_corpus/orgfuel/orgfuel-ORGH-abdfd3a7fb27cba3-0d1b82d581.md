---
name: orgfuel-ORGH-abdfd3a7fb27cba3-0d1b82d581
description: "commit 68733f8ed78e 2026-09-05 feat(auth): email_sender 加 Gm"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-abdfd3a7fb27cba3
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 68733f8ed78e 2026-09-05
feat(auth): email_sender 加 Gmail API OAuth 后端(方案B·零用户新操作)——复用 gmail-mcp grant
- 双后端自选: COMPASS_GMAIL_*(refresh token→access→gmail/v1 send raw,scope gmail.modify 含发信)优先,COMPASS_SMTP_* 兜底
- 纯 urllib 标准库零新依赖;urllib_request_urlopen 模块级 seam 供测试 mock
- 测试+2(gmail 刷新+POST raw 成功路径/invalid_grant→EmailSendError)共 21 绿
- 已知红旗待实弹验证: 原 grant refresh_token_expires_in≈7d,GCP 应用 Testing 状态下 refresh token 会 7 天轮换——服务器实测 refresh 定生死,失败则退 App Password 方案
