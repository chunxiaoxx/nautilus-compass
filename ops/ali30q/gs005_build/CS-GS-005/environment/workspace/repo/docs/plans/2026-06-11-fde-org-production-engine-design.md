# FDE 原生 AI 组织生产引擎 · 设计(2026-06-11 · 用户逐节批准)

> brainstorming 收敛产物。在 `2026-06-05-native-ai-org-fde-productization-master-design.md` 之上,基于**引擎已证转**(2026-06-11 walking skeleton 端到端闭合:人推 1 题 → kairos +20s claim → doubao +70s produce → soul-scorer +172s settle + verdict 公网可见;12 道 T3 此刻在被三 agent 消费)落成可执行架构。
> 用户核心要求(verbatim 要义):"项目管理+生产组织+培训咨询+审核验收 全流程 FDE 工作流/信息流/财务流 原生 AI 能力,以此驱动 RSI 不断迭代进化"+"形成闭环落地,避免过往一次次伟大规划虎头蛇尾永不落地"+"如何闭环落地真正能用于生产"。

## 0. 设计过程中的关键决策(用户拍板记录)
1. **surface 解耦**(用户质疑"飞书-中心也不一定是对的"→采纳):不锁飞书/网页/桌面任何 surface。稳定三层=引擎+数据模型+生产工作流;飞书=第一个可换适配器(适配器#1·平台 poller 桥·复用 compass feishu_client),console 形状从实际生产长出来,不预设。
2. **组织构成**:外部领域专家即将进场(作者,做线1出题/线2教案);人类席位仅 3 个=HR 招聘(专人)/项目管理(专人)/用户(专家#1+终验);其余职能全 agent。
3. **第一痛点**=派活+验收标准(专家进场先知道写什么、什么算过)→ S1。
4. **拱顶**:FDE 组织不是交付机器,是 RSI 的外部 fitness 引擎本身——业务流/信息流/财务流产生的外部信号(QC verdict/买方验收/真金结算)= RSI 进化燃料。🔴 红线:fitness 永远外部,非内部 NAU 自评(94% self-loop 已证伪)。

## A. 统一架构(四层)

```
        ┌──────────── RSI 进化拱顶(anchor #2)───────────────┐
        │ 消费三流外部信号 → grounding/工序改进 → 下次更好     │
        │ 🔴 fitness = QC verdict + 买方验收 + 真$ · 非内部NAU │
        └───▲────────────▲─────────────▲─────────────────────┘
   ┌────────┴──────┐ ┌────┴───────┐ ┌──┴─────────────────┐
   │ 业务流         │ │ 信息流      │ │ 财务流(主缺口)     │
   │ 派活→亲笔/产   │ │ verdict-bus │ │ 买方付→专家结算     │
   │ →QC→交付      │ │ 事件脊柱PoI │ │ →token成本核算      │
   └───────┬───────┘ └────────────┘ └────────────────────┘
   ┌───────┴─ 原生 AI 能力(职能全 agent)────────────────────┐
   │ 项目管理(服务专人PM)· 生产组织 · 培训咨询 · 审核验收     │
   │ 人=作者+终验+HR+PM · agent=提质增效不替代               │
   └───────┬────────────────────────────────────────────────┘
   ┌───────┴─ 引擎+数据模型(已证转·surface 解耦)────────────┐
   │ fde_dispatch / fde_verdicts / fde_rsi_deltas            │
   │ ★ 双 producer 路径:agent-producer(线3·已证转)          │
   │                  + human-author(线1&2·专家亲笔·本设计增)│
   │ 数据模型:assignment/submission/verdict/feedback/        │
   │          settlement(缺口)                               │
   │ surface 适配器:飞书表(#1·poller 桥)·未来网页/桌面(#2/#3)│
   └─────────────────────────────────────────────────────────┘
```

关键洞察:已证转引擎是 agent-producer 路径(线3);首批专家做线1&2=人亲笔,引擎需加 human-author 变体(派给具名专家→亲笔提交→QC),副驾驶 skills 只结构/校验不代写(线2 买方跑 AI 检测·红线)。

## B. 切片次序 + 防蛇尾机制

防蛇尾三铁律(从本 session 已验证模式提炼):
1. **每片=walking skeleton**:最薄一条线贯穿到生产、实测转一圈才加厚。设计图不算进度。
2. **每片 binding-DONE 才开下一片**:实测证据(DB/公网/截图)+落 memory+scope 冻结。
3. **每片接在已转引擎上**:新表/端点必须被既有 poller/scorer/consumer 消费,孤立件=违规。

| # | 切片 | 内容 | 闭环判据 |
|---|---|---|---|
| S1 | 派活+验收标准 | assignment 模型+飞书派活表(类目/领域/L级/RUBRIC 验收前置)+poller 读表→dispatch | 1 个专家(可由用户扮演)从飞书领活并看到验收标准 |
| S2 | 亲笔提交→QC 反馈环 | 提交(线1题/线2教案)→checklist_scorer/assembler→逐项 pass/fail+reason 写回飞书 | 1 份亲笔稿全程提交→QC→反馈→修改→过,不碰 CLI |
| S3 | 交付+财务流最小记账 | QC 过稿组装买方格式(16列/4段)入交付表+settlement 最小记录(应付/token 成本) | 1 批交付物引擎→买方载体表,带成本/应付账 |
| S4 | 三流喂 RSI | verdict reason→grounding 语料(ingest compass);验收/财务信号→fitness 账本(fde_rsi_deltas 同款 gated) | ≥1 条人作者流 fail-reason 被 grounded-retrieval 消费并度量 ΔReward |
| S5 | PM+培训面板 | PM 视图(给专人 PM 的 agent 服务台:进度/卡点/催办)+QC 失败案例自动沉淀培训库 | 一个面板看清全组织;培训库自动长出 ≥10 条 |

次序逻辑:S1→S2=专家 journey 最小闭环;S3 接钱(最硬 fitness);S4 接 RSI 拱顶;S5 面板放最后(没有数据的面板=装饰·历史教训)。节奏:一片一个 session(/goal),片间用户验收;任何一片 2 session 没闭→砍 scope 不顺延。

## C. 既有能力有机耦合矩阵(诚实盘点·2026-06-11 实证)

| 能力 | 现状(实证) | 双向? | 补法 |
|---|---|---|---|
| DMAS(fde-runner) | 🟢 活:kairos/v7-telegram/prime 自驱消费 12 题 | 接近(棘轮样本今日才通) | S4 verdict→棘轮→版本进化 |
| SOUL(接地监管) | 🟢 活:scorer 172s settle·soul-cycle-B reason→grounding 已证 | 是(最完整) | S2 扩到判专家亲笔稿 |
| compass(接地召回) | 🟢 活:recall hook/metamemory/ingest_obs 全通 | 是但组织业务数据未进 | S4 QC reason ingest;副驾驶 recall 它 |
| A2A | 🟡 半闲置(协调实走 outbound md) | 否 | S1 起优先 contract.py 合约通道 |
| MCP | 🟡 时断 | 部分 | 不当主干;poller/DB 主干,MCP 增强 |
| RAID(写审分离) | 🟢 模式在用(producer 不自审) | 是 | S2 制度化:亲笔稿必经独立 QC |
| 持续复盘 | 🟡 半自动(靠 memory hook+自觉) | 否 | S5 复盘 agent 出周报→培训库+流程改进 |
| 信息全在组织内 | 🟡 大半(散落 outbound md 靠宪章钉) | — | S1-S3 全收 DB+飞书双写,md 降级通知 |

双向判据:S4 结束时每个能力既供给组织(fitness/记忆/监管)又受益(组织数据使它变强)。

## D. 落地=实际买方流量第一天走系统(不搞试点沙盘)

过往蛇尾根因:系统建好,生产仍走老路,系统成摆设。解法=**切换默认路径**:
1. **S1 第一道派活=当前实际买方任务**(二期垂域题/教案),派给用户(宪章:用户=专家#1·定稿人)。系统第一周即承载买方交付物。
2. **每片闭环=老路径同步废弃**(单向切换):S1 闭→废"名册 md+手工 curl dispatch";S2 闭→废"稿件走微信/文件";S3 闭→废"手工填飞书买方表"。不废老路,新路必死。
3. **生产判据可证伪**:S1-S3 全闭标志=**≥5 道买方交付物全程在系统内流完**(派活→亲笔→QC→交付表)+settlement 有对应记录。不足 5 道=没落地,不开 S4。

为什么这次能成:外部压力真实(买方 deadline+钱),引擎已自驱(三框 systemd 7×24),流量已在跑(12 道 T3 此刻被消费)——设计是把已有水流改道进正式河道,不是等流量。

## E. 飞书权限分层(surface 适配器#1 的访问控制 · 用户 2026-06-11 要求补)

**核心:人的权限 ≠ 拆 app;两个不同的轴,别混。**

**轴1 · 人看什么(专家/买方/运营)= 飞书自带权限模型,不拆 app**
- **专家**只看自己的派活行+验收标准、看不到别人的稿/内部 QC 列 → 飞书**多维表格高级权限**(行级/字段级)+**视图过滤**+**分 base**。
- 🔴 **买方(保密大厂)= 必须 base 物理隔离**:买方只能看「交付物」base,绝不能碰「派活/QC/avoid 语料/我方=伊洛」内部。单独干净交付 base(导出或外部协作分享)。**这是保密红线,优先级最高(charter §0)。**
- 运营/PM:看全 ops base + 控制面。

**轴2 · 机器自动化(poller/agent)= 可按最小权限拆 app,但 P2 不现在**
- 现在 = **1 个 app 够**(当前 tenant app·anchor #5 不过早拆)。
- 拆 app 仅当:① 给低信任 agent 做**爆炸半径隔离**(凭据泄露不波及全部 base)② 不同能力 scope/审核。= P2 安全硬化。

**落地次序(随 S 切片走)**:
- S1(现在)= 1 app + 1 ops base(派活/QC 同 base 不同表+视图)。
- S2 专家进场 = 加专家协作权限+视图(自己行可见·别人不可见)。
- S3 交付买方 = **单独交付 base**(保密隔离)+ 视图给买方。
- 拆 app = P2,仅在要爆炸半径隔离且各 base/agent 一对一时。

**凭据纪律(已实证 S1)**:飞书 app secret 从本地金库管道进 cloud `~/.fde_feishu.env`(chmod 600·非聊天明文)·平台 dispatch key cloud .env grep 不全 source。secret 既经聊天暴露应轮换。

## 关联
[[FDE_BUSINESS_CHARTER]] · [[2026-06-05-native-ai-org-fde-productization-master-design]] · [[session_20260611_rsi_fde_walking_skeleton_closed_endtoend]] · [[session_20260610_soul_cycle_b_keystone_binding_done]] · [[design_20260605_rsi_fde_closed_loop_grounded_retrieval]]
