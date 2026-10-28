# 北极星执行方案 V1:unipat-in-agent 系统化工程(组织级)

> 2026-10-04 深夜 · 平台框 · **已批**(用户同夜:整案批准+渠道序「判分页→v7触客→BC外发」;四层死线照立为预注册判据)
> 输入:用户北极星定调(docs/NORTH_STAR_UNIPAT_AGENT_V1_20261004.md)+学界业界三路调研+仓内正本回顾(ARCHITECTURE/ORG_MECHANISM/BACKCAST/FUSION_ROADMAP/TSI)+平台 362 端点存量。

## 一、学界业界对照——我们站在哪(三路调研结论)

### 1.1 关键实证:我们的卖点有市场数据背书

| 发现 | 来源 | 对我们的意义 |
|---|---|---|
| **同模型不同 harness 差 10-15 分**("pick the harness, not just the model") | [SWE-bench 榜分析](https://www.swebench.com)/[vals.ai](https://www.vals.ai)/codesota | "提升 harness 能力"不是伪需求,是榜首之争的第一变量——v5 TSI 三线的方法论有真实付费场景 |
| **Contamination 危机**:GSM1k 私有集测出 -13%;SWE-bench 被疑背诵;GAIA-v2 重审计 | [Goodhart 数据](https://explainx.ai/blog/goodharts-law-ai-benchmark-contamination-gsm1k-mmlu-arena-2026)/[MAC-Bench](https://arxiv.org/html/2606.07805v1) | 信任缺口=商业空位:compass"判据预注册+独立判分+任何人可复算+判错公开认错"正是学界开出的药方,且已现役(CASEBOOK 12 案) |
| **失败数据集成为新方向**:Agent Error Dataset 5 万错误-诊断对(arxiv 3 天前) | [AED](https://arxiv.org) | 我们已有同构资产:errata 登记处+CASEBOOK 判例+fuel fail 轨迹——"卖轨迹"升级为"卖失败-诊断对",学界已验证需求 |
| **Elo+人投+专项赛道**成金标准 | LMArena/专项 Arena | J2a 周榜+VB 七轮的同构物;榜单专项化(harness 维度)是差异化空位 |

### 1.2 商业模式对照:工具型 vs 判定型

| 玩家 | 模式 | 计量轴 | 我们的位置 |
|---|---|---|---|
| [Braintrust](https://www.braintrust.dev/pricing)($116M 融资) | 评测+观测+playground 一体 SaaS | $249/mo+用量 | 他们卖**软件工具** |
| LangSmith($39/seat,~$2.5k/mo@1M traces) | LangChain 生态观测评测 | traces 数 | 同上 |
| AgentOps | 开源 SDK+freemium | 用量 | 同上 |
| **我们(compass 判分机构)** | **判读永久免费+装订收费+卖数据卖轨迹卖方法论** | 判例装订数/轨迹量/咨询 | 卖**判分结果+数据+Know-how**,工具全开源(PyPI assay 3.3.0)——工具型平台的护城河是生态锁定,我们的护城河是**独立公信力+失败数据资产**,不可被复刻 |

### 1.3 学界药方 → 我们已有的同构物(存量即答案)

| 学界方案 | 我们现役同构物 |
|---|---|
| 私有/隐藏测试集(GSM1k) | E1 判据预注册+判据冻结(v1 不可变条款) |
| 动态对抗基准(MAC-Bench) | VB 七轮 restock-gate+约束解码(判据回流) |
| 领域专用评测 | fuel/具身域数据(flywheel unipat) |
| 污染检测(n-gram/MinHash) | r79 学生自产禁入防自喂(7e505125 代码门)——组织内自喂即污染的组织级防控 |
| Held-out 探针 | S2 判据:fuel 版锚复考≥基线(r79 同批 10/13) |

## 二、过往探讨回顾——演进而非推翻

- **8/28 平台定位**(SSOT §⓪:AI 原生组织 OS,第一个客户是自己)→ 10/4 北极星是它的**对外商业化延伸**:OS 底座不变,业务面从"具身数采+验证"收敛为"具身域 unipat(飞轮)+agent 域 unipat(compass/v5)"双实例;
- **9/28 LEGAL_AGENT_ECOSYSTEM_BACKCAST** 的"十月 PMF 双验证"落位为北极星阶段 3 的判据(见 §四);
- **ORG_MECHANISM_ARCHITECTURE_V1**(RSI 机制防漂移)就是平台第 2/4 职能的机制正本——沉淀固化+降本;
- **OCTOBER_FUSION_ROADMAP** 三层融合=北极星的组织内对齐动作,不再重复发函,本次对齐函并入;
- **TSI(涡轮增压)**=北极星 L4 层(提升方法论)的 v5 侧正本。

## 三、平台存量映射——362 端点里直接可用的(零新建清单)

| 层 | 已有实物(可复用) | 缺的只是接线 |
|---|---|---|
| 判分层 | assay 登记处(外网已通)/errata 四枚举/E1 判据预注册/fde_verdicts 判分范式(3663 行)/score_reconcile 对账 | 外部委托入口页(判分页已挂,缺提交表单→A2A/PyPI 已可走通) |
| 榜单层 | J2a 周榜/VB 七轮/convergence API/驾驶舱渲染模式/门户卡 | **harness 对比榜页**(复用驾驶舱 fetch+textContent 惯例) |
| 评测集层 | **sinks `_sediment_endpoint` 工厂直接复用**(5 个 registry 端点现成,加一个 benchmarks/builtin 注册表=加一个 json+一行路由) | 主流评测集登记卡(SWE-bench/GAIA/Terminal-Bench 坐标+判据冻结状态) |
| 数据层 | fuel_trajectories 池/agent_tool_calls **42 万行运行时遥测**(=轨迹资产)/CASEBOOK 判例/errata | 失败-诊断对导出格式(AED 对标) |
| 管道层 | sinks 活性机制(今夜三件)/org_mailbox 总线/两闸结算/9 timer 骨架/ fuel 结算联动器 | 无 |

## 四、组织级方案:四层工程(每层:谁/判据/死线/复用什么)

| 层 | Owner | 首件 | 判据(预注册) | 死线 | 复用 |
|---|---|---|---|---|---|
| **L1 评测集层** | compass(直接工作)+平台(登记端点) | 主流评测集登记 3 件(SWE-bench Verified/GAIA/Terminal-Bench:坐标+判据冻结状态+污染风险注记) | ≥3 集登记上 sinks,判据冻结页可复算 | 10/8 | `_sediment_endpoint` 工厂(零新代码) |
| **L2 判分层** | compass | 对外判读服务入口激活(判分页已挂,收首笔外部委托) | **首笔外部委托判分立案**(北极星 PMF 关键信号) | 10/31 | PyPI assay 3.3.0+A2A+信箱 |
| **L3 榜单层** | 平台挂壳+compass/v5 供数 | harness 对比榜 v0:同任务集×≥2 harness(我们自家 v5-harness+第二个开源 harness)分差表 | 榜页外网可访+数据可复算(附复算命令) | 10/12 | 驾驶舱渲染模式/门户卡 |
| **L4 提升方法论层** | v5 | TSI 三线 11 件转存+首例"harness 提升前后分差"实证(自家 dogfood:LoRA 学生 v2 vs r79 基线) | 前后分差可复算+方法论文档化 | 10/15 | TSI 提案 V1+fuel 闭环 |

**平台管道贯穿**:sinks 活性机制管(L1-L4 全部产出物的正本锚)+两闸管结算+org_bus 管协同——今夜已全部生效,零额外建设。

## 五、PMF 路径(四阶段,判据预注册)

1. **内部 dogfood(已完成)**:r78→106 样本→LoRA→判据 v1 复考,组织第一个客户是自己;
2. **公开榜单(进行中→10/12)**:L3 上线,判分服务页引外部流量,榜单页=获客面;
3. **首笔外部委托(PMF 关键信号,10/31 前)**:判读免费入口→装订收费;渠道=v7-telegram 触客线+判分页 SEO/BC 外发(BC 线按 9/20 外发 B 级制,用户批后走);
4. **数据+方法论售卖(Q4 末验证)**:失败-诊断对数据集(AED 对标格式)+harness 提升咨询;判据:首个外部付费(任意金额,复用 ¥0.01 收钱链全通先例)。

## 六、执行序(本周)

| 日 | 件 | 谁 |
|---|---|---|
| 10/5 | 对齐函回执五框(已发);soul 首验 12:00;征议截止 22:12 | 各框 |
| 10/6 | v5 提案正式死线(已提前交)+L1 登记端点上线(平台,~10 行) | 平台 |
| 10/8 | L1 三集登记齐(compass 供坐标) | compass+平台 |
| 10/12 | L3 榜单页 v0 外网可访 | 平台+compass/v5 |
| 10/15 | L4 首例前后分差实证 | v5 |
| 用户侧 | 触客名单(卡 PMF 关键路径,给到即出作战卡) | 用户 |

## 七、呈批

1. 本方案批否(批→成为北极星执行正本,周报按此对齐);
2. L2 首笔外部委托的渠道优先级:判分页自然流量 / v7 触客 / BC 知乎外发——先后序请拍;
3. 四层死线(10/8-10/31)是否照此立判据。

—— 平台框 2026-10-04 深夜
