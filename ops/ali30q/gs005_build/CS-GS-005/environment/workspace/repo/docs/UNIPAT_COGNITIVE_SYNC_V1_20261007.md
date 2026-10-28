# unipat 认知对表 V1(2026-10-07 · 用户令:历程回顾+全网调研+框间同步+产物方案)

> 方法:发展历程凝练→学界业界四路调研→与我们三环资产对表→产物与方案。全部带源,分级标注(实测/据报道/待核)。

## 一、发展历程凝练(我们的路径,一周内完成了行业常规一季的路)

组织 agent 终极目标(8/30 定性)→组织 OS 优先(9/12)→RSI 核心+沉淀机制(10/4)→**北极星 unipat-in-agent:agent harness 一站式"基准评测→能力提升"(10/4 深夜)**→产品化五判据倒逼(10/5)→全框收敛两外壳(10/6)→CUDA 生态位+BYZ 治理协议(10/6 晚)→开业链(10/12)→PMF 首笔(10/31)。
已实证资产三环:①评测判读体系(判据 sha 预注册+四验门+NACRE 判分模型 88.51%)②真实任务数据飞轮(池 155 行判分-结算绑定)③训练闭环(SFT/GRPO+E1 复考锚,负结果照报纪律)。

## 二、学界最新(四条,2025-12~2026-09)

1. **SWE-bench Science(arXiv 2026-09)**:科学软件域 119 任务/98 仓库/20 域,**最强 agent(Claude Code+Opus-5 max)<50% pass@1**,并提出四类失败分类学 → ①直接证实我们"瓶颈在 harness 不在模型"的北极星判断;②失败分类学=我们 S3 负样本判因字典的学术对表对象;③科学域评测集=unipat 扩榜候选域。
2. **SWE-EVO(arXiv 2025-12)**:评测从"静态单点修复"转向"持续软件演化" → unipat 评测集 V2 的方向锚(与静态 SWE-bench 差异化)。
3. **ET-Agent(arXiv 2601.06860,2026-01)**:"Self-evolving Data Flywheel+行为校准训练"(Pareto 采样+课程式 RL) → 与我们涡轮增压机制同构(学界平行验证);训练侧方法论可直接借入 B7/GRPO 迭代。
4. **NeoHorse-1(2026-09,HF 日榜 ~134 赞)**:基元律动(王云鹤,前盘古负责人),4B/9B,"harness-native data flywheel"+Agentic Routing 递归自我改进 → **战略双重信号(10/7 用户指正修正)**:我们组织自己就在做这件事(v5 涡轮增压闭环=自家 harness+模型 RSI 实践,组织终极目标)——NeoHorse 是同路先行者非竞品;我们的真差异化=飞轮燃料带**第三方判据层**(判据 sha+不可写面+held-out+E1 公开复算),防"自我评估作弊"正是 RSI 最稀缺层;行动=邀 NeoHorse 系上榜被测(给同路人独立验证)+两外壳区分段改为"带第三方判据的自进化飞轮"叙事(原"卖水 vs 喝水"二分撤销)。另有 SkillRL(ICLR 2026)与 ICLR 2026 RSI Workshop(社区成形,unipat 投稿候选)。

## 三、业界最新(三条)

1. **评测工具市场有死亡案例**:Humanloop 2025-09 关停;存活者 Braintrust(eval-first 定位)/LangSmith($39/月起)/Langfuse → 它们做"开发者调试用 eval",我们做"独立第三方判分+数据商品"——差异化=中立性(判据 sha+不可写面)+数据资产;可借:trace/回归测试视图进我们榜单页。
2. **定价坐标**(2026 实测):consumer $20-50/月,business $50-200/月/席,**enterprise $10K-40K/年**(Synthflow 企业-only $30K/年) → 我们 L2 $199/次 L3 $999 起在坐标系偏低;方案:10/12 后 L3 试"年度委托制 $10K 起档"。
3. **企业采购趋势**:企业 AI 工具普遍 $10-40K/年+席位制 → Wave2 海外直邮(Factory/Cursor/Cognition)正文可引用此预算带,把 $199 定位为"入场级"。

## 四、产物与方案(并入死线链)

| # | 产物/方案 | 责任 | 窗口 |
|---|---|---|---|
| P1 | 两外壳补"学界对表"段(SWE-bench Science 四类失败分类学引用+NeoHorse-1 生态位区分段) | platform 装订+compass 术语核 | 18:00 呈批窗 |
| P2-① | NeoHorse-1 查重与叙事区分函(函 compass/v5:我们的判分中立性 vs 其自训练,勿混淆) | platform | 24h |
| P2-② | 榜单页加"失败分类学对表"引用(借学术背书) | v5+platform | 10/12 前 |
| P3 | 评测集 V2 立项评估:演化式(SWE-EVO 方向)+科学域(SWE-bench Science 119 任务候选) | compass 主笔评估函 | 10/20 前后 |
| P4 | L3 定价实验:年度委托制 $10K 起档 A/B | platform+用户拍 | 10/12 后 |
| P5 | unipat 学术投稿候选:ICLR 2026 RSI Workshop(榜单+负结果纪律=论文素材) | compass/v5 合笔评估 | 10/20 前后 |
| P6 | 训练侧:ET-Agent 方法论(Pareto 采样/课程 RL)供 B7/GRPO 迭代对表 | v5 | W2 |

## 源
- SWE-bench Science:[aiweekly](https://aiweekly.co)/[arXiv](https://arxiv.org)/[opentrain](https://opentrain.ai)
- NeoHorse-1:[arXiv](https://arxiv.org)/[HF 日报](https://www.htx.com)
- ET-Agent:[arXiv:2601.06860](https://arxiv.org/abs/2601.06860)
- SkillRL:[ICLR 2026](https://iclr.cc);SWE-EVO:[arXiv 2025-12]
- Humanloop 关停:[promptforge](https://promptforge-app.com);LangSmith 定价:[softwr](https://softwr.com);定价带:[taskade](https://www.taskade.com)/[cloudtalk](https://www.cloudtalk.io)
