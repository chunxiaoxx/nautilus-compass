---
name: orgfuel-ORGG-6b8e574f0ae0bb88-031181826c
description: "判读档判例 RERANK_ACCEPTANCE_PLAN_20261010 · 二、验收执行序(部署窗内,~30 分钟)"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-6b8e574f0ae0bb88
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 RERANK_ACCEPTANCE_PLAN_20261010 · 二、验收执行序(部署窗内,~30 分钟)
## 二、验收执行序(部署窗内,~30 分钟)

1. 合 main+重启 daemon(开关 off)→ V4 基线 diff;
2. 开双开关(COMPASS_PROD_RERANK=1 + COMPASS_RERANK_REMOTE=127.0.0.1:19879)→ 重启;
3. V1 一致性 10 query(取 A_plus_queries_v2 前 10)+V2 延迟 30 query;
4. V3 断链实弹(kill tunnel→recall→观察回退→重启隧道);
5. 全过→验收报告落档(rerank 上线正式化);任一不过→开关回 off,问题归因。
