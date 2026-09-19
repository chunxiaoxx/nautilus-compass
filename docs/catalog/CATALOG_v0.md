# CATALOG_v0 · 判据库 v0(2026-09-15 立库)

> 定位:compass 侧判据正本,与平台理论总账条目级 trace_id 双向互锚
> (格式 `criteria:<id>@catalog-v<n>`,platform 回函 id 232 认)。
> 条目来源:每次复算/预注册产生;首批评测见
> [[../platform/pilot_verifypack_10verdicts_20260915.md]]。
> 纪律:判据只许更严(棘轮,GOAL_STACK v3 纪律二同构);条目变更加 Updates 区。

## 条目

### criteria:verdict-recomputability-v1@catalog-v0
- **定义**:verdict 行可复算 ⇔(输入在行内或可由稳定指针解析)∧(items
  非空且含判据依据)∧(声称 score 可由所存 artifacts 推出)。
- **来源**:10 条 fde_verdicts 试点(9/15),首读 0/10。
- **测量法**:SELECT 行 → 逐条件核 → 三态(可复算/半可复算/不可复算)。

### criteria:external-verified-provenance-v1@catalog-v0
- **定义**:external_verified=true 只能由外部复算者复算后回写,须带 verifier
  身份+时间戳;生产者只可置 false/NULL。
- **来源**:同上试点,8/29 批违例 10/10(标志在无证据行上为 true)。

### criteria:evidence-schema-v1@catalog-v0
- **定义**:执行元数据自洽(多模型判分 ⇒ total_tokens>0;turns 与产出非零
  一致等)。
- **来源**:同上试点,违例 10/10。

### criteria:anchor-pool-selection-bias-v1@catalog-v0
- **定义**:校准/闸门所用的"锚池"必须以**历史合格批(hold-out/验收过条目)**语义
  构建;不得以"未验证的剩余候选"充当真值锚——批次越精选,剩余池分布越偏,
  锚越歪,离群假阳性被系统性放大。
- **来源活例**:flywheel sim50-001 闸③ 68% 离群三组对照归因(批内自锚 6.4%≈
  设计线 vs 生产池 68.1% vs 同构成 80.9%)——根因=选择偏差传导,非数据问题。
  归因正本:flywheel 仓 docs/plans/2026-09-15-闸③校准归因-锚池选择偏差.md
  (G1 盲区理论第 N 活例:锚=分布假设,假设错秤就歪)。2026-09-16 compass 注册。
- **测量法**:三组对照(生产池/批内自锚/同构成池)离群率对比;规则无罪判据=
  批内自锚离群率回到设计线。

### criteria:judge-systematic-inconsistency-v1@catalog-v0
- **定义**:判定器对同批样本的交叉/复测输出若出现**全量不一致**(一致性
  矩阵对角命中率显著低于随机基线),判为判定器系统性偏差,**整批判废**——
  该批任何读数不得引用为校准/评测依据;修复判定器后重产,无"部分可用"通道。
- **来源活例**:flywheel X1-v2 判定 47/47 全不一致→作废(flywheel 仓
  8aac2f5);同案作为 C4 声明进入 C 族首批校准包(c_family_calib_b1,
  "三检测零基线 47/47")。2026-09-16 compass 注册(同日回函 v5 id 298)。
- **测量法**:批内一致性抽检——构造判定矩阵,对角命中率 < 随机基线
  (1/类别数)即触发。

### criteria:longhorizon-l1-commit-clearance@catalog-v0
- **定义**:承诺清账率 = consumed 链 / intent 链(7 日滚动窗);链判定 = 同日
  state 迁移追加行(kind=result/consumed)归一条链。
- **来源**:v5 注册提交(358 函,2026-09-17),compass 审通过。失真源披露:
  9/16 前 consumed 恒 0(销账断头已修),baseline 只取修复后。
- **测量法**:复核者持 jsonl 切片+公式重算,零隐藏状态(ρ 高);观察窗转执法
  (连续 14 日 ≥70%)那一刻的 Δτ 须附证据链。

### criteria:longhorizon-l2-lookup-without-consume@catalog-v0
- **定义**:waste = 1 − Σconsume(配对[q]) / max(lookup(q), Σconsume);
  **配对表属 m 的一部分**,表变更 = ρ 修订须证据链(防"改表洗白 waste")。
- **来源**:同上;首跑活体证据自证(9/16 pf_task_detail 181 查 0 消费)。
- **测量法**:配对表 v1 冻结随注册(pf_task_detail→pf_score_bounty|pf_submit_bounty;
  pf_list_bounties→pf_claim|pf_post_bounty);辅证 B 案(报警轮占比)交叉不裁。

### criteria:longhorizon-l3-funnel-layering@catalog-v0
- **定义**:平台行为四层计数(发起=breath cycles/执行=selector 行/落账=outcome
  ok/消费=下游真验收),相邻层比 <50% = 断层层。
- **来源**:同上;**消费层首月读数自标 UNVERIFIABLE 上墙**(复算路径未通,提交方
  主动申报——宁缺勿滥纪律的执行样本)。
- **测量法**:platform_audit 只读导出(平台 320 函确认通道)。

### criteria:adversarial-window-picking@catalog-v0
- **定义**:证据纯净性攻击——被测方手工挑时刻跑汇流压低纸面计数。判据:重跑差
  >50% 且时刻<22:00 即 flag。
- **来源活例**:v5 对抗样例 V1(372 函,2026-09-17),正本 nautilus-v5/docs/
  ADVERSARIAL_SAMPLES_V1_20260917.md(commit c3d24a2)。
- **测量法**:同一汇流窗口独立重跑对照。

### criteria:adversarial-status-hiding@catalog-v0
- **定义**:状态语义攻击——把病灶标成 falling/watching(消退中)即可踢出消费队列
  绕过复验。判据:**判分器独立重算轨迹,不信工单自带 trend 字段**。
- **来源活例**:同上(实证 9/17,存续 36h,修复 e9f973a)。

### criteria:adversarial-fake-success@catalog-v0
- **定义**:异步壳攻击——fire-and-forget 后 LastTaskResult=0 掩盖下游崩溃。
  判据:声称完成时刻 vs 产物 mtime 双源对账。
- **来源活例**:同上(实证 9/15 23:30 汇流崩而任务状态全绿)。

### criteria:adversarial-attribution-drift@catalog-v0
- **定义**:归因漂移——结构病报成模型病(或反向)骗修法预算。判据:「模型病」
  结论必须挂 harness 四查清单,否则降级未归因。
- **来源活例**:同上(实证 9/17 用户当场纠偏)。

四条共同原则(对抗库第一性):**判分器独立重算,不信被测方自带的状态/结论字段。**

### criteria:skip-label-fidelity@catalog-v0
- **定义**:verdict 行携带的 skip/fail 病因标签必须可被独立重跑复现(结局与病因
  双保真);结局一致但病因标签不复现(如标 fixture_broken_red 实为无红)=标签失真,
  记 degrade 不记 agree。
- **来源活例**:10 verdict 复算(2026-09-18,agent 执行主会话审定):f08c/d821
  两行标签不复现(结局同向);x8f1d 精确复现。
- **测量法**:worktree 重跑复现标签描述的故障形态,比对结局+病因。

### criteria:paradigm-corroboration-chain-v1@catalog-v0
- **定义**:归因纪律——当独立外部范式文献 ≥5 次收敛于同一命题(当前命题:
  "瓶颈在标注数据与阈值调校,不在模型能力")时,组织内归因分析应**优先检查
  数据层与判据层**,模型层假设排最后。ρ 高:印证次数与出处可复算。
- **来源**:五链印证——奇绩 RSI 四阶段(9/16)/MGM ΦCH 生产版/arXiv 评测量级
  五级/RSI-Bench 六轴(9/16 调研)/**Jev(TypeSafe)分层范式(9/19,v5 485 函
  对表,"难的从来不是模型,是标数据和调那根线"=与 9/14 拍板同构)**;第六证=
  自家趋势线 1/5→3/5 全部来自 harness 层修复(模型未换)。
- **测量法**:归因报告若在印证链成立时仍先归因模型层,判 drift(违反归因纪律)。

对抗库交叉引用(Updates 注,判据本体不动):Jev 1.13 官方九失败模式 ↔ 我方
adversarial 四件(c3d24a2)同族——"字面 vs 意图"族(毒题自噬=字面理解毛边咬剥除
器的实证,与 status-hiding 同族);窗口挑选=window-picking 直对应。

### criteria:calibration-claim-verify-v1@catalog-v0
- **定义**:概率输出型决策模型(判分器/控制器)声称的校准水平(Brier/ECE/可靠
  图)必须可在公开 holdout 上独立重算;重算值与声称值的偏差超过披露容差即
  disagree。校准=控制代码按阈值消费概率时的安全裕度,校准声明是安全声明。
- **来源**:Jev 进具身范式(3.2Hz 决策,概率即安全层)+ NanoJev 开源校准训练
  (CE/Brier)与 holdout 发布格式;Genesis #2 Tier-2 实审(轨迹重放)。
- **测量法**:持公开 holdout 数据集+模型输出文件,重算 Brier/ECE,对声称值;
  陪审件:可靠图区间。**判据库现 15 条。**

## Updates
- 2026-09-15 立库,首批 3 条(均出自 10 条试点;同日回函 platform 记对方账)。
- 2026-09-16 增补 anchor-pool-selection-bias-v1(flywheel 闸③归因互锚,trace=本函链)。
- 2026-09-16 增补 judge-systematic-inconsistency-v1(flywheel X1-v2 47/47 活例;与 C 族包 C4 声明互锚)。
- 2026-09-17 双向记账成立:C 族首批校准包 c_family_calib_b1 由 compass 独立复算
  **6/6 agree**(agree/disagree/not_computable=6/0/0)——anchor-pool-selection-bias-v1
  首次被外部声明引用(C3a 剩余池 32/47)并以修正锚同批对照(C3b anchor_bank_v0
  3/47,一拦一放);judge-systematic-inconsistency-v1 经 C4 干净批零基线 47/47 咬合。
  回执:receipt.sig(ed25519,公钥 f7554b87…3e8be),manifest_hash f196d124…660a;
  函告 flywheel(trace=flywheel-c-family-b1-built-20260916)。预注册正本:
  docs/plans/2026-09-16-c-family-calib-preregistered.md。
- 2026-09-17 注册 v5 三长程分数(358 函,审 **3/3 通过**+条件:L1 τ 转执法须证据链/
  L2 配对表 versioned/L3 消费层首月 UNVERIFIABLE——三条均被提交方预含,如实归档)。
  同日 v5 359 函:被测材料规格=ticket 四件套(进 charter v1)、四类判分器盲区入
  对抗样例库(共建启动)、首被测=Sprint1(9/14-17)转录含失败三条;金标 provenance
  裁定=披露+seed 托管后**继续但永久标「半自证」不入认证名次**,外部题源并行。
- 2026-09-18 10 verdict 复算收账:agree 5/disagree 5/not_computable 0(score 声称
  10/10 独立复算吻合;disagree 全因 ev=true 无外部来源 5 行+total_tokens 聚合失效
  2 行——生产者自置实锤续案)。增严两处:新注册 skip-label-fidelity-v1;
  evidence-schema-v1 显式收紧(turn usage 非零 ⇒ total_tokens 必非零,子句化)。
  正本:docs/plans/2026-09-18-10verdict-recompute.md(agent a64017c,零改数)。
- 2026-09-19 注册 paradigm-corroboration-chain-v1(五链外部印证+自家第六证;
  v5 485 请求,归因纪律正本)+对抗库 Jev 映射注。主体=伊洛科技落 §5b(用户拍板)。
- 2026-09-20 注册 calibration-claim-verify-v1(Jev 吸收线 B 第一件;概率输出型
  模型的校准声明可复算——概率即安全层)。
