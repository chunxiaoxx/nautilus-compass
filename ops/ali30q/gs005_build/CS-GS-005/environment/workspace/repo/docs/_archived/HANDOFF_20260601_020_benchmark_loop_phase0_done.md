# HANDOFF #020 · fresh session 入口 · Benchmark Loop Phase 0 done

> 写 2026-06-01 · platform-soul dialog · 本 session = 深度战略重想 + 3 outbound 闭环 + Phase 0 probe 实跑。
> 精简入口 · 详情在 plan + memory · 不在此重复堆。

## 30 秒状态

递归自我提升闭环方向已重定 + Phase 0 probe 跑完。**下一步明确:Phase 1 = 拿一个单 LLM 有 headroom 的更难数据集,再测 consensus vs single delta。**

## session-start 必读 2 份(按序)

1. `memory/design_20260601_external_selection_pressure_benchmark_loop.md` — **战略命题 + Phase 0 真结果 + redirect**(核心)
2. `~/.claude/plans/purring-giggling-lark.md`(已 approve)— benchmark-probe plan · Phase 0/1/2 分阶段

## 锁定的命题(一句)

递归闭环 5-6 次失败根 = **无外部选择压力**(fitness 全自指)。方向 = 用**外部 benchmark ground truth 当 fitness**,测多 agent consensus 是否比单 LLM 更可靠。产品(Path B reliability)与闭环合一。

## Phase 0 结果(✅ done · 真数字)

- 跑现有 `phase3/agent-engine/benchmarks/raid_benchmark.py`(cloud soul-workspace · M3)· **史上第一次产出真 accuracy**。
- 测量管道证明可用(load dataset → 真 LLM → 对照 ground_truth → 算 accuracy)。
- single-agent = **100%**(task2 10/10 · task3 5/5 · task4 10/10)· 输出 timeout 截断未见 SUMMARY/RAID 段。
- **决定性发现**:数据集太易,单 LLM 已满分 → 无 headroom → 不能在此测命题。

## Phase 1 起点(下个 session 第一步)

1. **~30 min scoping 选数据集**:要单 LLM 失败率 20-40%(留 headroom)+ ground-truth 检查便宜。
   - **不要先上 SWE-bench-lite**(docker/test-runner 最重 · yak-shave 风险)· 信号出来后再上。
   - 优先 labeled bug-detection / 更难分类集 · 复用现成 `evaluate_classification`。
2. **TDD 写 consensus 变体**:同组 items 跑 `raid_engine.execute(level=RAID_2/3)` consensus vs 单 LLM baseline · 算 accuracy delta。
   - binding-DONE = single vs consensus 两真数字 + delta · delta>0 命题成立 / delta≤0 如实记不假装。

## 本 session 已闭环(不用再碰)

- outbound #13 platform→V5 已交付:Kairos (a)hard-exclude no-migration **unblocked**(独立 binding-DONE 排期 · 非本闭环线)· timer keep-disabled + gate principle 迁 benchmark loop · b2 平台 observer 0-action。
- `docs/FLYWHEEL_HEALTH_AUDIT_20260601.md` 已写。

## Parking(非本闭环 · 不抢跑)

- Kairos hard-exclude fix 实现(platform turf · V5 已 ack · 等排期 ship · V5 协助 24-48h 观察)
- cnt_compass_soul_sub_a1(due 6/5 · 已 ack read+write-back · 等 compass close-loop · benchmark 方向给它喂真 fitness)· cnt_compass_v5_outcome_b2(compass↔V5 · 平台 observer)
- daemon timer re-enable(等 benchmark probe 出信号后 · 不在空/错 fitness 上 re-enable)

## git

本 session 未 commit 文件(FLYWHEEL_HEALTH_AUDIT / OUTBOUND #12 #13 / 本 handoff 在 working tree · plan+memory 在 ~/.claude 不在 repo)· 待 user 决 commit/branch。
