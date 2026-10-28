# RSI grounded-retrieval 机制:外部 verdict 失败如何驱动 AI agent 不靠自改 prompt 而变强

<!--
═══════════════════════════════════════════════════════════════════════════
  这是【骨架】,不是成稿。填法:
  · 知识点列表(二)已替你列好——都是你真做过的点,可增删
  · Background Knowledge(三)每个 ◆ 子主题下的【你写:...】= 你要落笔的叙述正文
    每个 ◆ 已附「素材出处」+「可引用的真实数字」,照着回忆写,不用查不用编
  · 红线:三的叙述正文必须你亲写(买方跑 AI 检测)。我只给骨架+你自己的数据
  · 字数:三的正文合计 1000–30000 字(去空白计)。当前骨架文字不算数,填完再看
  · 写完把【】占位删干净,整篇粘进飞书「提交内容」,状态改「已提交」
═══════════════════════════════════════════════════════════════════════════
-->

**领域tag**: 工程 / AI Agent 递归自我提升(RSI)工程

## 一、Instruction
<!-- 任务描述+约束。下面是脚手架草稿,按你的口吻调整即可(这段非深度知识,可用我的草稿) -->
本任务面向「让 AI agent 系统在不修改自身 prompt 的前提下、靠外部客观反馈递归变强」这一工程场景。目标不是记住某个框架的 API,而是让模型理解:为什么内部自评式的自我提升会系统性失败、什么是可证伪的外部 fitness、如何用「失败 verdict → 结构化避坑语料 → 注入下一次产出输入」的 grounded-retrieval 闭环替代危险的「自改 prompt」、以及如何用置换检验把真增量和噪声区分开。适合构造 AI agent 工程 / RSI 方向的高质量 pre-train / instruction tuning 数据。

## 二、Knowledge Points
<!-- ≥5 条即可,已列 10 条真知识点;删到你能展开的范围 -->
- 双轮 RSI 的「半边」缺口:verdict→记忆/推送有,但 verdict→producer 能力更新缺失,导致 verdict 沦为死记录
- 三条已证伪的死路:内部 NAU 自指(94% self-loop)、ensemble/consensus、自改 prompt(单调退化)
- grounded-retrieval ≠ self-modification:改的是注入给 producer 的输入,不是 producer 自己的 prompt
- fitness 必须外部(QC pass / 买方接收 / 客观 reward),为什么内部自评必然塌缩
- 一个 verdict 的三层粒度:题级 score / agent 级 pass 率 / 内容级 per-item reason
- 最小可度量 4 步闭环:fail_reason → 避坑语料 → retrieve 注入 grounding → 下一轮度量
- escapes_noise 门:two-sample 置换检验 + ΔReward>0 且 p<0.05 才算真增量(防给噪声发奖励)
- speed-vs-correctness 权衡:激进优化提速但破坏正确性,正确性门=0 拖垮均值
- 守纪律的科学弧:诚实负结果 → 机制诊断 → 预注册迭代(区别于 p-hacking)→ 确认
- gated build 纪律:不为尚不存在的正信号建表,escapes=True 才落地数据通道

## 三、Background Knowledge
<!-- ↓↓↓ 每个 ◆ 下的【你写】= 亲笔正文。多段展开,每段含权衡/局限。素材出处帮你回忆,数字是你的真实验结果可直接引用 ↓↓↓ -->

◆ 1. 为什么需要外部 fitness:三连负教训
   素材出处:design `docs/plans/2026-06-05-rsi-fde-closed-loop-design.md` §2;memory truth_real_bucket_460_94pct_self_loop
   可引用的真事:内部 NAU 自指被实测是 94% self-loop;ensemble/consensus 范式 A 三连负;
   benchmark 弧反复证伪「靠自己评自己变强」。
   【你写:讲清楚你为什么从「内部自评」彻底转向「外部 ground truth」——这段是整篇的动机基石,
    把你亲历的失败说出来:自指经济为什么必然塌缩,什么叫"能诚实证伪自己"的尺。】

◆ 2. 核心机制:grounded-retrieval 4 步闭环
   素材出处:design §3–§4(4 步图);memory session_20260608_rsi_grounded_retrieval_soul_half_built
   可引用的真事:① soul QC 出 per-item fail_reason ② compass 把 reason 转避坑语料(bge-m3 可检索)
   ③ v5 producer 下一题前 retrieve 相关避坑规则、注入 task grounding(硬约束输入)④ 下一轮 verdict 度量。
   【你写:逐步讲这 4 步,重点说清「改的是输入不是 prompt」这个分水岭——为什么这避开了 Probe3
    那种自改 prompt 的单调退化(0.333→0.20→0.00)。讲 grounding 的正向来源=真 veto reason,非盲改噪声。】

◆ 3. verdict 的三层粒度
   素材出处:memory session_20260608...soul_half_built 第 16 行;fde_verdicts.items schema
   可引用的真事:一个 verdict 同时含 题级 score(compass 用)/ agent 级 pass 率(v5 用)/
   内容级 per-item reason(此前没人用=要复活的死记录);items=[{id,pass,veto,reason}]。
   【你写:讲为什么前两层都丢了 reason 文本,而 reason 才是 RSI 的燃料;粒度错配如何让信号白白流失。】

◆ 4. 度量方法学:two-sample 置换检验与 escapes_noise 门
   素材出处:memory ...soul_half_built 续2–续7;benchmarks/grounding_probe.py
   可引用的真事:首验形状=N 独立裸 vs N 独立 grounded=两样本,用配对统计是虚假配对(方法学坑,你亲自发现);
   改用精确置换检验(itertools.combinations);N≥5/臂否则 C(4,2)=6→min p=0.167 永不显著;
   escapes_noise=True ⟺ ΔReward>0 且 p<0.05。
   【你写:讲为什么必须有这道门——不设门就会给噪声发 PoI 奖励(self-referential PoI 病)。
    讲两样本 vs 配对的统计区别、N 的功效要求,这是别人搜不到、你踩过坑才懂的细节。】

◆ 5. 实证科学弧:从诚实负到 escapes=True
   素材出处:memory ...soul_half_built 续4 / 续6 / 续7;memory session_20260610_soul_cycle_b
   可引用的真事(全是你的真实验数字):
   · round-1 N=10:ΔReward −0.0607,escapes=False(激进优化 prefetch/SIMD,4/10 破坏正确性)
   · 诊断=speed-vs-correctness 权衡,避坑语料过度推优化欠推保正确性
   · round-2 correctness-first 修正:全分布 +0.0174 仍不显著,但 correct 子集 9v9 p=0.0010
   · round-3 confirmatory 全分布:bare 0.1835 / gv2 0.2568,ΔReward +0.0734,p=0.0215(10.4M 置换),escapes=TRUE
   · = 5–6 周首个有外部验证的真 RSI 增量(单题 radix_sort)
   【你写:把这条弧讲成一个完整故事——负结果不是失败而是信号、怎么诊断出机制、
    为什么 round-2/3 是预注册迭代而非 p-hacking(效应双指标同向+机制显著+无选择偏差)。
    诚实标 scope:单题 radix_sort,非"RSI 普遍成立"。这段是整篇最有价值的部分。】

◆ 6. 工程落地与纪律
   素材出处:design §5(四系统分工)/§7(红线);memory ...soul_half_built 续8(fde_rsi_deltas)
   可引用的真事:soul(fail_reason)/compass(避坑语料)/v5(retrieve 注入)/平台(verdict-bus)四分工;
   gated build=不为不存在的正信号建表,escapes=True 才 build fde_rsi_deltas 表 + PoI 订阅 escapes_only feed。
   【你写:讲为什么"先有信号再建管道"是纪律而非偷懒,讲红线(fitness 永远外部、绝不自改 prompt、
    绝不消费 escapes=False)如何防止重蹈 94% self-loop。】

## 四、Task示例
<!-- 输入/执行/结果三要素,描述一个真实可复现的最小任务。下面是骨架,数字是真的,叙述按需补 -->
**输入**:给定一道客观可自动打分的难题(radix_sort CUDA kernel,baseline 4.5s→reward 0、ref 0.35s→reward 0.5,log-stretch),已有 N=10 条「裸」候选的 reward 分布,以及一条从失败轨迹提取的避坑规则(correctness-first:只做安全优化 prefetch/restrict/8-bit ping-pong,禁致错的 combined-scan/SIMD)。要求度量「注入该避坑规则后,下一轮产出是否真的变好」。

**执行**:retrieve 避坑规则 → 注入 producer 的 grounding 输入 → 产 N=10 条「grounded」候选 → 客观 eval 出 reward → 跑 `grounding_probe_twosample(bare_rewards, grounded_rewards)`(精确置换检验,单边)→ 读 ΔReward / p / escapes_noise。

**结果/答案**:全分布 bare 0.1835 / grounded 0.2568,ΔReward +0.0734,p=0.0215(10.4M 精确置换),escapes_noise=TRUE。判决=穿过预注册门,第一个有外部客观验证的真 RSI 增量。诚实 scope:作用域=单题 radix_sort,效应双维=可靠性(92% vs 69% correct)+ 速度;非"RSI 普遍成立"的声明。
