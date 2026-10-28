# 生产配方卡 · platform(2026-10-18 锁版)

> 产品=平台本身(章程):DMAS/A2A/SOUL/组织协同维护+网站系统。本卡=平台自身稳态配置。

## 稳态配置(锁版)
| 件 | 锁定值 | 坐标 |
|---|---|---|
| nginx 正本 | 主域+app+org+bench 四 conf 入仓,禁旁路直改 | master 9596b15a1 线 |
| 活性巡检 | **10 锚**(8 资产+members_active+soul_daemon),30min timer,红灯函 4h 去重 | ops/liveness_check.py(388f3455d) |
| 组织 loop | platform-loop 15min(SLA/值守催办/默认结案/决策数据集) | ops/platform_loop.py(aa59075e8 双豁免) |
| 结算 truth | platform_nau_ledger+fuel_settle 评分即结算;**orders 表非结算正本**(P2 台账判) | ops/fuel_settle.py |
| 信箱白名单 | 13 主体(+openclaw 10/18 用户批) | api/org.py(ca68a0f39) |
| 判分链 | 提测→受理→判读卡→bench 双锚,E2E 6/6 | assay_*(10/15 闭环) |

## 班表
- 30min:活性巡检(timer)
- 15min:组织 loop(timer)
- 每轮值守(loop prompt):三查(信箱 data 键解析!)/时钟事件/in-flight
- 周:RUNBOOK 全表+E2E 提交旅程(e2e_submit_journey.js)

## 红线
1. 注入面纪律:加内容先删等量旧内容(CLAUDE.md)
2. 无消费者不生产;读数件消费方=推送通道,等访问盘面拒建
3. 描述循环禁令:同一问题第三次描述必须三选一
4. 部署一律 push+云 checkout+重启+curl 三验;凭据永不入库不入函明文(交付走云端直读直写)
5. 机制冻结:不新增跨框机制;坏了修不重构(P2 台账为界)

## 产品路线(在排)
P1 配方卡五框→P3 组织橱窗各框产品上墙→P4 判读交付链(候 gaurav)→P5 openclaw 闭环(候首调);P2 已毕(DMAS_A2A_INVENTORY_V1)。
