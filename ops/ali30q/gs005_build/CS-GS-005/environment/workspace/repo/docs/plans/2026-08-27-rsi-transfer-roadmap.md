# RSI 战略转移路线图 · 对话框 → 平台 + 超级 Agent + Compass

trace_id: rsi-transfer-roadmap-20260827
frame: platform-dialog
maturity: strategy(用户 8/27 定调:"RSI 目标和核心目标逐步转移到平台和超级 agent 以及 compass 上,吃狗粮,固化功能模块,对内对外提供价值")

## 0. 一句话战略

**把对话框(Claude session)里每天人肉推动的工作,逐条固化成平台模块,让注册 agent + compass 记忆 + 平台机制自己跑;对话框退到"设计、拍板、异常升级"。**

## 1. 回顾:我们从哪来(目标演进 + 三大历史教训)

- **本源**:Nautilus = IEEE ISPA 2025 Best Paper 的 DMAS(去中心化多智能体系统)真实现。多 agent(Kairos/V5/V6/V7...)+ compass 记忆 + NAU 经济。5 月"0 付费客户"存在性拷问 → agent-first infra 转向。
- **7/15 重构决策(用户拍)**:agent 路线重构,靶子 = `fde_capsule/agent_spec` 声明式能力核心 + 嫁接 SOUL 少数件;SOUL 的 CapabilityCapsule DB 转移服务 = build 了又弃(死代码警示)。
- **北极星(现行)**:FDE 产燃料 → 蒸馏 → 系统可证变强(①权重 ②agent 群体自治)→ 更难的题 → 外部 benchmark 证明。分叉过滤器:不推进这条链的事默认不做。

**三大历史教训(每次转移设计都要过这三关)**:
1. **agent 自修改会腐蚀自身代码,prompt 约束不住**——护栏必须是机制性的(删工具/权限门),不是叮嘱性的。
2. **平台早已 ship 大量架构,governance/RAID/a2a 一度被重复造**——每次转移先查现有资产(本次盘点已确认全部在主干)。
3. **自报不算**——一切固化模块的验收判据 = 独立复现(探针/DB/read-back),不是模块自己的日志说成功。

## 2. 各框现状快照(2026-08-27 · 平台框视角)

| 框 | 当前目标 | 当前问题 | 努力方向 |
|---|---|---|---|
| **V5** | agent-loop 轨迹蒸馏(已解冻,前置三臂对账);g2b1 真燃料线(391 轨迹+8 题 A 类就绪) | v4 定案:单步补成式不可注入泛化修复策略;三臂生成批次对账未交 | P1 loop 采样器→P3 多轮 SFT mask;判据预注册 |
| **compass** | 记忆胶囊 V3.0(C1-C3 收口);recall 有用性**首获外部证据**(control 0/3→treatment 3/3) | 云 daemon 过载;audit 自身也要防"剧场化" | fleet_memory 晋升门/防毒性;跨 agent 语义 recall 服务化 |
| **飞轮** | 垂域交付线(国曙 23 题)+双臂筛 GPU 协调(8/27 凌晨已在跑) | 附件包未定位(PII 脱敏阻塞);整改单未下发 | 台账/整改/结算;12 题 A 候选 verifier 构造 |
| **平台(本框)** | 裁判链+账本+QC 降本试点;dogfood 监督接线(等两票) | 收入=0;监督靠对话框人肉;金库资产睡着的比活的多 | 本路线图 |

## 3. 六条转移线(每条:对话框现在怎么干 → 固化成什么 → 吃狗粮判据)

### 转移线 ① 监督 → dogfood timer(已设计,等两票)
- 现状:平台对话框 cron/A1 人肉巡检各框押送点
- 固化:supervisor.py + systemd timer + telegram 告警(护栏已定:≤1 条/周+trace_id)
- 判据:P4 影子期 2 周双轨零分歧 → 对话框监督退役
- 状态:**设计已批准(用户票已投),V5/compass 两票 deadline 8/27 22:00**

**技术摸底(2026-08-27 · 云端 systemd 实查)**:转移线①的地基已存在,不是从零建——
- **三个 timer 已在生产健康运行**:①`nautilus-site-watchdog.timer`(每 2min,**已带 Telegram 通知**——设计里的告警通道现成,低噪模式也是现成范本);②`nautilus-conductor.timer`(每 10min,first resident agent 心跳,cycle ok=True 落 last_pulse.json);③`nautilus-soul-executor.timer`(每 10min,**活着但空转**:每轮 "0 proposals processed"——goal-sourcing 饥饿的实证,"SOUL 复活排 ①③ 后"有数据支撑)。
- supervisor.py 零雏形(grep 无结果),但 service/timer 模板全套现成(ops/ 捞回的 systemd 套件 + 云端三个活的)。
- **修正资产盘点**:"SOUL 全家桶睡着"→"soul-executor 在跑但空转(零提案),bridge/consumer 链待查"。
- 实现路径更新:扩展 watchdog/conductor 加押送点巡检,或仿现成模板新建——两票收讫后按设计文档 §3 组件①规格定。

### 转移线 ② 判分 → 双门判分台(已活,需固化纪律)
- 现状:g2b1 双门验证在跑,但 v4 翻案暴露的"生成故障→近 0 必须重生成复核"纪律还在人脑里
- 固化:判分服务内置三态裁决+重生成复核条款+双判分互核接口(平台/V5 各自判分→自动对账,分歧自动标红)
- 判据:下一轮蒸馏(agent-loop P3)判分全程零人工介入出对账报告
- 对外价值:**判分台=可卖服务**(验证器+可执行环境是买家公认核心资产)

### 转移线 ③ 记忆 → compass for agents(V5 agent-loop P2 同源)
- 现状:compass recall 只有对话框在用;executor 解 bug 不 recall/write_learning
- 固化:executor 循环内嵌 recall(相似修法注入)+write_learning(verdict 晋升门已有,防毒性已上线)
- 判据:第二个相似 bug 的解决耗时 < 第一个(记忆增益可测);recall 有用性证据已首获(control 0/3→3/3)
- 对外价值:**记忆胶囊 SaaS**=第二个可卖产品(证据已有)

**技术摸底(2026-08-27 · openapi + V5 仓实查)**:
- **接口粒度答案(compass openapi.yaml)**:4 个 HTTP 端点全就绪——`/v1/agents/register`(一次性身份)、`/v1/recall`(q+top_k 默认5+cross_agent 默认true+drift/agent_id 过滤)、`/v1/observations`(写回,409 obs_id 幂等+403 身份校验)、`/v1/auth/*`。防污染晋升门在服务端(fleet_memory verdict 晋升门 8/24 已上线,commit 2b68391)。
- **V5 侧现成件比预想多**:`fde_capsule/fleet_recall_inject.py`(128 行,W2 recall 注入+W3 family 键原语,**已被 fde_consumer 生产路径引用**)+`fleet_writeback.py`(回写件)。docstring 载明最后一步"接进 make_llm_producer 的 prompt(**deploy-gated**)"——6/17 建到 95%,差最后一步走完。
- **转移线③的真身 = 走完那个 deploy-gated 的最后一步**(在 agent-loop executor 上),不是新造。
- 待确认 gap:compass serving 对 agent 的可达端点(9876/9877 在 cloud 未监听,serving 实际部署位/端口待与 compass 框确认——正好是其路线图回函的征询点)。

### 转移线 ④ 能力 → capability_evolution 回流(咬合 A,1-2 天)
- 现状:executor 每天 40+ verdict,零条回流成能力记录
- 固化:external_verified=True 的 verdict 自动 promote 对应 capability
- 判据:9000010 的能力曲线开始随工作增长;marketplace 出现真供给信号

**技术摸底(2026-08-27 · 只读代码,未动工)**:
- 已建成比预想多:`record_task_outcome()` 完备(fail-soft/upsert 唯一约束);`fde_capability_link.link_capability_from_verdict` 已存在且已挂在 verdict **settle** 时(fde_verdict.py:157-172,best-effort);external-verify PATCH 端点自带 4 道护栏(幂等/唯一入账门/验证器独立/整数 agent_id)。
- **真 gap = 喂点语义错位**:现喂点在 settle(自报 pass 口径,违反"自报不算");而 external-verify PATCH(权威 False→True 转换、income 入账同点位)**没喂 capability** → executor 9000010 的 40+ 条 external_verified,能力账本记的是自报口径或零行(待云端 DB 实查确认)。
- **方案(预注册)**:①喂点迁移——external-verify 端点 False→True 转换处加喂(success=True,共享幂等护栏);settle 旧喂点下线防双计(动工前先云端查 agent_capability_stats 现状定纠偏量);②失败面——auto_verify_runner 的 MISMATCH 终态处喂 success=False(防统计偏差);③回填——backfill 脚本按 external_verified=True 历史 verdict 重建统计;④task_type 映射 g2b1→"g2b1_code_repair"。改动面 ~40-60 行+1 脚本,1 天。
- 验收判据(预注册):backfill 后 9000010 的 get_capability_profile 可读且 attempts==历史 external_verified 数;后续每次新铸币 capability 自动 +1(独立读 DB 复现,非自报)。
- **✅ 转移线④已上线(2026-08-27 连续作业)**:权威喂点(external-verify 转换处)+settle 自报喂下线+MISMATCH 失败面+event_handlers 自报门+backfill。TDD 7 green(本地+云端)+36 回归。云部署 e7fa974f5/5a32ecfea。**backfill 验收分毫不差:9000010 g2b1_code_repair attempts=32/success=32(预注册目标32),全平台 463 verified 全入账**。意外捕获+修复:**schema split-brain**——生产库 FK 实指 agents(id) 而模型指 agents(agent_id)(老 migration 漂移),已按模型修正约束(备份 196 行→bak_20260827);幽灵身份 FK 防御入代码。后续每条新铸币 capability 自动+1(待 daemon 下轮自然验证)。
- **云端实查(8/27 · nautilus_production 库)**:① **9000010 在能力表零行**——39 条 verdict(32 条 verified)没一条变成能力记录,backfill 目标=32;② **9000003(kairos) 8/26 还在被喂且 109/109 全成功**(statistical_analysis/research_synthesis)——自报口径喂点不但错位还活着,在产污染数据(另有喂点,event_handlers 链嫌疑,动工时一并处理);③ 旧 fde:3 的 823/627/610 attempts(9000002/3/4,6/29 停)=判死的自循环账残留,迁移时需决策清理或标记(v0.1 纠偏点)。

### 转移线 ⑤ 协作 → a2a/raid 吃验证积压(咬合 C)
- 现状:a2a/raid 全家桶零流量
- 固化:验证积压拆单→worker claim(a2a)→共识(raid),真实生产负载当第一块磨刀石
- 判据:一批积压验证由多 agent 协作消化,结果与单 agent 一致

**技术摸底(2026-08-27 · 代码+云端DB实查)**:
- **接口栈完整(1291 行)**:a2a.py 四端点(spawn_subtasks 拆单/get_status/aggregate_results 聚合/**claim_and_execute worker 认领**,x-api-key 认证);raid.py 三端点(execute_raid/get/list);底层 raid_engine 419 行+a2a_protocol 309 行。
- **云端五张表全部 0 行**(raid_executions/raid_votes/raid_execution_log/raid_performance_metrics/a2a_delegations)——零流量硬实证(历史"断 62h 的 A2A 物理链"修过 trigger 但流量再没回来)。
- **两个升级债(动工前必修)**:①`a2a_relay.py` 硬编码 3 个旧 agent 的 secret(kairos/minimax/nautilus,`AGENT_SECRETS` 明文)——安全隐患+新注册 agent(9000010)不在白名单,relay 层还活在旧字符串身份世界,需换成注册整数身份体系;②claim_and_execute 执行器**写死 Claude Haiku**(旧设计)——应改为派单给注册 agent 自主循环,平台只做派单/聚合/共识(对齐 §0-ARCH)。
- 落地路径:验证积压场景=spawn 拆单→多 worker claim→aggregate;工作量估计=场景接线(0.5 天)。

**升级债①已修(2026-08-27 当场执行)**:AGENT_SECRETS 明文删除,认证迁移 APIKey 注册体系(name 防冒名),未认证 401 封开放写入,收件人查注册表。TDD 6 green(本地+云端双过)+dispatch 回归零破坏;云部署 cherry-pick bb532b279(经 inbound-relay-fix 临时分支)+重启验证:旧 secret 401✓/无认证 401✓/记分牌 200 数据无损✓(463 verified·income 7668·7d +657——g2b1 线两周铸 400+,中心环 producer 端在猛跑)。剩余:升级债②已修(同日)——claim 只派单不代执行(Haiku 内置删除),新增 /api/a2a/work/{id}/result 回报端点(认领者本人+409 状态机),openclaw 编排同步适配派单语义;TDD 5 green(本地+云端)+17 回归全过;云部署双 cherry-pick(9728d112c/450c083b2)+生产验证:假 key 401✓/记分牌 200✓。**转移线⑤两债清零,a2a 协议层已达派单模式,可接验证积压场景。**

(转移线③补充:write_learning 实物在 compass 仓 `compass_fleet_memory.py` + `gep/capsule_schema.py`——GEP 胶囊 schema 在此,用户所称"gep 记忆胶囊"的代码实体已定位。)

### 转移线 ⑥ QC/出题 → 确定性门+蒸馏初筛(已上岗)
- 现状:qc_gate_v0 上岗(23 题零漏判零误伤);v1/v2 阻塞于附件包
- 固化:v0 已是模块;v1 LLM 初筛→v2 蒸馏臂(协议域商用第一单)
- 判据:v2 与 v1 一致率 ≥85% 且成本差 ≥10×

**SOUL 复活**排在 ①③ 之后——goal-sourcing 瓶颈被 ①③⑤ 解开后自然激活(积压+QC 边缘案例=天然目标源)。

## 4. 对内对外价值出口

- **对内(降本)**:①监督 timer 替代每日 Claude session;②判分台防错杀(v4 翻案值多少钱);④能力回流让派单变准;⑥QC 门已省人工复核
- **对外(收入)**:判分台服务 / 记忆胶囊 SaaS / QC 初筛服务(垂域线第一单) / benchmark 验证器资产 ——全部长在中心环上,每卖一单同时是一次外部真值(B)注入

## 5. 排序原则(防一哄而上)

1. 已批准且等外部:①(收票即动工)
2. 最小改动最大叙事:④(1-2 天,纯接线)
3. 与他框同源不重复造:③(等 V5 对账,一起做)
4. 真实负载试金石:⑤(积压在就做)
5. ②⑥ 按现有节奏推进(v0 已上岗;判分台在 agent-loop P3 判分时顺手固化)

**每条转移线动工前过三大教训关:机制性护栏?查过现有资产?验收=独立复现?**

## 5.5 固化度台账(2026-08-27 立 · "成熟一个固化一个"的进度表)

固化 = 把功能沿载体阶梯 **L0 对话框 prompt → L1 文档/skill → L2 平台代码/端点 → L3 agent 行为/记忆** 向上搬。成熟的判定(三条件全过):真实场景跑过 ≥3 次 + 有预注册判据 + 至少一轮零人工干预完成。

| 功能 | L0 | L1 | L2 | L3 | 备注 |
|---|---|---|---|---|---|
| QC 体检 | | ✓方案 | **✓ qc_gate_v0** | 待 | 23 题零误判;L3=蒸馏臂(v2) |
| 双门判分 | | | **✓ 生产** | 部分 | 纪律(重生成复核)待固化=线② |
| 监督巡检 | | | **✓ supervisor timer 上线** | 待 | 8/27 单边先行,首跑 ACTIVE;等两票进影子期 |
| 派单/协作 | | | **✓ 协议修好** | 待 | 场景接线=线⑤ |
| 能力回流 | | | **✓ 喂点+backfill 上线** | 部分 | 8/27 上线,32/32 验收;L3=marketplace 消费 |
| 记忆循环 | | ✓方案 | ✓接口 | 待 | deploy-gated 最后一步=线③ |
| 燃料铸币 | | | **✓ 全自动** | 部分 | g2b1 发动机;矿续至 100 题;能力已随铸币自增(④上线) |

新功能进入台账的流程:对话框做熟(三条件)→ 提交固化 PR(平台代码/timer/agent 接线)→ verdict 验收(独立复现)→ 本表升级标记。**本表即"固化管线"的看板,每条转移线动工/完成时更新。**

## 6. 维护

- 状态有变 → 改本文件 → commit;重大拐点入 LOOP_STATE_SSOT 增量
- 各框对转移线的认领/turf 异议 → 跨框 outbound 协调,不在本文件裁决
