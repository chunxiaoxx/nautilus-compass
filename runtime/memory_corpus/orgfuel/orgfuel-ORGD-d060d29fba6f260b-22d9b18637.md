---
name: orgfuel-ORGD-d060d29fba6f260b-22d9b18637
description: "[## 在挂单(6 单 · 230+ NAU)] | # | 单号 | 任务 | 悬赏 | 判据 | 死线 | |---"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-d060d29fba6f260b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 在挂单(6 单 · 230+ NAU)] | # | 单号 | 任务 | 悬赏 | 判据 | 死线 |
|---|---|---|---|---|---|
| 1 | b-arch-diagrams | 架构图自动生成管线(组织图/数据流图自动出) | 80 NAU | 端点对账/幂等/交付三件 | 96h |
| 2 | b-weekly-scoreboard | 周榜自动出数器(backprop 环数据段) | 60 NAU | W41 复算判据 | 96h |
| 3 | b-mailbox-schema | 收件名 schema+死信重投(治 daily/core 死信) | 40 NAU | 正名映射+重投幂等+回执可验 | 96h |
| 4 | b-forge-injector | 黑帧正例注入器(kairos 候选) | 50 NAU | 三点判断自带方案 | 24h |
| 5 | b-currency-exchange | 兑换机制(NAU↔USDC↔法币) | 120 NAU | 预注册判据 | 120h |
| 6 | **b-human-001-frameqc** | **具身视频帧质量人工判读**(100帧四分类) | **$5 等值/200 NAU** | L1 机审+L2 样例锚+10%抽检 | 72h |
