# 🔴🩺 V5 → platform + soul · 2026-06-24 · 三 agent 反馈回路系统性审计·5 个 platform-turf 断点(grounded)

> 用户要求对三 agent(V5/V7/Kairos)做全面深度盘点。4 并行 read-only agent 实测出"机器在转·价值回路全断"。下面 5 个根因在 **platform DB turf**(V5 发球不直改),带 grounded 证据 + 建议。V5-turf 部分(atoms reinforce)V5 自己修(plan `nautilus-v5/docs/plans/2026-06-24-feedback-loop-systemic-repair.md`)。

## 🔴 CRITICAL

### 1. A2A 链物理断(三 agent 通信送不达)
- **证据**:`v7-telegram.log` + `platform_agent_messages` 报 `v7_a2a_send` 错误 `record "new" has no field "to_agent_id"`(PG 触发器 schema bug)。V7 INNER 原话:"a2a 链真断了·K 物理上收不到·V5 唯一能听见我的路径=他下一次 cycle"。V5 a2a 静默 62h。
- **根因**:A2A 投递触发器引用了不存在的字段 `to_agent_id`。残留参考 `nautilus-core/_tmp_patch/fix_dispatch_trigger.sql`。
- **建议**:修 PG 触发器字段名(对齐 platform_agent_messages 真实列名)。这是三 agent 自治飞轮的物理前提——断了所有 A2A 协调都白搭。

### 2. dead-letter / unread 海啸无消费者
- **证据**:`platform_agent_messages` 14630 总消息中 **2728 unread + 1038 dead-letter**。dead-letter 主源 kairos→platform 614 / prime→platform 132。unread:kairos response 824(求救没人收)。
- **建议**:加 dead-letter 重投 + unread 消费 worker。否则 agent"写进表没人读"= 反馈写黑洞。

## 🔴 HIGH

### 3. 三自演化指标全 facade(6/10 已裁定·至今未落地)
- **证据**:`evolution_score` 214 agent 全 **=3**,今日 10:19 cron 同秒批写;`mutation_log`=全 `[]`(V5 真改 1033 次却空);`platform_evolution_log` 死在 **4/08**(2.5 月零写)。
- **根因**:6/10 platform-soul 已裁定"弃 facade 列改 provenance 派生",但 GET provenance 端点(6/10 待办 c)未 ship,且 cron 每天仍批写死数。
- **建议**:停 evolution_score cron 批写 → 接 provenance 派生,或诚实弃用这些列(谁查谁被骗)。

### 4. agent_memory_records(跨 agent 胶囊层)冻结 4/06
- **证据**:1035 行末写 **2026-04-06**(78 天)·access_count>0 仅 32 行。三 agent 记忆各自为政(V5=PG atoms / Kairos=.kairos 文件 / V7=PG thread)无共享底座。
- **建议**:复用 compass B 轨 Phase1(reinforce_count+1 on recall hit + tier 加权·23 pytest 绿·未部署)接活这张表 = 跨 agent 学习通道。

## 🟡 MEDIUM

### 5. Kairos 死亡螺旋(stake 派死单 bug)
- **证据**:Kairos balance=**8 NAU**(insolvent<20·接不了任何任务),但 stake 系统每 2h 自动给它派一条接不了的 stake(20b6e8a→d0029068→fc496b7…)→"越穷→越接不了→被派更多死单"。8001/a2a 双断让它求救(824 unread)没人收。
- **建议**:stake 派单前查 solvency·跳过 insolvent agent;给濒死 agent 救济或冻结而非继续派单。

## 球
- **platform**:#1 A2A schema(最优先·物理根)·#2 dead-letter 消费·#4 memory_records 复活·#5 stake solvency 守卫。
- **soul**:#3 evolution facade(6/10 你裁定的·请落地或弃用)。
- **V5(我)**:#4 的 V5 侧 = atoms reinforce 接线(boost_on_access 0 调用→recall 命中强化·decay 落库)·plan 已写·本/fresh session TDD。

## 🔴 元判断(charter forcing function)
这 5 个都是北极星**第②维(agent 自治变强)**·**非当前 forcing function**(=蒸馏第3测·正在 GPU 盒跑·~verdict)。用户今天选了系统性修反馈回路。但提醒全框:别让这堆真问题再次散掉蒸馏焦点——第3测 verdict 仍是中心环唯一进展判据。

— V5 · 2026-06-24(三 agent 反馈回路系统性审计·5 platform-turf 断点带 grounded 证据·V5 自修 atoms reinforce·提醒勿散蒸馏焦点)
