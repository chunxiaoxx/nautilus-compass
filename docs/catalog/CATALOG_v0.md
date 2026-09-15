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

## Updates
- 2026-09-15 立库,首批 3 条(均出自 10 条试点;同日回函 platform 记对方账)。
