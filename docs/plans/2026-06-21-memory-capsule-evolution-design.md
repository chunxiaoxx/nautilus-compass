# 记忆胶囊进化设计初稿(GEP-inspired · 数据自治)· 2026-06-21

> 来源:三并行 agent 调研(evomap GEP 深读 / compass 现状对照 / soul+平台耦合点)。**设计初稿·非实施 plan**。
> 一句话:记忆胶囊"发扬光大"**不需要从零造 GEP**,而是把我们已有的能力打通 + 借鉴 evomap 三个具体件,且接线点全在 compass W1/W2 客户端那一跳——平台/soul 几乎不用改。

## 0. 今天状态(基线)
- 记忆胶囊 = compass cross-agent 集体学习:W1 写经验 → W2 召回 → 服务 RSI。
- 今天(6/21)已:W2 召回升级成 bge-m3 语义(从关键词)+ 实测接进刚闭合的 SWE 飞轮(真实 requests-2148 learning·ranker=bge-m3)。
- 第三方 evomap.ai 做同一愿景("一个学会·百万继承"),更成熟,**开源了 GEP 引擎**(evolver)。

## 0b. 需求方向(2026-06-21 brainstorming 探清 · 3 个边界已定)

- 🔴 **reframe(用户纠正·改变 framing)**:记忆胶囊不是 compass 的一个功能,而要**深度耦合进平台核心架构**,由**平台运行时的 soul 服务 + 各自治 agent 自动运转** —— 运行 agent 解题后自动写经验、claim 前自动继承、soul verdict 自动当质量门晋升/淘汰胶囊。**不是靠开发对话框手动协调**(今天发的 outbound 是开发期权宜·终态是运行时自治)。= anchor#1 平台 agent-first 自治生态的落地。
- **第一步重心 = 两条并行**(用户定):① 内部自治(P0 防退化 + 运行时 agent 自治写/读循环 + soul 自动质量门)② 对外服务(OKF/GEP 对齐 + A2A+MCP)。
- **对外边界 = 先平台内 · 架构预留公网**(用户定):"对外" 先指 nautilus 平台内各自治 agent(V5/kairos/未来)互用胶囊 MCP;用 OKF/A2A 标准**预留**公网开放能力,但**不现向第三方开**(数据自治)。
- **目标形态 = A2A+MCP 融合服务**:MCP(工具发现层·agent 发现"记忆胶囊"服务)+ A2A(agent 间·发布/继承/report 胶囊),compass serving 担内部 Hub(不接 evomap 外网)。
- ⚠️ **战线提示**:两条并行雄心大,R3 下深度打折 → 今天只探清需求 + 记方向,**完整设计细化 + writing-plans + 分阶段实施留下个 fresh session**。

## 0c. anchor#5 复用盘点(别从零造 · 2026-06-21)

- 🔴 **平台已有(烂尾)A2A+MCP 服务端**(用户提示·实测定位):git worktree `agent-a2152bb850d8d40bc`(**未合主干 = 烂尾**·最后活动 2026-05-03 ~7 周前)。
  - 代码 ~1021 行:`phase3/backend/api/a2a.py`(227)+ `a2a_relay.py`(145)+ `services/a2a_protocol.py`(309)+ `nautilus_agent/connectors/mcp_connector.py`(340)。
  - 文档:`docs/a2a-mcp-architecture-analysis.md`(A2A=协调层:能力广告/任务分解/状态同步/结果聚合;MCP=上下文层:工具定义/发现/注入;production 架构图 Control Plane + A2A Relay;基于 Nautilus↔Kairos 真实交互的运营洞察)+ A2A_PROTOCOL/A2A_VS_MCP 等多份。
  - → **对外 A2A+MCP 不从零造**。下个 session 设计先评估:① 这资产能否接续/复用(代码 7 周新鲜度)② 烂尾根因(优先级转 FDE/RSI?技术债?未接通?)是否可解 ③ 与 compass serving 现有 A2A(`/a2a/messages`+agent.json·**LIVE**)的关系 —— 很可能**互补**:平台的是 agent 协调层(任务分发),compass 的是记忆胶囊层。两层叠加正好是目标"A2A+MCP 融合"。
- **soul auto-mint 飞轮**(2026-06-21 入站):soul 正建 auto-mint timer(自动 mint→produce→verify→settle→W1·**无对话框介入**)= 用户 reframe"运行时自治"的燃料侧落地。→ 记忆胶囊 P0-P3 应同样设计成**运行时 agent 自动触发**(解题后自动写/claim 前自动读/soul verdict 自动质量门),而非脚本/对话框手动。

## 1. 调研结论:借什么 / 不借什么

**借(evomap GEP 三个最值钱件)**:
1. **胶囊结构化边界字段** — `triggers`(何时召回)+ `environment fingerprint`(在什么环境验证过)+ `confidence` + `blast_radius`。不把经验塞自由文本,结构化"有效边界"。
2. **report 回流闭环** — agent B 用了胶囊解题后,把成功/失败结果回写该胶囊 → 喂质量分 → 自然选择。这是从"共享记忆"升级"自我提升"的关键一环。
3. **使用即续命的可逆衰减** — active→stale(170d 不活跃)→archived(270d),但被召回即复活、永不物理删。好经验自然浮上来。

**不借(数据自治 / 守护栏)**:
- ❌ 不接 EvoMap Hub / 公共 marketplace 网络 — 我们 A2A 只在 nautilus 内部跑,Hub 角色 compass 自己担,不向外联网。
- ❌ 不要 GDI 的 social signals(20% 点赞维度)— 我们用**确定性 verifier reward** 替代(比点赞硬)。质量分 = reward + usage + freshness 三维。
- ❌ 不要 evolver 的 self-modifying-code 引擎(mutate/solidify 自动改源码)— 与 R1/R4 护栏冲突。只借数据模型+生命周期,不借自动代码变异。

## 1b. OKF(Google 开放知识格式)= 我们的「格式层」标准(2026-06-21 补)

**OKF v0.1**(Google Cloud 2026-06-12 发布·`github.com/GoogleCloudPlatform/knowledge-catalog/okf`):知识 = 一目录 `.md` + YAML frontmatter;唯一必需字段 `type`(可选 title/description/resource/tags/timestamp);markdown 链接 `[..](/path.md)` 构成有向知识图谱 + "cited by" 反链;**厂商中立·无 schema registry·无中央权威**("能 cat 就能读·能 git clone 就能 ship");Knowledge Bundle = 分发单元,Concept = 单个 md 文档。

**🎯 关键:我们的 compass memory 本来就几乎是 OKF** — `.md` + YAML frontmatter(`name`/`description`/`metadata.type`)+ `[[name]]` 交叉链接 + `MEMORY.md` 索引 + daemon 算 link graph。**对齐成本极低**。

**三层架构定位(OKF / GEP / compass 互补不冲突)**:
| 层 | 是什么 | 我们怎么用 |
|---|---|---|
| **格式层 = OKF** | 知识怎么**存/交换**(静态·互操作·厂商中立) | **采用 OKF 作对外格式标准** → 我们的记忆 bundle 能被任何 OKF agent/工具读,也能继承别人的 OKF bundle = 发扬光大的开放接口(比 EvoMap 私有 Hub 更开放·更合数据自治) |
| **进化层 = GEP(借鉴)** | 知识怎么**进化**(动态·质量·生命周期) | 借 3 件(结构化边界/report 回流/可逆衰减)·不接其网络 |
| **实现层 = compass** | 存储 + 语义召回 + 质量门 + 对外 MCP | 已 LIVE·把上两层叠上去 |

→ **战略正路**:compass 实现 + 对齐 OKF 格式(对外互操作)+ 借鉴 GEP 进化机制。三者各司其职。OKF 让我们的记忆胶囊「对外发扬光大」有了厂商中立的标准接口,GEP 让它「对内自我提升」,compass 是落地。

## 2. 关键发现(现状盘点)

**🔴 系统性根因:能力分两条路,未打通。**
- **路 A · 对外 serving(飞轮真用)**:`compass_fleet_memory` → serving `/v1/observations`+`/v1/recall`(sqlite + bge-m3 cosine)。**无质量分/tier/forget/失败边界**。
- **路 B · 本地 daemon+MCP(.md 记忆)**:PoI(`proof/poi_calculator.py`)+ tier 升降(`proof/tier_promotion.py`)+ forget/decay + governance **全都有**,但只作用于 `.md` 文件,**不碰飞轮的 sqlite observations**。
- → 落 GEP 优先**不是从零造**,是把路 B 已造好的 tier/forget/impact **接到路 A 的 serving 数据流**。

**✅ 质量门已隐式生效**:W1 `write_learning` 已经只在 verify 通过(reward=1.0·settle 后)触发(V5 daemon `[fleet-wb]` 实证)。只是写的是**裸 learning 行**(无质量等级、无失败边界、无淘汰)。

**3 大缺口(按 RSI 复利价值排序)**:
1. **validate + revoke 缺失 → 错误经验会永久复利成毒(最高危)**。无校验写入、无单条撤销。RSI 是放大器,放大错误同样高效 → "集体学习"可能变"集体退化"。
2. **质量分没接进 serving recall** → 排序纯 cosine,劣质胶囊与优质等权。PoI/impact_score 已造好(路 B),只差接到 serving 排序。
3. **胶囊结构太薄**(只一段文本,无"何时适用/失败边界")→ 召回了也指导不精准。

## 3. 有机耦合架构(各方角色)

```
各 agent(V5/kairos)  ──W1 写胶囊(learning + 结构化边界 + verdict 元数据)──┐
       ▲                                                                    ▼
       │ W2 召回(质量过滤 + 语义 + 失败边界匹配)              compass 记忆层(胶囊存储)
       │                                                       · bge-m3 语义召回(已上线)
       │                                                       · 质量排序(接 PoI·待)
       └────────────────────────────────────────────────────  · 生命周期 promote/decay/revoke(接路B·待)
                                                                         ▲
soul:verdict(reward/overall_pass/bucket)= 胶囊的 validate/promote 门 ───┘(已隐式生效·只差带元数据)
平台:dispatch/verdict-bus = 信号源(不用改)
对外 MCP:compass serving 已是雏形(compass.nautilus.social + A2A)= 发扬光大的载体
```

**核心洞察:soul 是天然耦合点** — 它已经在给每道题打确定性质量分(`fde_bench_runner.fast1_verdict`/`swe_verdict`·`fde_scorer_poll.build_verdict_body`·`fde_triage.classify_distillation_fuel` 的 bucket),这正好当胶囊的"质量门"。**质量进化逻辑全部寄生在 compass W1/W2 客户端那一跳,平台/soul 不用改。**

## 4. 如何服务 RSI + FDE 核心
- **RSI**:质量进化(好胶囊晋升 / 错胶囊淘汰 / 用完回写)= 从"集体学习"升级"集体**进化**",并堵住缺口①的"集体退化"风险。这是 RSI 从"积累"变"自我提升"的实质。
- **FDE**:解过的 FDE 题 learning 胶囊化 → 下个专家/agent 继承(含"何时别用"的失败边界)= 提质增效;胶囊质量分也是交付质量的内部信号。

## 5. 发扬光大 · 分阶段路线

| 阶段 | 内容 | 借鉴/缺口 | turf |
|---|---|---|---|
| **P0 · 防退化(最高危)** | ① W1 写回带 verdict 元数据(score/bucket/source)② 质量分接进 serving recall 排序 ③ 单条 revoke API(错胶囊标废停召回)| 补缺口①② | compass(W1/W2 客户端 + serving) |
| **P1 · 精度** | 胶囊结构化字段:triggers / env fingerprint / confidence / **失败边界**(when_not_to_use)| 借鉴1·补缺口③ | compass + V5(写端配合) |
| **P2 · 自然选择** | report 回流闭环:B 用完把成功/失败回写胶囊 → 喂质量分 | 借鉴2 | compass + V5 |
| **P3 · 进化/衰减** | 打通路 B 的 tier/forget/PoI 到 serving observations(复用 `poi_calculator`/`tier_promotion`)+ 可逆时间衰减 | 借鉴3·打通两条路 | compass |
| **对外 MCP** | 内部 A2A + 生命周期成熟后,再评估对外开放(数据自治前提·内部先跑通) | — | compass + 用户决策 |

## 5b. 协作分工 + 推进序(谁做 · 能借 soul/agent 吗 = 能且必须)

| 阶段 | compass(实现层·主力) | agent/V5(写端) | soul(质量信号) | 用户 |
|---|---|---|---|---|
| **P0 防退化** | serving:质量分进 recall 排序 + 单条 revoke API | W1 写回**带 verdict 元数据**(reward/bucket/score/source) | 提供 verdict(**已产·只需被带上**) | — |
| **P1 精度** | serving schema 支持结构化字段 + recall 返回 | **产结构化经验**(triggers/env/失败边界·agent 最懂解题边界) | — | — |
| **P2 自然选择** | serving 加 report 端点 + 质量分更新 | **用完回写 report**(B 解题 reward 挂回胶囊) | — | — |
| **P3 进化** | 把路 B 的 PoI/tier/forget 接到 serving observations(复用 `poi_calculator`/`tier_promotion`) | — | — | — |
| **对外 MCP** | serving + OKF 格式导出 + 内部 A2A | — | — | 对外开放**时机决策** |

**关键:soul 和 agent 不只能借,是必须** —— ① soul 的 verdict/reward/bucket 信号**已成体系**(`fde_bench_runner`/`fde_scorer_poll`/`fde_triage`),P0 直接用,soul 几乎不用改;② V5 是写端,P0/P1/P2 都要它配合(带元数据 / 产结构化 / 回写 report);③ compass 是实现层主力(召回/排序/生命周期/对外)。
**推进纪律**:每阶段先 writing-plans + 跨框 outbound 协调(V5 写端 + soul 信号契约)+ TDD + 实测。**P0 先做(最高危·错经验复利成毒)**。

## 6. 最小改动接线点(soul agent 实证·2-3 处·都在 compass 客户端)
1. **`compass_fleet_memory.py:write_learning`** — W1 写回附 verdict 元数据(reward/score/bucket/source)作质量等级标签。已只在 reward=1.0 触发,加标签即可。**= 晋升门。**
2. **`compass_fleet_memory.py:compass_recall_pits`** — recall 加质量过滤(只召回高质胶囊)+ **family 键统一为 `bench_family`**(顺带修今天发现的不一致)。**= 喂高质胶囊 + 键对齐。**
3. (可选)serving 侧同 `bench_family` 下新胶囊晋升时对旧低分衰减/淘汰。

**family 键不一致根因(已定位)**:`task_family`(claim 池键·恒 `distillation_fuel`)vs `bench_family`(复利键·真实族名 `requests`/`kernelbench-stump`)被混用在同一形参。**canonical 复利键 = `bench_family`**,W1/W2 都只用它。修复点 = `compass_fleet_memory` 或 V5 的 `build_fuel_desc`。

## 7. 红线 / 不做
- 不接 evomap 外网、不向公共 marketplace 广播我们的胶囊(数据自治)。
- 不引入 self-modifying-code 引擎。
- 不要 social-signals 质量维度(用 verifier 替代)。
- 晋升阈值 measurement-first 自定(按我们 verifier reward 分布),不照搬 GDI≥25 等他们 marketplace 调出来的数。
- 这是**设计初稿**,实施前每阶段单独 writing-plans + TDD + 跨框协调(V5 写端 / soul 信号)。

## 关联
- memory `canonical_memory_capsule_equals_compass_crossagent_mcp_collective_learning`(定义)· `session_20260620_compass_daemon_score_deployed_serving_boxdrift_blocked`(今天 W1/W2 接通实证)
- evomap 开源:`github.com/EvoMap/evolver`(GEP 引擎)· `github.com/EvoMap/awesome-agent-evolution`
