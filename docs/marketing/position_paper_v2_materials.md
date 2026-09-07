# Position Paper v2 · 素材池(2026-09-07 理论日产出 · 9/10 v1 发布后迭代用)

> 来源:七算子产品审计 + 判据库理论框架 + Aegis Compass 竞品过秤(框架首次实战)三层。
> v1(20260904_architecture_position_paper.md)发布期内不动;本池只增不删,写 v2 时逐项取用。
> 纪律:每条标注来源与置信(measured=过秤实证 / inferred=推理 / heard=未验证)。

## 1. 核心论点升级候选(v1「写入时下注」→ v2)

**「写地址空间决定遗忘命运」**(inferred,判据库框架):灾难性遗忘从算法 bug 重分类为
**介质选型的架构级必然**——全局共享参数空间(SSI)写新必扰旧;稀疏可寻址空间(代码/条目,
Waddle/nautilus-compass)物理绕开干扰,代价是读变难;ICL 不写,零遗忘与关机即丢同源。
→ 可画:稀疏性 ←→ 干扰 的单轴四系统分布图。

## 2. 方程补预算项(框架修正①)

`Δ状态 = f(新经验, 旧状态, 门控 g) | 预算`——四家最硬差异之一是**更新成本结构**:
compass 写入零 LLM(成本曲线反转)是预算轴位置;ICL 不写=免费选项。有限容量系统面对
无限世界 + **有限更新预算**。(measured:write-path economics 对照卡数字 $0 vs ~$0.002/条)

## 3. 七算子坐标系 + 「选」算子二分(框架修正③,竞品反哺)

七原子算子:写/读/选(门控)/合并/忘/组合/评估。「选」必须拆两半:
- **select-action(动作门)**:输入=待执行动作,输出=allow/deny。失效模式=危险动作执行。
- **select-memory(记忆门)**:输入=候选记忆,输出=trust/reject/promote。失效模式=知识污染入库。

Aegis Compass 动作门 ● 记忆门 ○(policy 挡得住写 .env,挡不住错误记忆入库);
nautilus-compass 相反(记忆门 ●:判分卫生学/QC 门/drift;动作门弱)。**没人两门都有**。
→ v2 对比矩阵主轴。

## 4. MMU 类比三件套(9/15 修复的架构叙事)

| 修复 | MMU 对应 | 说明 |
|---|---|---|
| fact_status: measured/inferred/heard | dirty bit | 可信度标记先行,评估前置防污染 |
| 写入查重触发合并(cosine>0.9) | 去重页 | 单 SSOT 机制化 |
| 召回沿链一跳 | prefetch | 组合的最小可用版(脚手架,非组合本身) |

MMU 本职=权限(drift)+换页(忘/tier 衰减)+翻译(读);类比是结构性的非修辞。

## 5. 定位句(v2 收口句,Aegis 修正版)

> **Aegis arbitrates what agents *do*; nautilus-compass arbitrates what agents *remember*.**

介质(内存)是红海:mem0/Zep/MemOS/Aegis 全在造。仲裁器两条总线:动作总线已有产品化
(Aegis $20/mo);**记忆总线仍无人产品化**——判分卫生学(论文级)+QC 门+fact_status
是我们已有的三个记忆仲裁实例。(measured:Aegis 定价页;inferred:记忆总线空位)

## 6. 竞品矩阵行(v2 新增)

| 系统 | 介质 | 动作门 | 记忆门 | 成绩公开 | 本地/开源 |
|---|---|---|---|---|---|
| mem0/Zep/MemOS | ● | ○ | ◐ | 各自自报 | 部分 |
| Aegis Compass | ◐(符号图+episodic) | ●(policy/审计/合规) | ○ | 零 | 企业自托管 |
| nautilus-compass | ●(零 LLM 写/分型路由) | ◐(drift) | ● | 0.890 vs mem0 全证据链 | ●本地黑盒+Modified MIT |

## 7. 组合算子论纲(我们最弱项的机理)

组合是七算子中**唯一必须在读取时、有引擎在场**执行的算子(其余可离线/写入时)——
运行时计算非存储操作,故不会自然长在存储系统里。Waddle 做出组合因其架构定义含
「LLM 当引擎、代码当介质」。Aegis 的符号图=组合的**实体底座**(call-chain 即图上组合)。
→ roadmap 候选:9/15 沿链一跳(记忆内组合)之后,代码实体组合(对 coding agent 场景)。

## 8. 可裁决判据(双假设预注册,2027-12-31 截止)

框架预测:层间总线(晋升/consolidation)成为下一瓶颈位。竞争假设:**重训/蒸馏即记忆**
(SSI 若成,分层不需要)。裁决判据(任一即中):
① 主流 agent 框架将 memory promotion/consolidation 列为标准组件;
② 顶会 ≥3 篇 promotion 管线论文;③ 头部闭源模型发布会公开 consolidation 机制;
④ 反向:蒸馏式记忆更新成为主流(框架方向证伪)。

## 9. 诚实边界(v2 沿用)

- 「评估最前置」对 nautilus-compass 是相对成立(写入门 9/15 补上才绝对成立);
- MMU 是结构类比非机制声明;算子表是理想化分类;
- 框架当前解释力强、预测力弱——判据#8 是唯一的可证伪出口。
