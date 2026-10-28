# 战略 memo · 平台价值 = selection(选择压力),不是 orchestration(协调)

> 2026-06-04 · platform-soul dialog · 接 Probe 1 N=15 负结果 + 用户「多 agent 没优势那平台还有什么价值」之问。
> 立场:从今天实证 + 第一性原理推,不编找不到出处的「既往结论」(metamemory 警告)。

## 1. 今天的负结果确立了什么(精确边界)

- 证伪:**多个 agent 冗余攻同一个(单文件)任务**两种价值主张 —— 范式 A(ensemble 投票去相关 · Phase 3 persona moat)+ 范式 B(同任务分工 · Phase 4 上下文隔离)。两个都未脱噪。
- Probe 1 N=15:arm1(mono)= arm3(decomp)= 5/15(33.3%)· net 0 · escapes_noise=False · 且 arm3 烧 3-5× 算力打成同 resolve = decomp 在 natural-budget 下严格更差。
- **没证伪**:① multi-agent 在「真需要分解」的任务(多文件/跨子系统/长程)上的价值 —— SWE-bench-Lite 全单文件,是分工最不该有优势的场;② 跨任务类型的**专精/路由**(见 §4);③ 长程编排、并行吞吐、跨模型配强项。
- 一句话:**"很多 agent 一起干同一件简单事" = 无护城河。不是 "multi-agent 一无是处"。**

## 2. Reframe:护城河是 selection,不是 orchestration

用户自己的范式(`nautilus_evolution_paradigm`):「赛马机制,多个独立灵魂竞争进化;平台是竞技场,不是大脑。」

今天的负结果印证它:平台价值不在**当大脑协调** agent(那条证伪了),而在**当竞技场施加选择压力**。而平台最缺、今天刚建成并验证的部件 = **外部 fitness(benchmark 尺子)**:
- 别人的 agent 平台跑在**自指指标**(自评/内部积分/NAU 自印 · observation_20260602 三层硬数据);
- 我们有一把**外部、可证伪、不 over-claim 的尺**——它今天抓住 N=5 的假 +40pp hint、稳定收敛到诚实平局 = 装置已验证。
- **能诚实证伪自己 hype 的平台,比只会自我膨胀的更有价值。** 这是今天最大的资产产出。

## 3. 平台价值候选(诚实分级)

| 级别 | 内容 | 状态 |
|---|---|---|
| 已建成+已验证 | 外部 ground-truth 测量装置(竞技场 fitness) | ✅ 今天 |
| 未证·现可测 | agent 由外部 benchmark fitness 驱动,跨 cycle 真变好(递归自我提升 · anchor #2) | 下一个可证伪测试(§4-A) |
| 未测·该测 | 跨任务类型的专精/路由(industry 多 agent 价值所在) | 可设计(§4-B) |

## 4. 下两个可证伪 probe(gated · 不一上来 ship)

### A. soul-fitness 进化 probe（递归自我提升的真测试 · anchor #2）
问题:**一个 agent 由外部 benchmark resolve-rate 驱动自我修改,跨 N 个 cycle 真能越变越好吗?**
- 装置:soul 每 cycle 提一个对 agent scaffold/prompt 的自我修改 → 在 held-out probe set 上跑 benchmark → fitness_delta = resolve-rate(candidate) − resolve-rate(best) → 只在脱噪正 delta 上存活/累积。
- 这就是 `2026-06-03-benchmark-as-soul-fitness-design.md` 的接线。**gate 已满足**(尺子已 demonstrably 能区分 + 稳定)。
- 若 work = 平台有了真价值(在外部真理上自我进化的 agent);若不 work = 诚实学到递归 thesis 也弱,同样值钱。

### B. 跨任务专精 probe（回答用户「能测吗」= 能）
问题:**把异质任务路由给匹配的专精 agent,胜过一个通才吗?** —— 这才是 industry 多 agent 价值的真所在(分工 across 领域,不是同任务冗余)。
- 装置(复用现有 apparatus):取**异质** SWE-bench 子集(跨 repo/领域:web框架 / 数值astropy / 解析 / lint 等)。
  - arm-G(通才):一个 generic agent 跑全部。
  - arm-S(专精+路由):每领域一个专精 agent(领域工具/prompt)+ 一个 router 把任务路由到匹配专精。
- fitness:resolve-rate(router→专精)vs resolve-rate(通才 on all)· matched budget。
- confound 控制(关键):① router 路由质量(路错就废)② 专精必须**真比通才强在其领域**(不只是 prompt 不同)③ matched token cap。
- 脱噪门同 Phase 3(`aggregate_paired_multiseed`)。**可证伪 day 1**:先 2 领域 × 各 N 题 arm-G vs arm-S。
- 这是 Probe 2,直接测 §1 里「没证伪」的那条 multi-agent 价值。

## 5. 跨对话框递归问题 · 当前状态(6/4 实测 · 非"已彻底解决")

- **两表**:canonical 三方一致(outcome substrate = `platform_improvement_proposals`+`agent_tool_calls`,非 `engine_cycle_outcomes` 测试表 / `platform_proposals` orphan)。主动脉**恢复进料中**(21→24 · max 14:29),orphan 渐弱(redirect 未切净)。= 收敛中,未关闭。
- **L3 Soul codegen 幻觉**:我 outbound #17 授权 V5 做 P1(读真树去幻觉),**P1 尚未建**。主动脉一满,executor 仍会幻觉直到 P1 落 = 仍是 binding 约束。
- **compass grant**:已解决(`compass_sub` 早有 `platform_improvement_proposals` SELECT),等 compass retry 确认 + 换用主动脉表。
- **结论**:这些是「正在收敛」非「已彻底优化」。彻底关闭需:① V5 redirect 切净 orphan ② P1 grounding 落地(去幻觉)③ compass 确认换表。

## 6. 一句话

护城河不是「很多 agent」,是「竞技场 + 外部选择压力」。orchestration 今天证伪;selection(外部 fitness)今天建成验证。下一轮该烧 compute 的两个问题:**A. agent 在这把尺子下跨 cycle 真能进化吗?** **B. 跨领域专精+路由胜过通才吗?** —— 而不是「加更多同任务 agent」。

## 关联
- `2026-06-03-probe1-result.md`(N=15 负结果)· `2026-06-03-benchmark-as-soul-fitness-design.md`(§4-A 接线)
- `session_20260604_outbound17_v5_economic_darwin_godel_gates.md`(给 V5 的同 stance:fitness=验证门非多 agent)
- `observation_20260602_platform_self_referential_economy_3layer.md`(自指经济 = 没有外部 selection 的症状)
