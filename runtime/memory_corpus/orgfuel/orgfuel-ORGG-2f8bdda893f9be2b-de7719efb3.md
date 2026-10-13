---
name: orgfuel-ORGG-2f8bdda893f9be2b-de7719efb3
description: "判读档判例 AUTO_PUBLISH_ARCHITECTURE_20261001 · 一 · 现状盘点(实测) ## 一"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-2f8bdda893f9be2b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 AUTO_PUBLISH_ARCHITECTURE_20261001 · 一 · 现状盘点(实测)
## 一 · 现状盘点(实测)

| 平台 | 现役资产 | 卡点 | 正道 |
|---|---|---|---|
| X | x_post.py(9226 CDP,已修 Inline 钮) | 登录态依赖浏览器 | ✅ 可用;可选升 X API($100/m 基础档写帖,**不划算,CDP 够用**) |
| Reddit | 稿备+CDP 死通道(shadow DOM/busy) | 浏览器自动化脆 | **PRAW+Script App OAuth**(官方免费):reddit.com/prefs/apps 建 script 型 app→client_id/secret+账号→全自动发帖/评论/读信 |
| 知乎 | 9225 键盘管道(dry-run 18/18) | 403 复验中 | 无官方 API→CDP 兜底维持 |
| Discord | 9224 CDP 配方(9/27) | — | **Webhook 最优**:频道 webhook URL 一行 curl,零登录零浏览器 |
| dev.to | API key 在仓 | 平台衰退(已放弃) | — |
| HN | curl 管道 | 需养号 | 维持 |
| 广场 | X-Agent-Key API ✅ | — | ✅ 已全自动(今天 id=27 实证) |
