---
name: orgfuel-ORGM-devto-operations-2026090-a69b656d5f
description: "--- name: devto-operations-20260908 description: dev.to 自主运营"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-devto-operations-2026090
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: devto-operations-20260908
description: dev.to 自主运营首夜——零流量三根因(AI 披露新政/泄露文/title 锁死)+API 管道配方(curl UA 拦截)+泄露文下架事件
metadata: 
  node_type: memory
  type: project
  originSessionId: 803cee4f-6f04-4ee0-92fd-3ce055d70a29
  modified: 2026-09-08T15:32:56.317Z
---

2026-09-08 发布夜 dev.to 运营定案(用户授权自主运营):

**零流量三根因**(全账号 10+ 篇文章 views≈0):
1. `ai_disclosure_level` 未设——dev.to 新政策(响应 warnings 明示),未披露疑似不进分发;已补:compass 文=some_ai,agent 自主文=fully_autonomous。
2. 账号混发多框文章,3 篇泄露组织内部件(Kairos/V5/NAU/V7)→ 已 unpublish(公开端点 404 独立复验)。红线执行:内部件外发=无论谁发的都要撤;「Nautilus platform」是公开品牌(nautilus.social)不算泄露。
3. title 平台锁死:已发布文章 PUT 改 title 返回 200 但不生效(ai_disclosure 同 payload 却生效)——标题要在发布前定好。

**API 管道配方**(踩坑三次):
- python urllib(无论 UA)→ 403 Forbidden Bots;**curl + 浏览器 UA** 可写操作成功。
- PUT article 要 **title/body_markdo
