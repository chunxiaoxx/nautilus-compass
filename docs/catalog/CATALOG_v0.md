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
