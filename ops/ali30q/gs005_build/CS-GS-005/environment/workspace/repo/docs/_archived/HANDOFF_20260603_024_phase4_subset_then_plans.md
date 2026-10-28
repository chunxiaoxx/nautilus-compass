# HANDOFF #024 · Phase 4 范式 B probe — 子集核验 → writing-plans → Probe 0/1

> 写 2026-06-03 · platform-soul dialog · 接 [HANDOFF #023](./HANDOFF_20260603_023_phase3_multiseed_run_in_progress.md)(范式 A 证伪 CLOSED)。
> 本 session 已用 brainstorming 收敛出范式 B 可证伪 probe 设计(binding-DONE · 未写代码)。下个 Phase = 推进到可跑的最小 probe。

## Fresh-session 提示词(复制即用)

```
Benchmark Loop Phase 4 · 范式 B(division-of-labor)probe — 子集核验 → writing-plans → Probe 0/1

背景:Phase 1-3 范式 A(ensemble/consensus)已证伪。6/3 已用 brainstorming 收敛出范式 B 可证伪 probe 设计(binding-DONE),未写代码。下个 Phase = 把设计推进到可跑的最小 probe。

session-start 必读:
- memory/session_20260603_phase4_paradigm_b_probe_design_done.md(设计全貌 + 4 决策 + scaffold 选型)
- docs/plans/2026-06-03-paradigm-b-division-of-labor-probe-design.md(设计 doc · master 31fd4d82b+3626b0bc4 未 push)
- memory/design_20260603_multiagent_paradigm_b_division_of_labor_reframe.md(方向源)

设计已锁(勿重开):SWE-bench-lite 核心子集(中立筛 gold patch ≥2 文件/hunk)· 2x2 双因子(上下文隔离×工具专精)· 四臂全建在单 scaffold mini-swe-agent(Agentless 仅作 decomp 设计参考·不混两套代码库)· 匹配总预算 + 跨 lab M3+DeepSeek · Probe1=arm1 vs arm3 最小可证伪。

本 session binding-DONE(按序 · 不铺多线):
1. 【前置·先做】纯 Python 数 HuggingFace princeton-nlp/SWE-bench_Lite,统计满足"gold patch 跨 ≥2 文件 OR ≥2 hunk"的实例数(diff --git 计文件 · @@ 计 hunk),确认子集够 N≈30-60。不够则放宽标准或回报。无需 Docker。
2. 【顺手小修·独立】LLMClient.chat 加 per-request timeout(透传 messages.create ~180s)— Phase 3 seed3 挂死根因,任何长 multi-seed cloud run 前必须。走 TDD + worktree。
3. 子集确认够 → writing-plans 出 Probe 0(冒烟:arm1 ~5 题 sane baseline)+ Probe 1(arm1 vs arm3)实现计划。先 plan 不马上写 probe 主体。

护栏:复用 PR#127 harness 骨架 + Phase 3 escape-noise stats(anchor #5)· benchmark=proxy 非市场验证 · 正脱噪信号前不 wire V5 RSI/经济环/compass L4(anchor #3)· diverge/converge 分离 · R1 drift 自停 · R2 不"全做"。

cross-dialog(不抢不催):V5 outbound #15 已投(F2 voting 死锁已修+验 · V7 本就在 · 揭穿 executor check-stage 空心 = 0 PR · 内部飞轮 ship 是空的)。check-stage gap 是 V5/agent 侧决定是否追,平台侧不擅自修(自指再投资 · anchor #3)。
```

## 30 秒状态

- **主线 Phase 4 设计 binding-DONE**:4 决策(SWE-bench-lite 核心子集 / 2x2 双因子 / 单 scaffold mini-swe-agent · Agentless 作 decomp 设计参考 / 匹配预算 + 跨 lab M3+DeepSeek)· Probe1=arm1 vs arm3 · scaffold spike(3 并行 agent)证 harness 单 cloud VM 可行。doc 2 commit `31fd4d82b`+`3626b0bc4`(未 push)。
- **插入线 V5 RSI 请求处理完**(用户授权"都做"):F2 voting 死锁 1 行 SQL fix 实测兑现(`approved:6` · 6 真提案 accepted/auto_stale)· V7 voter 本就存在(agents id=9000004)· 验证揪出下游 executor check-stage 空心(`{'passed':False,'checks':[]}` → 0 PR)· outbound #15 投 cloud V5 通道验在位。详 memory `session_20260603_rsi_flywheel_f2_fix_check_stage_hollow.md`。

## 下个 session 第一步 = 子集核验(纯 Python · 无 Docker)

数 `princeton-nlp/SWE-bench_Lite` test split(300 行)`patch` 字段:`diff --git ` 头计文件数 · `@@` 头计 hunk 数 · 选 files≥2 OR hunks≥2。确认够 N≈30-60(Lite gold patch 偏小,多文件/多 hunk 是少数)。够 → writing-plans;不够 → 放宽标准回报用户。

## git

master = 本 handoff + 设计 doc 2 commit(未 push origin)。Phase 3 worktree `benchmark/phase3-multiseed` 未 merge(范式 A 已 CLOSED · PR #127)。soul daemon timer 保持 inactive;**nautilus-backend 本 session 因 F2 restart 过一次(已 active)**。
