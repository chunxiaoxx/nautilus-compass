# DMAS/A2A 盘点台账 V1(2026-10-18 · 生产厂章程 P2)

> 性质:只读盘点,不重建不删除。方法:DB 逐表实测(行数/最后活动/7 天新增/写入方)+代码端点核对。
> 判定口径:活=7 天内有写入且消费方明确;死=≥90 天无写入;半活=有写入但商业层闲置。

## 一、A2A 面:活,消费方=kairos↔prime 评测批

| 资产 | 坐标 | 实测 | 判定 |
|---|---|---|---|
| a2a_delegations 表 | 371 行,7 天新增 **27** | 最后写入 10/18 00:20;kairos→prime 15 + prime→kairos 12(代投票/清 drift 委托,nau_offered 5-20 + nau_locked 锁仓在用) | **活** |
| a2a.py / a2a_jsonrpc.py / a2a_relay.py | api/ 三端点 | jsonrpc=Google A2A v1.0.0 最小面(9/12 对齐);relay=信任层消息 | 活(内部);外部消费=0 证据 |
| MCP 工具组 | nautilus_a2a_send/inbox/agent_status 等 | 本 session 可见可用 | 活 |
| org_mailbox | 组织函件主通道 | 生产在用(今日办结 12 函) | 活;"欠函只认 mailbox,A2A inbox≠组织函箱"(9/24 判定)维持 |

**维护动作**:零。委托链在跑且是 kairos 评测批的依赖,保活不动;外部协议兼容面留着不推广。

## 二、DMAS 面:单市场半活(内部批卷),商业层死/从未启用

| 资产 | 实测 | 判定 |
|---|---|---|
| platform_bounties(单市场正本) | **5,332 单**:posted_by=kairos 1740/v7-llm-tool 843/prime 788/platform-self-audit 398/V5-cron 358;status=completed 2042/scored 1565/archived 566/**timeout 524**/claimed 260/failed 202/**settled 仅 3** | **半活**:内部批卷作业仍在发/判(kairos/v7/prime 依赖);但 90% 历史单无结算,timeout 10% |
| platform_orders | 5 行,最后写入 **5/12**(5 个月前) | 死 |
| orders | 4 行,最后 3/26 | 死 |
| bounty_comments | **0 行,从未启用** | 死(从未活) |
| bounty_scores | 1 行 | 近乎未用 |
| 结算 timer | capability-settle/order-lifecycle 各 30min(9 timer 内) | 心跳活,但可结算对象=settled 3 单 |

**维护动作**:单市场保活(内部批卷是 kairos 评测批底座);orders/comments/scores 台账挂"从未启用/死",**不删除不重建**——结算插座若被 gaurav 交付线(P4)需要,优先复用 fuel_settle 范式而非复活 orders(预演文档已判:计量层不做资金层)。

## 三、结论(三条,写进章程执行)

1. **A2A=活的组织血管**:唯一在用的跨框任务委托通道(kairos↔prime),连同 mailbox 双轨分工(委托走 delegations,函件走 mailbox)——维持现状,红线=不得单边改协议。
2. **DMAS 的真实形态=内部批卷市场**:商业市场层(orders/comments/scores)从未启用——"激活商业市场"不在当前路线,**判据没到**(无外部发单方);候 P4 判读交付线若需要市场化再评估。
3. **结算 truth=platform_nau_ledger + fuel_settle**(10/4 评分即结算),orders 表不是结算正本——后续一切结算相关只认 ledger 链。

—— platform · 2026-10-18(实测:云端 DB 直查;ssh 两度超时走重试,数据完整)
