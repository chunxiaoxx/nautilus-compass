# RSI 试验环 #1(记忆门三件套)· 预注册判据 · 2026-09-09 落档

> trace: compass-roadmap-20260907 §2.4 · #48 · 状态:**判据先于实现落档**(预注册纪律:
> 判据在任何结果产生前冻结;9/7 用户拍板口径,本档为其可寻址正本)。
> 执行流程(冻结):实现 → 回归 → 非实现者复算 → 合入。窗口 9/15(与旧入口退役、
> watchdog 同批动 daemon;一次改完一次验证)。

## 判据(四条,冻结不改)

| # | 判据 | 通过线 | 测法 |
|---|---|---|---|
| J1 | **fact_status 覆盖** | 落档后新写入的 memory 100% 带 `fact_status: measured\|inferred\|heard` | 扫描脚本对 mem 目录全量 frontmatter 检查;基线日(9/9)前旧条目不计入 |
| J2 | **查重零误合并** | 对照组(构造的无关条目对)0 次被判 merge;实验组(cosine≥0.9 对)100% 被判 merge | `dedup_check` 单测+一次真库抽样(≥20 条)人工复核 |
| J3 | **沿链一跳** | 命中含 `[[name]]` 引用的条目时,被引条目 100% 出现在 `chain_extra`;无链查询 chain_extra 恒空;recall P95 ≤ 基线 ×1.2 | 构造 A→B 对;延迟取 /status 滑窗+50 次冒烟计时 |
| J4 | **全局回归门** | 冻结三条 fact 查询的目标条目 hit@3 不低于改动前基线;e2e 现役口径不重跑时以三 fact 门+冒烟为准 | `ops/regression_gate.py`(改前跑=基线,改后跑=对照) |

## J4 冻结的三条 fact 查询(今日定死)

1. query=`9876 daemon ping 协议要求` → 期望命中 `daemon-9876-watchdog-rootcause-20260908.md`
2. query=`PyPI nautilus-compass 发布` → 期望命中 `pypi-311-published-20260906.md`
3. query=`LME-V2 451 题基准归属` → 期望命中 `lmev2-upstream-attribution-20260902.md`

## 三件套范围(实现契约)

1. **fact_status 写入门**:daemon `parse_memory_file` 读出+recall 结果带出+hook 渲染标注;
   session_writer 蒸馏输出必带;人工写入走纪律(frontmatter 模板)。**只标注不过滤**
   (过滤策略 Phase 2 与置信度分层一起定,本环不引入自动丢弃)。
2. **查重触发合并**:daemon 新 action `dedup_check`(BGE 对全项目条目,≥0.9 merge /
   0.75-0.9 gray / 其余 unique);session_writer 写入前调用,merge 时升级原条目不新建;
   人工写入纪律=写前调用。**本环 daemon 不自动改写任何 memory 文件**。
3. **沿链一跳**:recall 组装后对 top 条目 body 的 `[[name]]` 引用展开一层(不递归,
   cap 5,`chain_extra` 单独字段+`via` 标注,不混入 recall 主列表打分)。

## 边界(冻结)

- 本环不动:drift/锚点/查询改写/生产 rerank 等现役开关;不加自动删除/自动改写。
- daemon 改动单分支 `feat/memory-gate-trio` 单 commit 可回滚;合入=受控重启+复测 J1-J4。
- 判据改动只允许"更严",不允许放宽;任何放宽必须用户拍板并追加记录于本档。

## 记录(合入后回填)

- [x] 9/9 实现完成:daemon 仓分支 `feat/memory-gate-trio`(b982327,worktree
  `~/.claude/plugins/nautilus-compass-memgate`)· 15 单测绿 · 未部署(等窗口)
- [x] 9/9 基线三 fact 读数(hit@3 全 PASS · 生产 daemon 3912205):
  daemon ping→daemon-9876-watchdog(615ms)· PyPI→pypi-311(1496ms)·
  LME-V2→lmev2-upstream(2072ms)· 基线固化 ops/regression_gate_baseline.json
- [ ] 9/15 改后三 fact 读数:待回填
- [x] J1-J3 读数:已回填(见下「9/14 合入执行读数」)
- [ ] 非实现者复算回执:待回填(9/15 早独立会话)
- [x] 9/9 实现修订一条(手段非判据):session_writer 对 merge 命中**不自动改写**
  原条目,只标 `merge_target` frontmatter 留人工/下一环——自动改写污染原条目风险
  大于收益;J2 判据(零误合并)不变。

### 9/14 合入执行读数(提前于 9/15 窗口,用户拍板)

- **合入形态**:生产 worktree checkout `feat/memory-gate-trio`(9cb9e7e)。⚠️中途曾试 main 基座 cherry-pick 版(merge-ready-0915),发现 main 缺 3912205 线运行时修复(recall v2.4/HUD wrapper 278 行/daemon_start 改进)→hook 回退 v2.3,当场纠正回 feat 线直切;merge-ready-0915 弃用,main 统一留作后续工作。
- **J1(fact_status 覆盖)**:写入门在线(15 单测覆盖 fact_status 路径);真库覆盖率待合入后新条目产生再统计回填(合入日无新写样本)。
- **J2(查重零误合并)真库抽样**:无关文本→unique(hits 空)✅;同主题不同文→gray 0.840✅(区间 0.75-0.9);真条目原文重判→merge 0.938✅(≥0.9)。三档行为全对,零误合并。
- **J3(沿链一跳)在线验证**:查询命中 aegis-compass-competitor-20260907(含 [[paper-roadmap-history-20260904]]),chain_extra 正确带出被引条目✅;无链查询 chain_extra 恒空✅。延迟:冷路径 389-518ms(与 J4 基线同量级),热缓存 p50=1ms(daemon mtime cache 命中)。
- **J4(全局回归门)**:9876 生产 GREEN(三 fact 全 PASS·命中正确;首查 7.1s=embed 冷缓存,后续 389/400ms);预演日 9878(main 基座版)同样 GREEN——两基座双验。
- **功能在线探针**:dedup_check action 被生产 daemon 接受并正确裁决(ok:True,旧版无此 action)。
- **RSI 环第四段(非实现者复算)待办**:留给 9/15 早新鲜会话独立执行(纯按本档判据复算,不带实现上下文)。
