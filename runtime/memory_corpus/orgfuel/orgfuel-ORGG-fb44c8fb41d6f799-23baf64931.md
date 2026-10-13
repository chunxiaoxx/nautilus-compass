---
name: orgfuel-ORGG-fb44c8fb41d6f799-23baf64931
description: "判读档判例 2026-06-20-compass-serving-semantic-recall · Task 4: 端"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-fb44c8fb41d6f799
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-20-compass-serving-semantic-recall · Task 4: 端到端语义验证(verification-before-completion · 真证据)
## Task 4: 端到端语义验证(verification-before-completion · 真证据)

**目标**:证 bge-m3 召回胜过关键词基线(B 用不同措辞召回 A 的 learning)。**本地起 daemon + serving 或对 staging·非生产**。

**Steps:**
1. 构造:同 user 两 agent。agent A `POST /v1/observations` 写 learning（措辞 X·如 "retry with exponential backoff on 429 rate limit"）。
2. agent B `GET /v1/recall?cross_agent=true&q=<措辞 Y 语义近·如 "handle too-many-requests throttling">`。
3. 断言:bge-m3 路径命中 A 的 obs（score 高·`ranker:bge-m3`）;同 query 关键词基线（daemon 停）miss 或排末。
4. 对照:`q` 与 A content 无词面重叠但语义近 → 关键词 0.5 平分排不出·bge-m3 排第一 = 升级价值实证。
5. 记录真 curl 输出 + 两 ranker 对比进收尾 memory。

**无新增生产代码·验证脚本可留 `examples/`。**

---
