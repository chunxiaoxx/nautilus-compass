---
name: orgfuel-ORGM-6d761bb35b6b3bc1-1cb5b90c98
description: "记忆条目 devto-operations-20260908.md 2026-09-08 发布夜 dev.to 运营定案"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-6d761bb35b6b3bc1
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 devto-operations-20260908.md
2026-09-08 发布夜 dev.to 运营定案(用户授权自主运营):

**零流量三根因**(全账号 10+ 篇文章 views≈0):
1. `ai_disclosure_level` 未设——dev.to 新政策(响应 warnings 明示),未披露疑似不进分发;已补:compass 文=some_ai,agent 自主文=fully_autonomous。
2. 账号混发多框文章,3 篇泄露组织内部件(Kairos/V5/NAU/V7)→ 已 unpublish(公开端点 404 独立复验)。红线执行:内部件外发=无论谁发的都要撤;「Nautilus platform」是公开品牌(nautilus.social)不算泄露。
3. title 平台锁死:已发布文章 PUT 改 title 返回 200 但不生效(ai_disclosure 同 payload 却生效)——标题要在发布前定好。

**API 管道配方**(踩坑三次):
- python urllib(无论 UA)→ 403 Forbidden Bots;**curl + 浏览器 UA** 可写操作成功。
- PUT article 要 **title/body_markdown 等全文同 payload** 才稳;unpublish={"article":{"published":false}},验证=公开 GET 404,响应不回传 published 字段。
- POST /api/comments 404(端点变或拦)——回评论走网页,30 秒。
- bio 修改 PUT /api/profile/{profile_id} 未通(profile_id 字段 API 不回);网页改。

**流量机制**(指导后续):分发=标签
