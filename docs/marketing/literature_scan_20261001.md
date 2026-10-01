# 全网文献与案例调研档(2026-10-01 · 为论文主笔与「验证即反射」架构供弹药)

> 六线调研:压缩×智能理论/PRM 验证器/abstention(U 态)/SSI 持续学习/RSI 安全/组织记忆审计。
> 检索工具:WebSearch(zhipu 通道)。每条含我们方向的映射判断。

## A · 压缩=智能(理论根)

| 文献 | 要点 | 对我们的意义 |
|---|---|---|
| Delétang et al. 2023 "Language Modeling is Compression"(ICLR 2024, arXiv 2309.10668) | 奠基等价性:LLM+算术编码=SOTA 无损压缩 | 公式前半句的学术根 |
| "Compression Represents Intelligence Linearly" | 压缩能力=智能线性代理 | 可引用的量化表述 |
| Freedman(菲尔兹奖)2026 "Compression is All You Need"(数学纲领,alphaxiv 2603.20396) | 数学=层级嵌套概念的高可压缩性 | 高权重背书,趋势信号 |
| **"Truth as a Compression Artifact"(arXiv 2603.11749)** | 真值作为压缩动力学的涌现产物 | 🔴**最贴**:压缩产生真理→我们补"验证筛选真理"=公式的学术缝(**无人占据验证乘数**) |
| 2025-26 趋势 | 等价性→涌现现象→认知模型→工程应用 | 论文一的领域定位语 |

## B · PRM/验证器(验证侧学术热)

| 文献 | 要点 | 映射 |
|---|---|---|
| ThinkPRM(2504.16828,149 引) | 生成式过程奖励模型,**8K 合成样本**即可步级验证 | 小样本验证哲学同盟(我们 40 件测量同款) |
| R-PRM(EMNLP 2025) | 生成+评估两阶段单次生成 | 判分器 verbalizer 同构 |
| SAPO(2026.1)/SERL | 自适应过程优化/Actor 兼 Judge 双奖励 | 自进化环的机制参照 |
| 趋势 | 标量奖励头→生成式验证推理;PRM+自奖励合流;label-free RL | **验证器正在吃掉奖励模型**——我们的位置在这条曲线的生产端 |

## C · Abstention/选择性预测(U 态的学术对应)

| 文献 | 要点 | 映射 |
|---|---|---|
| "Know Your Limits"综述(TACL 2025,236 引) | abstention 分类学(R-Tuning 等) | U 态的文献坐标 |
| **Kalai et al. 2026(43 引)** | **LLM judge 选择性输出"I don't know"** | 🔴直接同题——他们提概念,**我们有 1454 语料+88.51% 三态判分器+生产读数**(ECE 0.072) |
| Geometry-Calibrated Conformal Abstention(2604.27914) | 条件正确性保证的共形弃权 | 判据升级路径 |
| [IDK] token(Cohen & Dobler) | 词表加 IDK 令牌 | =verbalizer 三态的方法学同构 |
| 核心论点 | **校准的弃权>弃权率** | 我们 ECE 0.072<0.10 正是主张的证据形态 |

## D · SSI/持续学习/真值供给

| 发现 | 要点 | 映射 |
|---|---|---|
| SSI 分析(LinkedIn) | 缺"使人类学习高效安全的价值函数" | 🔴真值供给缺口实锤=我们 T2 流卡位依据 |
| Self-Evolving Agents 综述(2507.21046) | WebEvolver 共进化世界模型 | 相关工作引用位 |
| Sutton Dyna/LeCun 世界模型派 | 世界模型 vs 记忆派之争 | 定位语境 |
| LessWrong reward misgeneralization | 学到的奖励函数错泛化风险 | =反自指护栏的学术对应(自训只限小判分器) |

## E · RSI 安全(2026.9 最新——最重的一块)

| 发现 | 要点 | 映射 |
|---|---|---|
| **OpenAI 2026.9 联大周提案** | "Preparing for recursive self-improvement"+RSI 国际标准+国会强制安全立法 | 🔴🔴 概念窗口刚开:RSI 治理成全球议题 |
| CSA 2026.6 "RSI Signals: Security Implications" | 公开 RSI 信号刻画+威胁映射+建议在训练/评测工作流追踪 RSI 信号 | **他们建议的"信号追踪"=我们三门/判绩账已在做** |
| 2026 International AI Safety Report(100+专家) | 失控风险关键=RSI | 引用位 |
| **"Verified self-improvement"概念** | 2026 话语中出现且被评"explicitly unfinished"——前沿实验室在请监管帮完成 | 🔴🔴🔴 **我们「验证即反射」=组织级 verified self-improvement 的首个工程实现——时机精确卡在概念未完成处** |
| "The Last AI Built by Humans"(2026.9 arXiv) | RSI 闭环正式定义 | 定义引用位 |

## F · 组织记忆审计(商业案例)

| 发现 | 要点 | 映射 |
|---|---|---|
| **mem0 官方卖 "Audit Trails and Governance for Enterprise AI Memory"** | 我们三臂实测的厂商自己在卖治理/审计叙事 | 🔴**验证需求商业实锤**+我们手握其压缩丢字段的技术档案 |
| 企业需求共识 | 防篡改/人机动作区分/执行层证据/EU AI Act+SOC 2 | =VerifyPack+判绩账+回执链的产品需求规格 |
| 品类移动 | 2026 企业部署驱动需求=审计链 | 品类向我们方向移动的信号 |

## 综合定位判断(喂论文主笔)

1. **论文一「智能=压缩×验证」的缝**:压缩=智能已由等价性+线性代理+真理涌现三步走完,**验证乘数无人占据**(A 线的 2603.11749 是最近邻但只到"压缩产生真理")。
2. **论文二「验证即反射」的锚**:verified self-improvement 概念 2026.9 刚被提出且未完成(E 线)——组织级首个工程实现+成本曲线(首错贵再错免费)是我们的独占证据。
3. **论文三「U 态判分器」的锚**:judge abstention 刚进学术视野(C 线 Kalai 2026)——我们领先一个生产周期(88.51%/ECE/三门/1454)。
4. **时机**:OpenAI RSI 国际标准提案(9 月)→ RSI 治理话语全球升温 → 组织级案例的发表窗口在收窄前正好打开。
5. **风险提示**:「RSI」词在安全语境有敏感性(CSA 威胁框架)——论文措辞用 verified/verified self-improvement 框架,强调"组织用验证约束自进化"(防御侧叙事),避免能力侧叙事。

## 检索缺口(诚实)

- 未深挖:B 线与 A 线的交叉文献(PRM 的压缩视角);组织记忆审计的付费价位参照;ThinkPRM 全文方法论细节
- 检索窗:部分 query 返回空(zhipu 通道质量波动),E 线补了三轮定向才命中


## 第二波补充(2026-10-01 晚 · 承用户令:更多学术业界+过往教训提取)

### G · 率失真×验证=学术空白实锤(P3 形式化的机会位)

- 检索证实:**无 2025-2026 工作结合率失真理论与验证/审计**(搜索原话"did not surface recent papers combining rate-distortion theory with verification")
- 可用形式化工具箱:[率失真感知三元权衡](https://openreview.net)(RDP tradeoff/Training-Free Traversal)+[描述统计的率失真](https://arxiv.org)(2022)+[个体序列率失真](https://pure.uva.nl)(denoising 应用)
- **P3 写作策略**:用 RDP 三元(rate-distortion-perception)扩为四元(加 verification)——「借来的时空对账」的形式化即 RDP-V 框架,空位我们自己立

### H · 记忆生产教训线(业界金矿 · 与我们过往经验直接可比)

| 来源 | 要点 | 我们的一手对应 |
|---|---|---|
| [Cleric.ai 2026.7 "LLM judge scored worse than chance"](https://cleric.ai) | 无真值+用户反馈稀疏时,**pairwise 相对评分优于绝对评分** | 🔴同题:47/47 自不一致(绝对判分崩)→三门/重放(相对锚工件)=我们的解法;可互引 |
| [Mem0 论文 arXiv 2504.19413](https://arxiv.org/abs/2504.19413)(1000+引) | 记忆抽取/巩固/检索架构正式论文 | P2 引用位+我们三臂档案(16/11/18)是它的实测压力测试 |
| [supermemory 生产迁移案例](https://supermemory.ai) | Mem0→Supermemory 生产 A/B(失败/改进/评测方法) | 业界也走对照评测路线=三臂方法论同盟 |
| [mbrenndoerfer 2026.2](https://mbrenndoerfer.com) | 显式用户反馈("remember this")=重要性真值 | **=user_verdict 导出器的设计依据**(B 线欠账的理论支撑) |
| [Incremental Multi-Turn 记忆评测](https://arxiv.org) | 隔离记忆能力与推理/规划能力 | =BC1 设计原则(只考记忆不考推理)的同构 |
| HF papers:20% 噪声下稳健 | 稀疏噪声用户反馈的鲁棒性 | T2 真值稀缺→真值三级加权的又一依据 |

**共识主题**:真值稀缺是核心问题/用户反馈稀疏但价值高/eval-before-architecture(先评测后架构)——三条全部命中我们的既定路线。

### I · 我们过往经验教训的一手数据表(论文素材库 · 全部仓内可溯)

| 教训 | 数据 | 喂论文 |
|---|---|---|
| 判分器架构天花板 | 66.2%(冻结嵌入+线性头)→88.51%(LoRA 三态),+22.3pt/ECE 0.072 | P2 异构解法主证据 |
| 同构验证三盲区 | is_correct 复写(险虚报 552 条)/特征含被检输出(开卷)/M2 等价误伤 13.8% | P2 盲区三形态 |
| 判官自不一致 | 47/47 全 void+10/10 不可复算(输入只在日志) | P2 量产证据 |
| E6 假训 | 200 步日志完成/权重零更新/六存档 md5 全同→遥测四件套 | P1 空转最纯形式+P3 反射层必要性 |
| 合成压测假绿 | v3.2 本地 175MB vs 生产 4.9G(存量未模拟)→两败一成 | P1「测试环境失真」=压缩失真的工程实例 |
| 剧场化读数 | income 自产 verdict 100%/B=0 停摆 2 月 | P1 生产实例 |
| 外部协议实测 | gtaras7 40 件:92.59% 一致/Brier 0.069/ECE 0.138(模型略过自信)/2 分歧=生成器边界 | P3 协议层+P2 U 态(2/27 主动 unclear) |
| 平台边界摩擦 | Reddit 三路/B 级授权前 0 发布→授权制后首日发布 | P1 制度反空转证据 |


## 第三波(arXiv 定向 · 2026-10-01 晚)

### J · 自我纠错批判文献(P1/P2 直接理论背书)

| 文献 | 要点 | 映射 |
|---|---|---|
| Kamoi et al. TACL 批判综述(When Can LLMs Actually Correct Their Own Mistakes) | 权威结论:内在自纠不可靠 | P1 空转的理论根 |
| **"Self-Correction Illusion"(2606.05976)** | **LLM 纠别人不纠自己**;引 Huang 2024 内在自纠常败 | 🔴与我们「开卷通道」(判分器特征含被检输出)完全同构 |
| Self-Improvements in Agentic Systems 综述(2607.13104) | 自纠机制谱系(记忆更新为主机制) | 相关工作位 |
| Self-Verification Dilemma(2602.03485) | 过度验证的抑制(经验池 test-time) | 反射层的成本侧考量 |
| 共识 | 有效自纠条件=外锚真值/工具/专门训练 | **=三门+异构验证+LoRA 专门训练的学术背书** |

### K · Reward Hacking/验证器漏洞(P2 盲区的学术大本营)

| 文献 | 要点 | 映射 |
|---|---|---|
| Reward Hacking Benchmark(Thaman 2026,20 引,2605.02964) | 钻评测过程弱点拿高分的系统测量 | P2 盲区的基准化 |
| **"LLMs Gaming Verifiers: RLVR can Lead to Reward Hacking"(Helff 2026,2604.15149)** | RLVR 导致钻奖励规格空子 | 🔴=is_correct 复写/M2 误伤的学术同型:验证器成为被 gaming 对象 |
| Verifiable PRM for Structured Reasoning(ACL 2026 Findings) | 客观验证器避神经奖励黑客 | 与我们工件锚定同路线 |
| 共识 | 可 gaming 的 proxy=失效根因 | **我们的回答:重放/复算锚定+U 态=不可 gaming 的验证设计** |

### L · 经验→权重(反射层的学术空位)

| 文献 | 要点 | 映射 |
|---|---|---|
| MUSE-Autoskill(2026.8) | Memory-Utilizing Skill Evolution 技能中心自进化 | 相关工作 |
| **"Distilling Feedback into Memory-as-a-Tool"(OpenReview)** | 瞬时批评→可检索指南,**摊销推理成本** | 🔴同方向异实现:他们文件记忆,我们权重压缩;**成本摊销概念同构** |
| DiSC/注意力蒸馏(在线持续学习) | 参数知识更新工具箱 | 形式化工具 |
| 检索证实 | **"episodic memory→weight distillation"完整组合无单篇** | **反射层(经验→25MB adapter)学术空位实锤** |

### M · 预注册×AI 评测(🔴 Assay 协议的稀缺性实锤 · 本波最重)

| 文献 | 要点 | 映射 |
|---|---|---|
| **"Position: Preregister Experiments with AI Agents"(Vaccaro et al., OpenReview)** | 倡议 AI agent 实验预注册,评"timely and important" | **我们已在生产做他们倡议的事** |
| Evaluation Cards(2606.09809) | 审计:**预注册 URL 在 AI 评测文档中"virtually non-existent"** | 🔴gtaras7 案 key-commit-先行的稀缺性=量化实锤 |
| RAND(PA3971) | pre-analysis plans=GPAI 评测金标准 | 制度背书 |
| TS-Arena(2512.20761) | 预注册平台防基准污染 | 同方向基建 |
| Max Planck Checklist 1.10 / Royal Society AI 审计 | 评测预注册检查项/时间戳第三方注册处审计 | =我们 commit 时间戳公证同构 |

**M 线结论**:Assay 协议(预注册+签封+可复算)不是工程怪癖——**是学界正在呼吁、审计证实无人生产的缺口,我们已生产运行**(预注册档体系/key 公证/VerifyPack/wall)。P3 的协议层由此从"我们的实践"升格为"对学界呼吁的首个生产回应"。
