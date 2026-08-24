# ASSET MAP v3 · compass 冰山全量测绘(2026-08-24)

> 目的:发 v3.0.0 前把"冰山以下"盘清——每项标注 **生(在跑)/接(能用没在用)/眠(建完即眠)/死(废弃)**,证据可查。
> 判定标准:生=有进程/调用方在用;接=代码完整可运行但无消费方;眠=功能完成但从未接线;死=被替代/明确废弃。
> 这份地图同时是减法清单候选:眠/死项由用户拍砍。

## 总量(实测)

**~480 文件 · ~7.7 万行(不含 vtf 数据)· 162 个测试 · 53 份论文材料 · 64 个运维脚本**

| 域 | 文件 | 行数 | 最后活动 | 判定 | 说明 |
|---|---|---|---|---|---|
| 顶层引擎(daemon/recall/mcp/contract/merkle/distill…) | 17 | 9,011 | 8/22 | **生** | 核心在跑;merkle_chain/compass_verify 部分眠 |
| GEP 进化(胶囊/经验包/飞轮/gate B 适配) | 12 | 4,202 | 8/22 | **生** | 昨晚 Gate B/Gold 用它;capsule_schema 端到端待 V5 写端(接) |
| 运维体系(ops/ 64 脚本:cron/巡检/守护) | 64 | 8,244 | 8/23 | **半生** | 一部分在 cron 跑(health/compact/sync),大量一次性脚本眠;今天加 goalmode/daemon_start |
| 实验/评测工具(tools/) | 9 | 1,521 | 8/23 | **生** | recall_usefulness_exp/fuel_intake/heartbeat 全新在跑 |
| 论文/文档(paper 53 + docs 18 + specs 5) | 140 | 26,305 | 8/22 | **接(最大未开发资产)** | 黑盒vs白盒论文全套含 arXiv 清单——**从未对外发布**;UNIFIED_STRATEGY/统一战略 v2 在 docs |
| 测试 | 181 | 28,350 | 8/22 | **生** | 162 test 文件,gep/gate B 全覆盖 |
| benchmark env(ale/kernelbench/fde_benchmarks) | 16 | 1,958 | 7/17 | **眠→将活** | FDE 第3类交付过(飞书表有记录);等蒸馏线唤醒 |
| SDK/发布(npm/sdk/release/hf_space/cursor-ext) | 17 | 2,238 | 6/23 | **眠** | 对外发布全套雏形,从未发布——产品线(P 层)解冻即用 |
| 漂移执法(drift/) | 9 | 992 | 6/23 | **接** | hook 在用其中一部分;drift 深度分析眠 |
| 元记忆/OKF/裁判(metamemory/okf/judges) | 12 | 780 | 6/22 | **眠** | 互操作格式+裁判雏形,OKF exporter 完成未发布 |
| MCP durable/middleware | 5 | 542 | 6/24 | **眠** | 断线重连/中间件,2.0 时代产物,部分被 mcp_client 替代 |

## v3.0.0 应讲的故事(从地图生成,如实)

**v3.0 · 从记忆库到进化引擎**
1. 引擎:语义召回+正文直交+自愈心跳(生,今日实证)
2. 进化:GEP 胶囊+③类燃料+Gate B 外部裁决(生,Gold ×3 实证)
3. 蒸馏:SFT 管道+对照协议(进行中,L4a)
4. 治理:目标账本+合约到期亮牌+心跳执法(生,今日首立功)
5. 资产:26k 行文档/论文未发布(诚实披露,非功能)

## 减法候选(眠/死,请用户拍)

- mcp_durable/middleware(被替代) → 建议归档
- drift 深度分析、judges → 保留观察
- ops 一次性脚本 → 下批清理
- OKF/论文/SDK → 不是砍,是"待发布资产",进产品线排期
