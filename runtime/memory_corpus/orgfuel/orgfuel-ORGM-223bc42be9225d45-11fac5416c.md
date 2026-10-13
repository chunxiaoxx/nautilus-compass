---
name: orgfuel-ORGM-223bc42be9225d45-11fac5416c
description: "记忆条目 devto-comment-no-api-and-harness-pr.md 2026-10-12 dev.t"
metadata:
  type: reference
  source: org_fuel:memory_r3
  pf_id: ORGM-223bc42be9225d45
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 devto-comment-no-api-and-harness-pr.md
2026-10-12 dev.to 外联两发现:

1. **dev.to v1 API 没有 POST /api/comments**(实测三形态全 404:commentable_type=Comment/Article、无 type;此前的 429 是全局限流在路由解析前拦截,误导性极强——**429 不代表路由存在**)。API key 只能发文不能回评论。回复评论需前端会话(账号走 GitHub OAuth 无密码,curl 管道死)。**429 不代表路由存在**要记住。
2. 三条 PRECOR 帖评论回复终稿在 `runtime/outreach/devto_reply_{arhancanli,baumgaerben_post,mp6}_20261012.md`,候会话凭据或手动发。baumgaerben/arhancanli 的回复档 10/11 就写了但从未发出——**写了档≠发了帖**再度实证,幸有实测抓出。mp6nfjxhrlxc 尾部带 "labagent .tech" 推广(spam 嫌疑),只回技术点不接广告。

**Why:** 外联渠道"配方在档"不等于"当前可用",API 路由会变;发帖类动作必须 post 后读回验证。

**How to apply:**
- dev.to 读数据 OK:`/api/articles?username=`、`/api/comments?a_id=`、`/api/comments/<id_code>`(children 嵌套);403 Forbidden Bots 加浏览器 UA 解决。
- 渠道数据:PRECOR 帖(10/10 quantized judge)r=1 c=3 全账号最佳;其余 29 帖评论≈0——广
