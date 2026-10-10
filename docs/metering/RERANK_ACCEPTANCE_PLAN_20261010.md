# rerank 在线验收方案(2026-10-10 · R489 · 部署四步第 4 步细化)

> 前置:部署序列①合 main(PG 流程)②隧道自启 ③双开关——本档=第 4 步"验收"的可执行定义。判据源=E1-TUNE v1 冻结档(EIGHTB/SEVENB_PREREG 同源纪律,零新判据)。

## 一、验收判定表(预注册,只许更严)

| 门 | 判据 | 口径 |
|---|---|---|
| V1 功能门 | daemon 开 rerank 后,recall 输出的 top 顺序与离线 E1 组合管线(0.8333 读数管线)对同一查询集一致 | 抽 10 query,逐条比对 |
| V2 延迟门 | 带 rerank 的 recall 端到端 P50 ≤ 3s(本机预算) | 30 query 实测 |
| V3 回退门 | 隧道断开(杀 a100_rerank_tunnel)→recall 自动回退 dense 顺序,不报错不挂起 | 断链实弹 3 次 |
| V4 开关门 | COMPASS_PROD_RERANK=0(默认)行为与现版 byte-identical | 抽 5 query diff |

## 二、验收执行序(部署窗内,~30 分钟)

1. 合 main+重启 daemon(开关 off)→ V4 基线 diff;
2. 开双开关(COMPASS_PROD_RERANK=1 + COMPASS_RERANK_REMOTE=127.0.0.1:19879)→ 重启;
3. V1 一致性 10 query(取 A_plus_queries_v2 前 10)+V2 延迟 30 query;
4. V3 断链实弹(kill tunnel→recall→观察回退→重启隧道);
5. 全过→验收报告落档(rerank 上线正式化);任一不过→开关回 off,问题归因。

## 三、回滚预案

开关回 off 即回滚(零数据迁移);隧道守护独立存在不影响其他服务;daemon 回退=git revert 单 commit。

—— compass · RERANK-ACCEPTANCE · R489 · 2026-10-10
