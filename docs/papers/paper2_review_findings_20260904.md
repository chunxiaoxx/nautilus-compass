# paper2 独立评审意见清单 · 2026-09-04(三视角:审稿人/数字对账/伦理)

> 流程:用户 9/4 指出"未见过论文、无审核、不应谈提交"后启动。融合缝审查 agent 因环境无
> 文件工具失败,其检查面(记号统一/结构对齐)由审稿人报告部分覆盖,修订时补自检。
> 注:数字对账读的是 GitHub main 版(早于本地两处未推 commit:标题 Draft 尾巴+作者栏
> Anonymous→Chunxiao Wang),内容审不受影响。

## 总判(合并)

**修后可发,当前不可提交。** 4 个 P0(1 个击穿匿名化、2 个论证承重墙缺数据/逻辑错、
1 个数字无源)+ ~15 个 P1。好消息:数字对账确认 e2e 线已用 9/4 定案口径(0.700/0.754/0.816
链自洽,agent 独立复算通过)、LME-V2 线与 d13/d14 定案吻合、时间线无过时数字。

## P0(4)

1. **[伦理] L184/L320 点名 "a Doubao judge"** — 击穿 §9 自述的厂商匿名策略,自相矛盾
   (Case 1 点名还间接给 Case 2 的"某网关"消匿名)。修:两处改 "a commercial
   reasoning-mode judge (vendor anonymized)";理论实验的 Kimi k3/MiniMax-M3 属公开基准判官可留。
2. **[审稿人] "prompting does not help"(L174-177/L101-102)无消融数据** — 这是"结构性失效
   vs 可纠正偏差"定位的承重墙,§4 没有给出"明确指示核对数值"消融条件的通过率。仓内
   (verification-learning-papers data/ 仅 3.3KB)大概率无此数据。修(降格路径):改为
   "我们试过的 N 个指令变体无效"并列出试了什么;若能补消融实验则升格(见 P1-补实验)。
3. **[审稿人] Δ "monotonically predicts"(L172-173)与自身数据矛盾** — Δ 映射
   9.7→0%/5.3→45%/2.3→13%/0.8→0% 是倒 U 型非单调;仅 4 个样本内点;用被评测判官自己算
   Δ 再预测该判官=循环论证;§6.2 Δ≈6.2-7.0→0% 进一步破坏单调。修:删 "monotonically",
   改"单峰/分段带预测器,盲区在中带",如实标注 in-sample 局限,held-out 验证留待后续。
4. **[数字] "31/31" 四处(L37/204/342/396)无源** — 真值权威句="71 题断连全部重判补齐"
   (arm_a_final_verdict.md:3)。修:31/31→71/71(四处);若 31 另有分解出处需先举证,否则按 71。

## P1(合并去重)

5. 无 COI 声明(§9)——加:§5 生产设施由作者雇主运营、协议为该系统开发并采用、无判官/网关
   供应商参与本工作(建议措辞见伦理报告)。
6. LongMemEval-S 与 LME-V2 零正式引用,但 §9 声称 "attributed to original authors"——
   补两条 bibitem+首次提及处 \cite+注明 upstream maintained。
7. arXiv:2608.02620 引作 "Anonymous (2026)" 实为 **JudgeArena 七人实名**(Lushtaku et al.,
   CC-BY 4.0)——改实名条目;另一条 Anonymous 是未发表 companion paper 1,标注 unpublished。
8. 计数打架:摘要 "five-item protocol" vs 引言 "six routines" vs Table 3 六行——统一口径。
9. "a fifth"(L59-60)算术:5.4/32.8≈1/6——改 "one-sixth" 或改写;顺带补 0.816-0.700=11.6pt。
10. −5pt vs ±3.3pt(L349-351):5pt>±1 题带,自证失败——改配对完整二项带或 ±2 题;真值文件
    同句一并修(算术瑕疵继承自 verdict)。
11. Table 2 全线无置信区间,与 P5 自己 preach 的噪声带原则矛盾——每格加 Wilson 区间
    (n=100 下 0.48 vs 0.37 的两族差在 CI 内,正文声明要相应收敛:"invariant across judge
    families"→"stable across the two tested families, ≤11pp")。
12. P3 三口径只有 overall 无 per-subtype 表,而"幻影 −20pt 回退"恰发生在亚型层——补
    per-subtype 三口径 gate 表。
13. "retry actively harmful"(L72-74)过强——改"无口径纪律的 retry 有害"。
14. J-B 案例零量化(§5.1):无截断条目占比/修复前后分数——仓内 d13 有现成数据
    ("empty response content" 250 次风暴/146 题零分)补入;顺带补终修配置
    (16384+reasoning low+156 题重判,防"加大 max_tokens 即治愈"误读)。
15. 断连率外部效度:14.2% 是单网关单时段——Limitations 加一句 not an industry estimate;
    有条件则补自家历史各 run 断连率分布。
16. artifact bundle 无链接/DOI 且不覆盖 Evidence I(2600 调用语料/probe/Δ 代码)——扩释放
    清单+具体落点;不释放部分明说。

## P2(择要)

17. 上游许可一句(逐题判分输出内嵌上游题目文本,再分发合规性)。
18. Evidence I 判官无版本/访问日期(生产案例已给时段,理论实验补齐同规格)。
19. 时间线 "August–September 2026"(L146) vs "during September 2026"(L311) 统一。
20. "resolved 31/31"→改后加半句 resolved≠correct(全程净翻正 27/71)。
21. Table 1:J-C "Pre-deployable: yes" 与间歇性矛盾→改 in-run;J-B 方向注明由 default 极性定。
22. 分类学接文献:Avizienis 2004 dependability / Dean & Barroso tail-at-scale / Manski 界,
    novelty 收窄为"首次系统搬到 LLM-judge 评测管线"。
23. Proposition 1 改 "Empirical Finding"(无假设无证明)。
24. 标题 "for Long-Memory Evaluation" 限定与 J-K 通用性张力——去限定或说明迁移性。
25. L65-67 "sub-percent" 措辞:±1% 非 sub-percent,37-48% 只在 ±0.1% 档。
26. tex 头注释含内部决策痕迹,随 artifact 发布前剥掉。
27. 温度混杂(Kimi 1 vs MiniMax 0.3)未说明——统一或给理由。

## 第四视角补充(融合缝自检 · 主对话执行 · 2026-09-04)

- **N1[P0 精化] 两条"单调"必须拆开**:骨架原稿同时声明 ①ρ_J(δ) 对扰动幅度 δ 单调
  递减(骨架 L89,数据支持:37-48%@±0.1%→13%@±1%→0%@±10%,**保留**)②Δ 对通过率
  单调预测(骨架 L37/L51/L119,数据不支持:Δ=9.7→0%/5.3→45%/2.3→13%/0.8→0% 为倒 U,
  **删除/改单峰**)。融合版把两条都继承了(L172/L254/L301)。修 P0#3 时按此拆分,不要一刀切。
- **N2[P1] 匿名纪律不一致的根源**:骨架(理论节)匿名纪律严格,新写案例节(§5)松——
  "Doubao" 点名正是案例节带入。修订以骨架纪律为准全文统一。
- **N3[P1] 摘要 "clinical evidence"(L33)overclaim**:医疗词暗示受控实验,而 J-B/J-C
  是单厂商事故叙事——改 "production evidence"。
- **N4[P2] "invariant across judge families"(摘要)继承自骨架 abstract 未收敛**——
  与 P1#11 一并改 "stable across the two tested families (≤11pp)"。
- **记号核对 ✓**:δ(v,v*)/Δ(k)/δ_c 三组定义融合无丢失无漂移(骨架 L71/L115/L99 vs
  成品 L243/L299/L257 同式);骨架 Scope Limitation 节在成品 §Scope 保留 ✓。

## 修订工作量估计

- 文字修(P0-1/3/4 + P1 全部 + P2):一个专注日,不需要新实验。
- 需要数据回仓的:J-B 量化(#14,d13 现成)、per-subtype 三口径表(#12,per_question 现成)、
  历史断连率分布(#15,需查多次 run 记录)。
- 可能需要新实验的(可后补/降格):prompting 消融(#2)、Δ held-out(#3)、温度统一(#27)。
