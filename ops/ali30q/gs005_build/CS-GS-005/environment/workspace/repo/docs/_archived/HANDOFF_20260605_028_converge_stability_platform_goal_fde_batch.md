# HANDOFF #028 · platform-soul · 收敛闭环+稳定可靠(平台 /goal)+ FDE 批次 6 题 + 组织产品主设计

> 写 2026-06-05 · 收口一个 ~多轮 marathon。单一 fresh-session 入口。取代 [#027](./HANDOFF_20260605_027_platform_soul_benchmark_arc_closed_fde_mainline.md)。

## Fresh-session 提示词(复制即用)
```
接 HANDOFF #028(platform-soul · 当前关键=收敛闭环+稳定可靠)。
session-start 必读(按序):
- docs/HANDOFF_20260605_028_...md(本文·全图)
- docs/plans/GOAL_2026-06-05_platform_4way_coupling_wiring.md(要 fire 的 /goal)
- docs/plans/2026-06-05-native-ai-org-fde-productization-master-design.md(组织/产品愿景·P2-P3 deferred)
- memory/session_20260605_native_ai_org_master_design_converge_stability_focus.md(聚焦定调)

战略锁定(勿重开):用户最终聚焦=当前唯一关键=收敛闭环+稳定可靠。其余宏大愿景(GUI/资金流/招募/培训/编队)captured-but-deferred(P2-P3·非drop)。先让 1 条 FDE 线可靠地闭再谈扩。

立即行动:fire `/goal platform-4way-coupling-wiring`(GOAL 文件里有 verbatim)。起手序 W4 自愈→W1 收敛(verdict-bus/事件脊柱)→W2 可感知→W3 A2A→W5 对外可用化(spike)。
并行卡点:v5 跑 data_002(球在 v5·cross-dialog·非本 /goal)。
```

## 30 秒状态
- **当前关键(用户定调·压倒一切)= 收敛闭环 + 稳定可靠**。其余 deferred(非 drop·在 roadmap P2-P3)。
- **要 fire 的 /goal = `platform-4way-coupling-wiring`**(已写好·W1-W5·起手序 W4 止血→W1 收敛→W2 可感知→W3→W5)。fresh session 粘 GOAL 文件 verbatim 段。
- **唯一卡点 = v5 跑 data_002**(soul+compass 段全齐·球在 v5)→ 证 1 条 FDE 线真闭。

## 收敛闭环 + 稳定可靠 = 已规划的什么
| 关键 | = | 状态 |
|---|---|---|
| 收敛闭环 | data_002 跑通 + W1 verdict-bus/事件脊柱(回路共享文件→substrate) | data_002 待 v5·W1 设计+字段锁定 |
| 稳定可靠 | W4 自愈(daemon KeyError@daemon.py:685/双 ship/LLM timeout/失败不静默)+ W2 可感知 + 维护审计 agent | 全在 goal·排序稳定优先 |

## FDE 批次状态(soul lane DONE)
- 6 题 checklist 攒成:data_001-006(3 一级类目 + L2/L3 + 多产物格式)· 全自校验过 checklist_scorer · `vertical-task-factory/data_00N_checklist.json`。
- data_001 闭环 11/11(v5 LLM 驱动·过我 QC)· data_002 三方齐待 v5 跑(跨题泛化验证)。
- 买方第三类(11 前沿基准复现)绿灯:都要·判质量+量级·生产 OK·效率高·自报价 → 下一步跑 1-2 开源 bench 出复现实样支撑报价(`BUYER_FRONTIER_BENCH_CAPABILITY_MATCH.md`)。

## 三框状态(收敛聚焦)
- **soul(我)**:6 题 checklist + RUBRIC §1-11 + 平台 4-way goal + verdict 字段锁 compass schema(W1.1)+ 主设计。
- **compass**:飞书全通(196 表+附件)· data_002-006 附件可下 · PoI adapter `credit_from_checklist_verdict` 对齐真 verdict · dual_flywheel goal。
- **v5**:producer 泛化成功(solve_task LLM 驱动 data_001 10/11)· 事件脊柱设计(已 ack 并进平台 W1·防平行造轮子)· **待跑 data_002**。

## 平台 4-way goal 要点(= 收敛+稳定的执行)
W1 事件脊柱(平台 OWN·吸收 v5 event_outbox·verdict-bus·字段锁 compass PoI)· W2 可感知(soul-activity 端点+企业微信活动 digest+修静默吞)· W3 A2A(协调走 a2a_relay)· W4 自愈(daemon/双 ship/timeout)· W5 对外可用化(spike·GUI/论坛门/KG 可视化)。GATE:内部 NAU 自指 held · 生产 DDL/企业微信真发 G-cloud 停报 · 事件脊柱合约 G-align 三框 buy-in · 大产品 G-spike 等用户拍。

## 组织/产品愿景(主设计·P2-P3 deferred·非 drop)
3 业务线人/agent 分工 · 人员招募/筛选/培训(自 QC 反馈)· GUI(飞书嵌 agent / Hermes 桌面 / 易装 CLI·傻瓜式)· 三流数字化(资金流=组织化真缺口)· 员工 agent 编队+维护审计自愈+数据复用(🔴 自迭代信号=外部 FDE verdict 非内部 NAU)。详见主设计 doc。

## Outstanding / backlog
- cnt_content_engine_soul_naming_a1(due 6/9):裁定已交付·等 compass consume 关。
- 安全:对话明文贴过 API key + 飞书凭据 → 建议轮换。
- checklist-from-task 否决项偶过标(1/6 重跑即正常)→ backlog 加 veto cap。
- harness/LLM call 加 timeout(=W4.3)。

## 守住(本 marathon)
benchmark 弧三连负已 closed(平台价值=外部 fitness 尺)· anchor #2 修订(字节=双轮引擎非 defer)· 全程守 anchor #3 反 spray(愿景 captured 不 build·先收敛+稳定)· 「真」不作强调副词。
