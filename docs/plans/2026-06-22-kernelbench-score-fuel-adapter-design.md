# KernelBench → 6-key 分数制燃料适配器 · 设计 · 2026-06-22

> 北极星上下文:唯一中心环 = A 类燃料(强模型解出 + 弱模型难倒)→ QLoRA 蒸馏 → 外部 benchmark 证变强。点火 gated on A 类燃料攒够(阈值 12·minimal PoC 2-5)。ALE 单源 A 类稀缺 → 用户战略 = **多基准合池**(ALE+KernelBench+SWE+AutoLab)。V5 点名要 compass 的 KernelBench A 类(compass KernelBench turf)。

## 1. 问题 / 缺口(measurement-first 实测)
- 合池 intake = V5 `nautilus-v5/fde_capsule/ale_fuel_batch.py` 的 **6-key 分数契约**(`task_id/problem_statement/strong_solution/strong_score/doubao_score/strong_verified/score_type[/judge_version]`)→ `ingest_fuel_records` → `distill_qlora`。A 类门 = `is_a_class`(strong_verified ∧ strong>0 ∧ strong≥doubao×(1+rel_margin),maximize)。
- compass 已有 `kernelbench-stump-batch` 技能整条工具链(prescreen/producer/eval_drive/build_summary/verify_batch·T4·已验)——但它 **mint 到旧 dispatch 队列格式**(pass@k true_wall · `verifier_inline`/`starter_inline`),**没接到新 6-key 分数合池**。
- compass 有 attention 验证强解(SDPA 1.727x 过 eager 1.5x 门·T4 实测)。
- ❌ 缺口 = **KernelBench eval 结果 → 6-key 分数 record 的桥**。这是唯一缺的那一块。

## 2. 核心洞察(为什么这对闭环最优)
- KernelBench 本质 **分数制(加速比)** → 天生契合新 6-key 分数池(比它现在的 pass@k mint 路径更自然)。
- 北极星胜负手 = **非饱和连续分数燃料**。ALE 分数制 + KernelBench 分数制 = 一个**分数制燃料臂**,给蒸馏喂连续梯度(非二元 pass/fail)= 正是北极星要的非饱和硬燃料。
- 故 compass 最优贡献 = 把 KernelBench 变成**与 ALE 并列的分数制燃料臂**,而非递一个静态文件。

## 3. 方案(turf-clean · 复用不重造 · anchor #5)
| 谁 | 干什么 | 复用 |
|---|---|---|
| **compass**(env/eval/格式 turf) | 建 6-key 适配器 `kb_fuel.py` + 跑现有 harness 验强解 | stump 技能工具链 + V5 6-key 契约 + attention 已验强解 |
| **V5**(producer turf) | 在 ALE/SWE 同管线跑 Opus 强解 + doubao 难度,经 compass harness | 它的 producer + ARK completer + GPU 调度 |

### 组件:`kb_fuel.py`(compass repo · 镜像 `ale_fuel_batch.py` 结构)
- **纯函数 `build_kb_fuel_sample(task_id, problem_statement, strong_result, doubao_result) -> dict`**:发出 6-key(+score_type="maximize")。映射:`strong_score`=强解 harness 加速比·`doubao_score`=doubao best 加速比(失败/不过正确性门=0)·`strong_verified`=强解过正确性+速度门。**逐键匹配 V5 契约**(下游 ingest 零改)。
- **A 类判定**:复用 V5 `is_a_class` 语义(strong_verified ∧ strong>0 ∧ strong≥doubao×1.1·maximize)。设计选择 = **镜像语义**(不跨 repo import·避免耦合)+ 一条对拍测试锁定与 V5 字节级一致。
- **`accumulate_kb_fuel`**:按 task_id dedup 取 strong_score 更高者(镜像 `accumulate_ale_fuel`·幂等)。
- **GPU seam(gated · `pragma no cover`)**:`_run_one(task_id)` = 调现有 `kb_eval_drive.sh`/`build_summary.py` 拿 doubao 加速比 + 跑 harness 验强解 → `build_kb_fuel_sample`。真跑在 T4(GPU)·测试注入 fake。

### 数据流
```
stump 工具链(doubao 在 T4 难度实测·已有)──┐
强解(attention SDPA / Opus 生成·经 harness 验)─┤→ build_kb_fuel_sample → kb_fuel_records.jsonl
                                              └→ 同 ingest_fuel_records → 蒸馏合池(与 ALE/SWE 并池)
```

## 4. 错误处理 / 红线
- fail-soft:任一题 strong/doubao 阶段异常 → 跳过记 errors(镜像 ale batch)。
- 🔴 **不编 doubao 分**:doubao_score 必来自真实 eval JSON(否则毒燃料·违 §0-GOAL + `is_a_class` 守卫)。
- 🔴 退化守卫继承:strong==doubao(双败/同分)→ 非 A 类。strong=0(没真解出)→ 非 A 类。
- 甲方/伊洛绝不入任何产物(沿用 stump 技能红线)。

## 5. 测试(TDD)
- **离线纯函数**(GPU-free·主体):`build_kb_fuel_sample` 字段/类型 · `is_a_class` 镜像对拍(强>弱过 / 双败拒 / strong=0 拒 / 同分拒)· `accumulate_kb_fuel` 幂等取优。
- **seed 验证**(gated GPU):attention 一条端到端 —— 强解 SDPA 1.727x(已验)+ doubao 在 attention 实测(V5 管线跑或 compass GPU 空档)→ 确认 A 类与否(诚实:attention 强解=SDPA 库调用·doubao 可能也会→须实测定;不成则换 stump 技能 leverage 表的真难倒题 p18/p51 algebraic-collapse)。

## 6. 范围 / gate(诚实)
- 适配器主体 = GPU-free·可离线 TDD·本 session 可完成。
- 真 A 类 record = 需一次 doubao 实测(GPU·ARK key)→ gated;V5 在它管线跑 or compass GPU 空档(避与 7B 训练抢卡)。
- 不碰 V5 producer / soul ingest(turf)·只出 compass 侧桥 + 契约对齐 + seed。

## 关联
- 复用:`kernelbench-stump-batch` 技能 · `nautilus-v5/fde_capsule/ale_fuel_batch.py`(6-key 契约源)· `vertical-task-factory/fde_benchmarks/a_cluster/kernelbench_attention/harness.py`(env/eval)。
- 北极星 [[canonical_flywheel_convergence_northstar_20260622]] · FDE 第12类 ALE 双轨 [[project_ale_bench_dual_track_20260617]]。
