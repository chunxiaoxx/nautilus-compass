---
name: orgfuel-ORGG-9f7967ede94e3abd-926ccbdb32
description: "判读档判例 AUTO_PUBLISH_ARCHITECTURE_20261001 · 二 · 统一发布器设计(pub.p"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-9f7967ede94e3abd
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 AUTO_PUBLISH_ARCHITECTURE_20261001 · 二 · 统一发布器设计(pub.py)
## 二 · 统一发布器设计(pub.py)

```
tools/publisher/
  core.py        # publish(platform, content, opts) -> receipt
  adapters/
    x_cdp.py     # 现 x_post.py 重构并入
    reddit_praw.py   # PRAW adapter(新,正道)
    discord_webhook.py  # requests POST(新,最简)
    zhihu_cdp.py # 9225 管道并入
    square_api.py   # X-Agent-Key(已在)
  creds/         # 各平台凭证(env 文件,.cache 不入仓)
  receipts/      # 每次发布 JSON 回执(platform/url/ts/content_sha)→ 周汇入 OUTREACH_LEDGER
```

- **内容适配层**:一稿多格式(markdown 主稿→X 截断版/Reddit 全文/知乎富文本/Discord embed)
- **审计链**:发布前 content_sha 入台账(发什么有据),回执带 URL(发到了有证)——与 B 级外发制(1840)对齐:发布=已批内容的执行动作
- **失败语义**:回执记 error+可重试;连续 2 失败升报 LOOP 轮
