---
name: orgfuel-ORGG-3fde8bcad32a0000-1e322775af
description: "判读档判例 2026-09-02-summary-layer-preregistration · 二、方案设计:摘要层("
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-3fde8bcad32a0000
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-09-02-summary-layer-preregistration · 二、方案设计:摘要层(session summary layer)
## 二、方案设计:摘要层(session summary layer)

### 2.1 session 摘要卡(预生成,一次构建全量复用)

对数据集每个 unique session 生成一张结构化摘要卡(ARK coding plan 端点,plan 内额度):

```
[Session <id> · <date>]
USER FACTS: 每条一行,保留实体/数量/金额/日期(可数、可聚合)
  - 要去干洗店取回海军蓝西装
  - 买了柠檬树,花了 $85
ASSISTANT: 助手做过/说过/推荐的(每条一行)
  - 推荐了三个瑜伽馆
TOPICS: 3-5 个关键词
```

关键设计约束:
- **可数性优先**:ms 题 = 数东西,USER FACTS 的 bullet 结构让"数数"变成数 bullet。
- **保实体保数量**:金额/数量/日期/专名逐条保留,不写段落式总结(段落会吞数量)。
- 输入预算:session 原文按 6000 字符分段(超过则分段摘要再合并),单卡输出 ≤150 字。
- 幂等缓存:summary_cache.json 按 session_id + 内容 hash 键,断点续跑。

### 2.2 context 组装(ZMM_SUMMARY_LAYER=1 时,ms/ssa/tr 三型路由)

```
=== Session Timeline(全部 top5 session 的摘要卡,按日期排序)===
[Session A · 2023-01-15] USER FACTS: …
[Session B · 2023-01-22] USER FACT
