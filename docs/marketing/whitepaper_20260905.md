# nautilus-compass 技术白皮书(Deep-Dive)

> 版本 v1.1 · 2026-09-05 · 面向技术读者(工程师/研究者/评测从业者)的深度正本。
> v1.1:参考 nautilus-core 平台白皮书(Technical Whitepaper V2,2026-03)的结构纪律,
> 补生态定位(§3.0)/路线图与开放问题(§9.1)/研究贡献与引用(§10);版本变更随版本号记录。
> 立场文与发布会帖讲"为什么",本文讲"是什么、怎么做、数字怎么来"。
> 每个数字附 evidence 锚(§11 索引);口径以 [SCOREBOARD](../nautilusmem/SCOREBOARD.md) 定案为准。

---

## 1. 摘要

nautilus-compass 是一个 local-first 的 agent 记忆与可靠性层:写入路径存储原文、零 LLM 调用、本地嵌入,全部智能集中在读取路径(查询分型路由 → 混合检索 → 上下文组装)。

核心结果(口径与复现细节见 §4/§5/§6):

| 战场 | 结果 |
|---|---|
| LongMemEval-S e2e(500 题) | 42.6% → **75.4%**(剔判官断连口径 81.6%),纯 context 工程 +32.8pt |
| 检索对打 mem0 2.0.19 复现(同题同判据) | P@1 **0.890** vs 0.774(P@5 0.978/0.916,MRR 0.929/0.834) |
| LOCOMO-10 客场(n=1986) | P@1 **0.644** vs mem0 0.592 |
| EverMemBench-Dynamic(第三方榜) | **44.4-47.3** vs Mem0 37.09 / Zep 39.97 / MemOS 42.55 |
| LongMemEval-V2(上游官方基准,451 题双域) | web **40.0%** / ent **38.4%**(untuned 19.6/12.8) |
| memory_query 延迟 | p95 **0.34-0.80s**,对照组 LLM controller 架构 26.9s(~80×) |
| 全链路复现成本 | ≈ **$3.50**(GPU 租金+judge 调用),脚本与 evidence 全开源 |

配套贡献:判分卫生学(judge failure taxonomy + hygiene protocol,arXiv 在投 paper2)——我们自己抓了判官 5 次事故,其中一次基础设施断连把 500 题里 14.2% 静默记成错答。

### 按受众读法

| 读者 | 建议路径 |
|---|---|
| 研究者 / 评测从业者 | §2 立场 → §5 判官病理学 → §6 评测版图 |
| 工程师 / 架构师 | §3 架构 → §4 算法解剖 → §7 安全与多租户 |
| 想上手的人 | §1 摘要 → §8 接入与成本 |
| 商业 / 生态合作 | §8 价值与成本 → §9 dogfood → §10 贡献与开源 |

---

## 2. 问题与立场:写时压缩为什么必输

### 2.1 三个不变量

**不变量 1 · 未来查询分布不可知。** 记忆的价值在检索时兑现;重要性只在被问到的时刻显影。写入时做有损提炼(摘要/事实抽取/图谱),是在意图未知的时刻对未来下注。实证:同一份记忆库,仅按题型切换检索单元,P@1 从 0.20 → 1.00(单会话用户型)——变的不是记忆,是问题。

**不变量 2 · 原文是唯一可重新索引的表示。** 提炼物被冻结在当初那个 LLM 的认知水平;无损原文明天可以换更好的 embedder、更好的读法、可以作训练燃料。写时压缩不只丢信息,它把记忆锁死在技术现状里。

**不变量 3 · 成本曲线方向反了。** 存储趋零,LLM 调用恒贵。把便宜的(原文)换成昂贵的(提炼物)是逆成本曲线。写入免费 + 读侧 p95 0.34-0.80s 是把智能放在正确时刻的自然结果,不是优化奇迹。

### 2.2 第三方背书(ICLR 2025 LongMemEval 基准论文,arXiv 2410.10813)

- §5.2:用 LLM 提炼的摘要/facts 替代原文 → 因信息丢失损害 QA;
- Appendix B 人肉研究:ChatGPT 随对话压缩历史时覆写关键信息,Coze 漏记间接提及;
- 长上下文直读在 LongMemEval-S 上掉 30-60%——裸读也是死路,记忆层的必要性由基准作者论证。

### 2.3 为什么业界普遍做反了

1. **路径依赖**:记忆系统从对话摘要演化而来,写时提炼"顺手"——没人把记忆当存储问题而非理解问题。
2. **商业激励错位**:写时 LLM = 按 token 收租的理由 + "智能记忆管理"叙事;简单架构没故事。不是想不到,是不愿意。
3. **评测盲区**:没有严格基准就量不出压缩丢了什么;上游 2024 年才造出尺子(LongMemEval),我们是第一波量出写侧路线败绩的团队之一。
4. **直觉错觉**:LLM 时代的直觉是"聪明模型处理一切";反直觉认知是——聪明模型应在最需要的时刻(读取)出现一次,而不是在每个时刻(写入)出现无数次。
5. **出身红利**:自用 dogfood,隐私/本地/成本是硬约束。约束逼出正确架构;一人开发者把劣势变成方法论优势。

---

## 3. 架构

### 3.0 生态定位:与 nautilus 平台的关系

compass 起源于 nautilus 智涌平台(nautilus.social):平台的 agent 舰队需要跨 agent 记忆与可靠性层,compass 从那里长出来并保持 dogfood(§9)。在平台的 Trinity 三层架构(Nexus 协议 / Orchestrator / Memory Chain)中,compass 对应记忆与治理层的独立化、开源化形态——**作为独立组件发布,不依赖平台即可完整运行**(本地三条命令,§8)。平台理论基础(Epiplexity, arXiv:2601.03220;DMAS, arXiv:2512.02410)与平台侧白皮书见 nautilus-core 仓库;本文只覆盖 compass 自身的设计、算法与证据。

### 3.1 六层总图

```
┌─ 进化层 📊  记忆胶囊 W1 验证写回 → W2 继承召回 → tier 晋升/可逆衰减
├─ 治理层 ✅  drift 检测(AUC 0.83)· 跨 agent 合约审计 · scoped token 三层隔离
│            · 判分卫生学 · merkle 链/数字声明验证
├─ 组装层 ✅  摘要卡按题型路由(ms/ssa/tr)· 日期时间线排序 · utterance 窗口组装
├─ 召回层 ✅  六型分型路由 → BM25+dense RRF 融合 · 日期锚定 · 分型粒度选择
├─ 存储层 ✅  原文 verbatim(md+frontmatter)· 本地 BGE-m3 嵌入 · 日期元数据 · 零 LLM 零上云
└─ 格式层 ✅  OKF(Google 开放知识格式)兼容:记忆 bundle 可被任何 OKF 工具读
```

数据流:

```
写入:对话/文档 → verbatim 存储 → 本地嵌入+日期元数据 → 索引   (零 LLM,免费,无损)
读取:问题 → 分型路由(6 型)→ 混合检索(分型粒度)→ 组装层 → reader LLM → 答案
进化:解题 reward≥1.0 → 写回胶囊 → 他 agent 召回继承 → report 回流 → 质量晋升
```

状态标注纪律:✅ 已验证 LIVE / 📊 已接线待证 / 📐 设计愿景。进化层的 tier 晋升做过三次独立实测 uplift 均为 0(语料信号稀疏),因此保持"待证"标注,不冒充已验证——feature 价值账本([FEATURE_VALUE_LEDGER](../FEATURE_VALUE_LEDGER.md))记录每一次升降级。

### 3.2 写入端决策表

| 决策 | 内容 | 理由 |
|---|---|---|
| 存什么 | 原文 verbatim(md+frontmatter+`[[链接]]`) | 不变量 2 |
| 怎么索引 | 本地 BGE-m3 dense + BM25 词面 + 日期元数据 | 三路互补:词面扛精确标识符,dense 扛语义,日期扛时序 |
| 不做什么 | 零 LLM:不提炼 facts、不建图谱、不生成摘要、不上云 | 不变量 1+3 |
| 质量门 | 胶囊写回需 reward ≥ 1.0(验证过的经验才入库) | 防退化:错经验不入库,不被跨 agent 复利成毒 |

### 3.3 架构决策记录(放弃过什么,代价是什么)

| 被放弃的方案 | 结果 | 教训 |
|---|---|---|
| 图数据库(Neo4j)+ graph rerank | 检索 -6.2pt | 图边引入噪声;原文+混合检索已够——复杂度做减法不做加法 |
| cross-encoder reranker | e2e -2pt | bge-m3 自身排序已更好;瓶颈在排序质量时加 reranker 是叠床架屋 |
| 大 K(K=50 vs 20) | 无差异 | 无 reranker 时 K 只加宽 RRF 窗口,top-5 不变 |
| 小嵌入模型(Qwen3-0.6B) | wash(ku +1/ssa −2;P@5 0.833 vs bge-m3 0.867) | 嵌入质量是检索层地基,换小模型省的钱买不回排序损失 |
| LoRA 域适配 embedder(LME-V2 刀3) | 代理指标涨(guard recall@5 0.533→0.733)但 e2e parity → 未采纳 | 预注册 +5pt 门没过就不上;代理指标≠端到端 |
| abstention gate(主动拒答) | 预注册判据拒收:误拒 web 92 题(门 ≤1)/ent 89 题(门 ≤2) | 95% 新拒答题本来就是答错的题——打掉的是噪声不是错误 |

代价的诚实披露:verbatim 存储意味着存储增长快于提炼式方案;索引冷启动慢(max 尾部 web 23.8s/ent 50.9s,是索引进场非稳态);上下文预算 24k 限制了单查询可塞证据量(§6.3 的诚实定位来源之一)。我们没有解决这些问题,而是判断它们在当前硬件成本曲线下不构成瓶颈。

### 3.4 治理层(独有件)

- **drift 检测**:动作前对照失败模式锚点,AUC 0.83,p95 < 50ms;
- **跨 agent 合约审计**:多 agent 共享文件时追踪隐式义务;
- **多租户隔离**:scoped token 三层(user/设备/agent),四探针公网可验证,撤销即时(§7);
- **判分卫生学**:预注册锚/判官函数调用级冒烟/多口径强制披露/二项噪声带(§5)。

测量可信度先于分数——这是治理层存在的理由。

---

## 4. 算法解剖

### 4.1 六型分型路由

问题先分类,每型不同检索单元与组装策略:

| 型 | 全称 | 检索/组装策略 | e2e 基线→终局(8/29 锚→9/4 重判口径) |
|---|---|---|---|
| ssu | single-session-user | turn 级块(滑动窗 2) | 0.957 → **0.971** |
| ssp | single-session-preference | turn 级块 | 0.800 → **0.800** |
| ku | knowledge-update | turn 级块(后扩) | 0.731 → **0.808** |
| ssa | single-session-assistant | 摘要卡 | 0.250 → **0.839** |
| ms | multi-session | 摘要卡 | 0.226 → **0.692** |
| tr | temporal-reasoning | 摘要卡+日期时间线 | 0.158 → **0.624** |

干净口径(剔除 71 判官断连题,n=429):ms 73.2 / ssa 85.4 / tr 83.3 / ssu 96.9 / ku 79.5 / ssp 75.0。

设计逻辑:用户陈述型问题的答案通常落在一个 user turn 里——检 turn 级块;跨会话/助手行为/时序型需要"每场会话发生了什么"的地图——路由到逐会话摘要卡(按日期排序 + Evidence Extracts 3→6 条);tr 额外获得日期时间线。**ssu/ssp/ku 的 context 字节不变**(不碰强项),改动集中在三弱型。

### 4.2 归因链:42.6 → 75.4 每一步

| 步 | 日期 | 数字(full / 剔除断连) | 改动 |
|---|---|---|---|
| 0. 配对修复轮 | 8/28 | n=30:0.267 → 0.567 | 600 字符 context 截断 → 分型 utterance context + 日期锚定(小样本验证用,不入主链) |
| 1. 500 题基线 | 8/29 | **42.6%**(213/500) | GPU 4 分片;bge-m3 dense + BM25 RRF(k=60)+ 日期锚定 + 四型 utterance context |
| 2. 摘要层(A 臂) | 9/3 | **70.0%** / 81.6% | 三弱型(ms/ssa/tr)路由到摘要卡;9/2 预注册三态门(锚=基线同 judge 同 subject),三型全过门 |
| 3. 判官断连重判 | 9/4 | **75.4%**(377/500)/ 81.6% | 71 题(14.2%)曾因 judge 网关 403/超时被记错;同判官同 prompt 仅加重试,71/71 解决(27 题翻对) |

净效应 +32.8pt,来源分解:**约 27.4pt 来自摘要层(方法),5.4pt 来自判分修正(测量)**——后者不是方法效应,是修复测量仪器。混报这两件事是评测写作最常见的自我欺骗。

预注册细节:门在跑数前落仓带 hash——ms ≥35%(锚 22.6)/ ssa ≥40%(锚 25.0)/ tr ≥30%(锚 15.8);终局三口径 0.700/0.754/0.816 全过门(§5.4)。

### 4.3 检索层:0.784 → 0.890 的路由演进

对打 mem0 的检索 P@1 不是一次到位:

| 版本 | P@1 | 增量来源 |
|---|---|---|
| m3-only(K20 混合) | 0.784 | 与 mem0 打平(0.774)——纯基建不赢 |
| + ssu/ssp 分型路由 | 0.848 | 单会话型切 turn 级 |
| + ku 路由 | 0.876 | 知识更新型切 turn 级 |
| + 日期锚定 | **0.890** | tr P@1 0.83→0.88;P@5 0.978 / MRR 0.929 |

中间态如实公开:首版 m3-only 与 mem0 打平。赢在路由,不赢在嵌入——这决定了对打的正确表述方式(§4.4)。

### 4.4 检索对打的实验设置(逐字段)

- **同题**:LongMemEval-S 全 500 题,按 question_id join;
- **同判据**:retrieval-only 双方(不涉 reader/judge);mem0 侧 `infer=False`(纯检索模式,不开 LLM 提炼);
- **各用默认嵌入**:compass 用 bge-m3,mem0 复现用 vertexai text-embedding-005——比的是两个系统开箱即用的检索层,不替对方换嵌入;
- **版本钉死**:mem0ai 2.0.19(8/27 pip 核对为 PyPI 最新;hosted 闭源版另注);
- **复现成本**:CPU 可跑(smoke)/ GPU 推荐(全 500 题),一条命令(`scripts/reproduce_lmes_retrieval.sh`)。

诚实披露:对方嵌入在部分单会话型查询上更强(ssu 残余差距归因嵌入),我们靠分型路由整体赢。**"同题同判据"成立,"同嵌入"不成立也无需成立**——开箱对打才是用户真实场景。

### 4.5 LOCOMO 与 EverMemBench 口径

- **LOCOMO-10**(n=1986):utterance dual-speaker chunks,P@1 0.644 / P@5 0.890 / MRR 0.740,vs mem0 2.0.19 的 0.592/0.802/0.677。temporal 类 0.24→0.42 仍是双方案共同弱项(embedder-common weakness)。mem0 论文自报 66.9% 为 e2e LLM-judge 口径,不可与本表直接比。
- **EverMemBench-Dynamic**(第三方公开榜,5-topic 版 n=500):Run 1 **44.4%**(头条主动用首轮防挑样)/ Run 2 47.3%(n=497),跨 Run 均值 45.84;Run 2 Bootstrap 95% CI (42.9, 51.7)。对照已发表基线:Mem0 37.09 / Zep 39.97 / MemOS 42.55 / MemoBase 34.27。**不 claim industry SOTA**——榜单口径以官方 Table 4 为准。

---

## 5. 判官病理学:我们抓了自己判官 5 次

> 详见 paper2(arXiv 在投)*Judge Failure in the Wild*。此处是工程视角精炼。

### 5.1 三型 taxonomy(判官失败 = 资源耗尽)

部署中的判官是 `J*(θ, B, I)`:模型 θ 的知识边界、输出预算 B、打分基础设施 I。任一耗尽即失败,三型机制不同、信号不同、解药不同:

| 型 | 资源 | 检测信号 | retry 可治? | 可部署前检出? | 对分数的效应 |
|---|---|---|---|---|---|
| **J-K** 知识边界 | θ 的判别力 | Δ 探针集 | 否 | 是(探针集) | 静默放过错误 |
| **J-B** 输出预算 | B | 截断率/空响应率 | 否 | 是(冒烟) | 塌缩到默认标签 |
| **J-C** 连接 | I | 错误标签率 | **是** | 仅运行中 | 假性错答(下界) |

### 5.2 J-K:知识边界盲区(受控实验,2,600 次真实 API 调用)

- 双判官族(Kimi k3 / MiniMax-M3)对注入数值误差的通过率**随幅度单调下降**:±0.1% 时 37-48%、±1% 时 12-14%、±10% 时 0%——盲区边界稳定在 0.1%-1% 之间,跨族差 ≤11pp(结构性,非单模型缺陷);
- 盲区在"事实性要求已写入判分 prompt"的前提下仍存在;换更强判官(两族)没用;
- 判官能抓的:实体替换(0% 通过)、常识错误(0%)、文风夸大——不是普遍轻信,是数值精度盲区;
- Δ 判别信号(良性均分−污染均分)可作部署前带状分离器:Δ=9.7→0% 通过,5.3→45%,2.3→13%,0.8→0%——盲区在中带;
- 局限:两判官均为 reasoning 模型,对非 reasoning 架构的泛化未测;prompt 变体消融未做(开放项,不作断言)。

### 5.3 J-B 与 J-C:两次生产事故

**Case 1(J-B,预算饥饿)**:LME-V2 调优循环中,reasoning 判官 `max_tokens=4096` 被思考过程吃满,截断输出解析为默认标签——ent 域 146/211 题(69%)被记 0,raw 日志 250 次空响应。连续两轮调优被误判为"方法未过门"后才发现是测量坏了。重判(16384/low)后 web +3.3pt / ent −1.9pt——**方向相反**,不重判就永远带着错数字发布。解药=部署时冒烟:真实尺寸条目上断言判官输出非空可解析。

**Case 2(J-C,断连)**:500 题生产跑中 71 题(14.2%)由间歇 403/超时网关后的判官"判分"——管道把中止调用记为错答。整轮重试未清零(新题继续命中)= 随机基础设施故障,非题目绑定。同判官同 prompt 重判解决 71/71(27 题翻对)。失真 5.4pt ≈ 被测真实效应(32.8pt)的 1/6——基础设施噪声可吞掉六分之一的被测效应。中期一次"-20pt 子型回归"事后证实全部是断连误标。

### 5.4 Hygiene protocol(P1-P5)

1. **P1 预注册锚与门**:跑数前冻结分型基线锚、提升门与裁决规则(版本化+hash);裁决标准不得在看到分数后选;
2. **P2 同判官重判退避**(J-C 解药):带基础设施签名(4xx/5xx/超时/空 verdict)的条目只重试打分调用,答案原样复用;退避后仍败的报告,不静默丢弃;
3. **P3 多口径披露**:保守(断连记错)/ 重判后 / 干净(剔除)三口径并报;结论仅在口径一致时称稳健;拒绝 cherry-picking;
4. **P4 部署冒烟**(J-B 解药):真实尺寸条目、非空可解析断言、预算占用审计、判官配置变更后重跑;
5. **P5 二项噪声带**:n=30 子型上一题=±3.3pt;带内"回归"一律推迟到逐题判官输出审计。

六相 checklist(部署前 Δ 探针+冒烟 / 跑前预注册 / 跑中签名率监控 / 跑后重判+多口径)——成本主要是几次 API 调用。**这套协议产生的直接动因是我们自己 5 次事故(401 变量名/断连/预算吃满/空响应/子型幻影回归),全部是配置层,没有一次是模型能力问题。**

---

## 6. 评测版图

### 6.1 五个战场各测什么

| 战场 | 性质 | 回答的问题 |
|---|---|---|
| LME-S e2e 500 题 | 自建 harness 主场 | 方法效应:路由+组装带来多少(42.6→75.4) |
| 检索对打 mem0 | 同题同判据 | 相对优势:开箱检索层谁强(P@1 0.890 vs 0.774) |
| LOCOMO-10 | 客场 | 换数据集结论是否保持(0.644 vs 0.592) |
| EverMemBench | 第三方公开榜 | 别人出的卷子防自吹(44.4-47.3 vs Mem0 37.09) |
| LME-V2 451 题 | 上游官方基准 | 社区可比坐标系(40.0/38.4,untuned 19.6/12.8) |

组合逻辑:主场证效应、对打证相对、客场证泛化、他榜防自吹、官方基准证可比。任何单一战场都可被质疑,组合的覆盖面难以全部归为"自选有利"。

### 6.2 LME-V2:调优记录(d12 三刀 + 判分修正)

上游:xiaowu0162/LongMemEval-V2(Di Wu 等,451 手工题,web/enterprise 双域,license Apache-2.0,题与轨迹归上游,我们只发自研后端/判分工具/evidence)。官方接入路径(`@register_memory` 自定义 memory backend),reader 与官方一致(Qwen3.5-9B)。

| 步 | 内容 | 效果 |
|---|---|---|
| untuned 基线 | 8/30 首跑 | web 19.6 / ent 12.8 |
| 刀1 abstention 判分口径 | 禁裸 UNKNOWN,引导 judge 走两条合法得分路线(指出前提矛盾/明示无法验证 live state) | abstention 组得分率 web 2.8→45.8 / ent 0→83.9;裸 UNKNOWN 252→0 |
| 刀2 检索单元升级 | a11y 空结构行剪枝 + 轨迹内 dense 重排 + 预算 12k→24k | gold-在场得分率 ent 0.115→0.652(倒挂修复);procedure web +16.6pt |
| 刀3 embedder LoRA | 代理指标涨,e2e parity | **未采纳**(预注册 +5pt 门未过) |
| d13 判分修正 | judge 4096→16384 重判(§5.3 Case 1) | web 36.7→**40.0** / ent 40.3→**38.4**(方向相反) |

刀4(abstention gate)与 cheap-tier 组合均被预注册判据拒收(§3.3)——负结果与正结果同等记录。

### 6.3 官方坐标系里的诚实定位

官方 README baseline(gpt-5.2 judge + 200k 预算,Small Overall):No retrieval 1.3 / RAG query→slice 42.8 / RAG slice+notes 51.0 / AgentRunbook-R 58.6(延迟 26.9s)/ Codex 69.9(177s)/ AgentRunbook-C 74.9(108s);compass 合并 ≈39.3。

**放进去看:与最弱 RAG 基线相当,不是优势。** 差距的两个结构性来源:①上下文预算 24k vs 官方 200k(8.3×);②判分口径(全题 doubao LLM judge vs 官方程序化为主+gpt-5.2)。我们的差异化不在榜单名次,在**延迟**(memory_query p50 0.165-0.328s vs AgentRunbook-R 26.9s,~80×)与**判分卫生学贡献**。真正的攻坚方向=官方三池设计移植(raw state/event/note pools;A 臂摘要卡≈note pool 简化版),目标 Small 55-60%——有竞争力后再上官方 leaderboard。这是把"我们在哪里"说清楚,比把 40.0 说成大胜更有信用。

---

## 7. 安全与多租户

### 7.1 三层身份模型

```
user(JWT 身份)→ 设备 → agent(scoped token:read:<project> / write:<project> / read:*)
```

- 隔离边界 = project 命名空间(`u_<id>_memory`);header-only 身份(X-User-ID 类)永久禁止——v0.9 曾有 X-User-ID 冒充洞(公网可冒充任意用户读写),已改 JWT-only 并五项矩阵验证;
- 自助 token 由 signup→console 自助签发,scopes 只含持有者自己的空间;缺省 project 显式注入持有者 uid(读写落自己空间,而非进程默认空间)——9/5 曾抓到"自助 token 读写全断+跨租户读"双洞,根因是检查侧与执行侧不同源 resolve,终修后公网复验 own-space 通过;
- ops token(tokens.json,`tools.*` 旧格式标志)为内部调度凭证,可见全量工具面;公网自助 token 只见 8 个用户工具(tools/list 17→8,内部工具知名字直调也 forbidden)。

### 7.2 四探针(公网可重跑)

| 探针 | 断言 |
|---|---|
| P1 | A 的 token 读 B 的空间 → forbidden |
| P2 | A 的 token 写 B 的空间 → forbidden |
| P3 | A 的 token 读写 A 自己的空间 → 放行(不误伤) |
| P4 | 撤销 token → 下一次调用立即 401 |

脚本开源(`probes.py`),任何人对生产端点可重跑;发布流程规定四探针 FOUR-GREEN 才发帖。多轮修复后(9/4 workers 2、9/5 双洞、tools/list 收敛)各复验一轮 FOUR-GREEN——**隔离属性不是设计声明,是可持续重验的生产事实**。

---

## 8. 价值与成本

### 8.1 延迟:80× 差距从哪来

写入零 LLM + 读取纯检索组装,所以 memory_query p95 0.34-0.80s(d12 全量实测:web p50 0.165/p95 0.339,ent p50 0.328/p95 0.798)。对照组 AgentRunbook-R(LLM controller 架构)单查 26.9s≈80×。不靠 cache 不靠捷径——智能放在了不花钱的时刻。诚实注记:max 尾部(web 23.8s/ent 50.9s)= 冷启动/索引进场,非稳态。对交互式 agent,亚秒检索与 27s 等待不是同一可用性等级。

### 8.2 成本账

- **写入 0 token**:每条记忆零 LLM 调用(对比:写时提炼方案每条记忆都要过 LLM——按条计费的边际成本在我们这里是零);
- **读取**:检索+组装无 LLM,reader 一次调用;
- **复现成本 ≈$3.50**(v0.8 时代实测口径):LLM ≈¥7(5M in×¥1/M + 0.5M out×¥4/M,DeepSeek)+ T4 spot 8h×¥0.40=¥3.20 + 权重下载网络 ≈$0.50 + 冷启 ≈$0.50;约 8h 墙钟;
- 诚实注记:竞品每条记忆写入的 LLM 调用次数我们无实测数字(闭源),只作定性对比——"写入免费"是我方可验证的事实,对方的成本不是我方断言。

### 8.3 三档接入与 license

| 路径 | 适合谁 | 成本 |
|---|---|---|
| 本地三条命令(git clone + install + daemon_start) | 隐私/成本敏感,单机 | 永久免费,数据不出机器 |
| Hosted beta(compass.nautilus.social) | 快速试用/团队 | 自助 signup → scoped token → 任意 MCP 客户端(open beta) |
| 私有化 | 组织部署 | 联系我们 |

License:Modified MIT(Kimi 式)——MIT 基础 + 商标保护 + 托管 100 付费用户上限;自部署/内部/个人永久免费。开放程度用行为定义(全源码 + $3.50 复现 + evidence 链 + 四探针可重跑),不用标签。

---

## 9. dogfood 与进化层

- **130 天 771 commits,其中 603 由 agent 舰队提交**——nautilus 智涌平台多 agent 调度跑在 compass 上,记忆胶囊跨 agent 继承有实录:agent A 解题 reward 1.0 → 写胶囊 → agent B 直接继承(B 从 FAIL→PASS,6/17 实测);
- 进化层诚实分级:W1→W2 端到端已实战;tier 晋升/PoI 重排/可逆衰减已接线但三次独立实测 uplift 均为 0——保持"待证",等盒语料重测;不冒充已验证。

这本身是产品的证明:一个记忆层好不好,先看它的作者敢不敢把组织日常跑在上面。

### 9.1 路线图与开放问题

| 期 | 事项 |
|---|---|
| 发布窗口 | hosted beta 邮箱验证门禁上线 / PyPI 3.1.1 发版 / MCP 目录提交 |
| 主攻坚 | LME-V2 官方三池设计移植(raw state/event/note pools;A 臂摘要卡≈note pool 简化版),目标 Small 55-60%(超 AgentRunbook-R)——当前 ≈39.3 与最弱 RAG 基线相当,这是主要差距战场(§6.3) |
| 工程 | 嵌入 daemon 并行化(生产读吞吐 ≈5 rps 天花板的根因是 BGE-m3 串行推理) |
| 待证 | 进化层 tier 晋升 uplift 三次实测为 0,盒语料重测前保持待证不动 |
| 开放问题 | tr 时序推理(终局 62.4)仍是六型短板;J-K 判官盲区的 prompt 变体消融未做;判官结论对非 reasoning 架构泛化未测;hosted 侧外部真实用户案例为零(dogfood 之外) |

---

## 10. 研究贡献、开源与引用

### 10.1 贡献映射

| 贡献 | 载体 |
|---|---|
| 判官失败三型 taxonomy(J-K/J-B/J-C)+ hygiene protocol(P1-P5) | paper2(arXiv 在投)+ §5;协议 v1.0 随基准分发([PROTOCOL.md](../nautilusmem/PROTOCOL.md)) |
| 分型路由+摘要卡的 context 工程方法(+32.8pt 可复现) | §4;脚本与 evidence 开源 |
| 负结果预注册文化(七个被拒绝/关闭方案全公开) | §3.3 / §6.2;预注册文件带 hash 落仓 |
| 生产级多租户隔离验证方法(四探针) | §7;任何人对生产端点可重跑 |

### 10.2 开源承诺

全源码 + 复现脚本(检索对打一条命令 ≈$3.50)+ evidence 链全公开 + 四探针可对生产端点重跑。License:Modified MIT——自部署/内部/个人永久免费;开放程度用行为定义,不用标签。

### 10.3 引用

```bibtex
@article{longmemeval2024,
  title={Benchmarking Chat Assistants on Long-Term Interactive Memory},
  author={Wu, D., et al.}, journal={arXiv:2410.10813}, year={2024}}
@article{lmev22026,
  title={LongMemEval-V2: Evaluating Long-Term Agent Memory Toward Experienced Colleagues},
  author={Wu, D., Ji, Z., Kawatkar, A., et al.}, journal={arXiv:2605.12493}, year={2026}}
@misc{paper2_2026,
  title={Judge Failure in the Wild: A Taxonomy of LLM-as-Judge Breakdown and a Hygiene Protocol for Long-Memory Evaluation},
  author={Wang, Chunxiao}, note={arXiv in submission}, year={2026}}
@article{epiplexity2026,
  title={From Entropy to Epiplexity}, journal={arXiv:2601.03220}, year={2026}}
@inproceedings{dmas2025,
  title={Decentralized Multi-Agent System with Trust-Aware Communication},
  booktitle={IEEE ISPA 2025}, note={Best Paper Award}, year={2025}}
```

---

## 11. 附录:evidence 索引

| 断言 | 锚 |
|---|---|
| e2e 500 题基线 42.6(8/29) | `docs/evidence/e2e_500_full_20260829.json` |
| 摘要层 70.0/81.6 + 预注册门 | `docs/plans/2026-09-02-summary-layer-preregistration.md` · `vtf/_e2e_diag/arm_a_final_verdict.md` |
| 71 题重判 → 75.4/81.6 | `vtf/_e2e_diag/arm_a_final_verdict.md` · `tools/rejudge_errors.py` |
| 配对修复轮 0.267→0.567(n=30) | `docs/evidence/e2e_context_fix_20260828.json` |
| 检索对打 0.890 vs 0.774(设置/嵌入/版本) | `docs/evidence/headhead_mem0_full500_20260826.json`(protocol 字段) |
| LOCOMO 0.644/0.890/0.740 | 同上 json `locomo_*` 字段 |
| EverMemBench 44.4/47.3 + CI | `docs/REPRODUCE.md` §110-140 |
| LME-V2 untuned→d12→重判 全记录 | `docs/nautilusmem/SCOREBOARD.md` · `vtf/_compass_lmev2_out/d12/` `d13/` `d14_*` |
| 刀1/刀2 分项数字 | `vtf/_compass_lmev2_out/d12/D12_VS_BASELINE_20260830.md` |
| 判分修正(web +3.3/ent −1.9) | `vtf/_compass_lmev2_out/d13/D13_FIXATION_20260831.md` |
| 判分协议 v1.0 | `docs/nautilusmem/PROTOCOL.md` |
| LME-V2 attribution/官方坐标系/定位纠偏 | `docs/nautilusmem/ATTRIBUTION.md` |
| 判官三型 taxonomy/P1-P5/三口径 | `docs/papers/paper2_judge_hygiene.tex`(arXiv 在投) |
| 延迟 p95 0.339/0.798 实测 | `docs/nautilusmem/SCOREBOARD.md` §2 |
| 负结果全集(rerank/K50/Qwen3-0.6B/Neo4j/LoRA/abstention gate/cheap-tier) | `docs/evidence/headhead_mem0_full500_20260826.json` · `CHANGELOG.md` · `vtf/_compass_lmev2_out/d14_verdict_20260902.md` |
| 四探针/三层模型/冒充洞 | `probes.py` · `docs/plans/2026-08-30-multi-tenant-memory-design.md` · `docs/SECURITY_TOKEN_SCOPE_20260901.md` |
| $3.50 构成 | `BENCHMARKS_REPRODUCE.md` Cost breakdown |
| 六型基线→终局数字 | `vtf/_e2e_diag/arm_a_final_verdict.md` · README |
| 判官 5 次事故全录 | `docs/runbooks/EVAL_LESSONS_20260904.md` |

> 数字门纪律:本文任何数字若与 evidence 文件冲突,以 evidence 为准并回改本文——白皮书也是"自报",锚才是终审。
