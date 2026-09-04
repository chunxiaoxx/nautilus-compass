# paper2 审阅包(导读+成熟度现状)· 2026-09-04

> 背景:用户指出论文从未见过、无独立审核,不应直接谈提交——本件即审阅入口。
> 论文本体:`docs/papers/paper2_judge_hygiene.tex`(约 3800 词源码)/ `paper2_judge_hygiene.pdf`(9 页,240KB)。

## 一、这篇论文是什么(一段话)

《Judge Failure in the Wild: A Taxonomy of LLM-as-Judge Breakdown and a Hygiene Protocol for
Long-Memory Evaluation》——LLM 判官在生产管线里的失效分类学 + 判分卫生协议。理论骨来自
verification-learning-papers 的"判官盲区"(数值精度盲点定理,2600 次真实 API 调用),
案例骨来自 compass 自家 LME-V2/e2e 评测线的一手事故(判分预算被 reasoning 吃满→系统性压 0;
judge 网关断连→14.2% 题目被误判;401 鉴权静默失败)。是 kimi 论文②的"实身"。

## 二、结构(9 节)

| 节 | 内容 | 证据来源 |
|---|---|---|
| §1-2 Intro/Related | bias 文献只讲可纠正偏差,我们讲结构性失效 | mtbench/verbosity/self-enhancement 等 12 条文献 |
| §3 分类学 | J-K 知识边界盲区 / J-B 预算盲区 / J-C 连接盲区 | — |
| §4 Evidence I(J-K) | 数值精度盲点:±0.1% 扰动通过率 37-48%,单调衰减,Δ 预测子 | kimi 2600 调用实验(papers 仓 data/) |
| §5 Evidence II/III(J-B/J-C) | 案例1:4096 预算被 reasoning 吃满(d12/d13);案例2:71/500 题断连=5.4pt 失真 | 本仓 vtf/_compass_lmev2_out 定案报告 |
| §6 卫生协议 P1-P5 | 预注册锚/同判官重试退避/多口径披露/判官冒烟/二项噪声带 | 本仓 PROTOCOL.md+rejudge 工具 |
| §7-9 Discussion/Limitations/Repro | 边界+伦理(服务商不指名) | — |

## 三、已做过的检查(机械层,非内容审)

- [x] 编译两遍收敛 0 错 0 undefined;摘要 1469 字符<1920;零图零外部依赖
- [x] 12 条文献逐条 WebSearch 验证(纠 3 处)
- [x] 摘要/正文数字三处对齐(14.2%/71 题/5.4pt/32.8pt)
- [x] 诚实边界落稿:三口径并报/451 题上游 attribution/服务商匿名("intermittent gateway failures")

## 四、没做过的(审核缺口——提交前必须补)

1. **用户通读**(你还没见过论文本体)
2. **独立评审**(paper1 当年有正式 Readiness Audit;paper2 零):novelty/主张-证据匹配/
   融合缝(理论节 vs 案例节风格)/伦理匿名化措辞
3. **已知疑点待审**:§523 引 "Anonymous (2026) arXiv:2608.02620"(引匿名文献是否站得住);
   案例全部自产自报(单厂商外部效度);J-K 实验判官仅两族(Kimi k3/MiniMax-M3)

## 五、审核流程(提议)

你读(本导读+PDF)→ 独立评审轮出意见清单 → 修订 → 终审拍板 → 才进入提交流程。
提交时机以审核质量为准,不再绑 9/12。
