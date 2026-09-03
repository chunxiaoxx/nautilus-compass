# Paper 2 融合版大纲 · 判官失效分类学与判分卫生学

> 2026-09-04 立项(用户拍板排序①)。融合 kimi 5 月稿(`verification-learning-papers/papers/paper2_judge_blindspot.tex`,数值精度盲区,398 行)+ compass 9 月三组第一手实证。
> 写作模式:LOOP 每轮一节,写完即 commit。arXiv 提交动作等用户拍板。

## 0. 定位

- **标题候选**:`Judge Failure in the Wild: A Taxonomy of LLM-as-Judge Breakdown and a Hygiene Protocol for Long-Memory Evaluation`
- **一句话**:判官失效不是单一偏差而是一族结构失效;我们给出三分类(知识边界盲/预算盲/连接盲)、每组一手实证、以及一套可操作的判分卫生学协议(重判退避+双口径披露+预注册锚)。
- **与 5 月稿关系**:5 月稿的数值精度盲区成为分类学第一类(知识边界盲)的一等公民证据,不是被推翻而是被收编。
- **差异化护栏**(related work 已有 judge bias 批评,我们的增量):
  1. 成因分类学——三类失效机理不同、解药不同,混谈会开错药;
  2. 生产级管线临床案例(非合成扰动实验):14% 题被错杀、整体分数被压 5.4pt;
  3. 处方而非诊断:卫生学协议+检查清单,可直接套用。

## 1. 三类失效 × 证据映射(主表)

| 类 | 机理 | 一手证据 | 数字 | 解药 |
|---|---|---|---|---|
| ① 知识边界盲 | 判官对超出自身知识边界的内容结构性失明,非能力差距 | kimi 5 月实验:2600 真实 API 调用,Kimi k3 + MiniMax-M3 两家族;±0.1% 扰动放行 37-48%、±1% ~13%、±10% 0%;Δ 信号(9.7/5.3/2.3→0%/45%/13%)单调预测 | 盲区边界稳定在 0.1%-1% 相对扰动,跨家族差 <11pp | grounding(程序化接真值);Δ 作部署前预测子 |
| ② 预算盲 | 判官推理预算被吃满,输出被截断→系统性偏判 | compass d13:LME-V2 doubao judge max_tokens 4096 被 reasoning 吃满→判分系统性压 0;两连崩教训=函数调用级冒烟才暴露 | 修复前 ent 域判分不可用(系统性压 0) | 预算审计+判官输出冒烟(部署时检查,非事后) |
| ③ 连接盲 | 判分基础设施故障被计为"答错",错误静默混入分数 | compass e2e 9/3:71/500 题(14.2%)judge 断连(newapi glm 间歇 403)被计错;三口径 0.700(保守)/0.754(重判定案)/0.816(剔除);同判重判修复 | 断连规模=被测系统提升量(+32.8pt)的一半 | 重试退避重判(同 judge 同 prompt)+双口径披露规范 |

## 2. 章节骨架(约 9-11 页)

1. **Introduction**——judge 范式三大失效场景;贡献三条(分类学/临床证据/卫生学协议)
2. **Related Work**——judge biases(可纠正的表面偏差 vs 我们的结构失效);eval 可复现性;LLM-as-Judge 元评测。5 月稿 Related Work 骨架可复用,加 2026 新文献
3. **A Taxonomy of Judge Failure**(核心理论节)——三分类形式化:失效面=判官知识边界∩输出预算×基础设施可靠性;每类的可检测信号
4. **Evidence I: Knowledge-Boundary Blindness**(5 月稿实验全节收编,数据已有)
5. **Evidence II & III: Production-Pipeline Cases**(compass 两案例;d13 预算盲+e2e 连接盲;含三口径披露方法学)
6. **The Hygiene Protocol**(处方节)——①预注册锚与三态判定 ②断连题重判退避(算法框:同 judge 同 prompt 仅重试,30/31 修复)③双口径披露规范(保守/重判/剔除三口径并报)④判官部署冒烟(预算+连通性)⑤卫生检查清单(表格,可撕下即用)
7. **Discussion**——对"更强判官"范式的 refine;与自改进系统空转(Paper 1)的关系;评测基础设施建设即科学贡献
8. **Limitations**——两域基准(LongMemEval-S 500 题+LME-V2 451 题);判官家族覆盖;断连根因在 newapi 侧不可控
9. **Ethics/Reproducibility**——上游 attribution(451 题=xiaowu0162 官方基准,我们只做调优与判分)、数据与脚本开源路径

## 3. 素材索引(写作时直接取)

- 5 月稿全文:`C:\Users\chunx\Projects\verification-learning-papers\papers\paper2_judge_blindspot.tex`(中文版同目录)
- 价值盘点:`...\docs\全程论文价值盘点.md`(判官盲区=A 档,93-100% 放行表述出处)
- e2e 定案:`vtf/_e2e_diag/arm_a_final_verdict.md`(三口径数字+重判方法)
- 重判脚本:`tools/rejudge_errors.py`(31/31 修复,算法框素材)
- d13 案例:memory `d13-judge-retry-verdict-20260831.md`+LME-V2 三刀文档
- 判分协议:T0-5 定版 v1.0(task #32 产物,协议节素材,与 #34 T0-7 共用)

## 4. 诚实边界(写进论文的红线)

- e2e 与 LME-V2 成绩均为**自家判分口径**,论文主张是"判分卫生学"而非刷榜;主表数字全部三口径并报
- 451 题基准=上游官方(xiaowu0162/Di Wu),attribution 章节显式写;我们贡献=调优+判分协议
- 断连根因(newapi 间歇 403)是基础设施事实,不指名羞辱服务商,写"intermittent gateway failures"
- ssp -5pt 这类小样本波动必须带二项噪声带(n=30 时 ±1 题=±3.3pt)

## 5. 写作计划(LOOP 每轮一节)

| 轮次 | 产出 | 依赖 |
|---|---|---|
| R1(本轮) | 本大纲 | — |
| R2 | §3 分类学(理论核心,先写难) | 5 月稿 Related Work |
| R3 | §4 Evidence I(收编 5 月实验) | R2 |
| R4 | §5 Evidence II&III(compass 两案例) | R2 |
| R5 | §6 卫生学协议(处方) | R4 |
| R6 | §1 Intro+§2 Related | 全部证据节 |
| R7 | §7-9+Abstract,全文合稿互审 | R6 |
| 提交 | arXiv(等用户拍板;同步刷 #34 T0-7 决策材料) | 用户 |

## 6. 协同

- **9/12 营销帖**:判分卫生学叙事提前背书(三口径披露=诚实卖点)
- **#34 T0-7 judge 口径决策材料**:与本论文 §5/§6 同素材,一次写作两用
- **成绩册 #31**:判分协议章节引用本论文(预印本即可)
- kimi 三篇总排序不变:paper2(本篇,9 月)→ compass 系统 2.0(10 月)→ paper1 验证学习(Q4,等 T2 数据)→ paper3 元理论(降级博客)
