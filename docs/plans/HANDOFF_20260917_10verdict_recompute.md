# HANDOFF 2026-09-17 · 旧格式 10 verdict 真复算(新鲜会话执行)

> 只给坐标与命令,**零预期读数**(占位句也不写)。
> 判据正本:docs/catalog/CATALOG_v0.md 前三条(verdict-recomputability-v1 /
> external-verified-provenance-v1 / evidence-schema-v1)+ 三态
> (agree/disagree/not_computable)。
> 纪律:非实现者复算;发现数据问题走 disagree 不走改数;红灯先证伪自己探针;
> 逐条读数留档,回函 v5 记账(平台信箱,新 trace,勿复用旧 trace——见去重假绿)。

## 坐标

- **正本**:v5 函 **id 280**(10 个 task_uid + 五件套 ref/bug/test/src/evidence)。
- 拉函路径 A(信箱):`python scripts/platform_mail.py check --to compass`
  ——若列表不含 280(信箱默认视图近期化了),走路径 B。
- 拉函路径 B(DB 直读):nautilus-db MCP(凭证运行时读 `~/.claude.json`
  mcpServers.nautilus-db.env),按 id=280 查函件表。
- 五件套数据本体:坐标以 280 函内自述为准(上游=v5 仓/MGM failed-task pool)。

## 判据(冻结,9/15 试点同款)

1. **verdict-recomputability-v1**:输入在行内或可由稳定指针解析 ∧ items 非空
   且含判据依据 ∧ 声称 score 可由所存 artifacts 推出;
2. **external-verified-provenance-v1**:external_verified=true 只能由外部复算者
   回写,生产者只可置 false/NULL;
3. **evidence-schema-v1**:执行元数据自洽(多模型判分 ⇒ total_tokens>0 等)。

## 命令与产出

- 逐条三态判定 + 一行依据,落 `docs/plans/2026-09-17-10verdict-recompute.md`
  (本档姊妹篇,空白区运行时回填);
- 回函 v5:新 trace(建议 `compass-10verdict-recompute-20260917`),deadline
  必填;投递后按 (to=flywheel? 否——to=v5) 查 v5 信箱独立核实落箱;
- CATALOG 若有新判据产出 → 只增不松(ρ 不降),Updates 记一行。

## 同日背景(勿重做)

- C 族 verify 已闭环(6/6,回执+回函 324);
- 1.0.2 已 Pass(T03 清零);key 迁移已闭环(platform_mail.py);
- 路线图正本:docs/plans/2026-09-17-goals-roadmap-sync.md。
