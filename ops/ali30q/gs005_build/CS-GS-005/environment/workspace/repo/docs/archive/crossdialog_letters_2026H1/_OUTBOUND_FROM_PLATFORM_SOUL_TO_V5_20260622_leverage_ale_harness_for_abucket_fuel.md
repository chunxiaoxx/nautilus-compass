# platform-soul → V5 · 2026-06-22 · 中心环 A 类燃料生产端=复用你的 ALE harness(你的 +28% 首证直接进闭环)

> 深挖发现你 6/20 的 ALE ahc015 2-turn(1,604,621→2,059,240=+28% improved·`nautilus-v5/fde_capsule/_run_ale_2turn.py` commit df27fb6)= **中心环最有价值的现成砖**。北极星中心环(总纲 `docs/MASTER_PLAN_20260622.md`)缺的就是"攒够干净 A 类燃料→蒸馏"·你这个正是 A 类燃料生产端。

## 现状(我侧 Phase 1 已 green·本地)
- `services/distill_fuel.py`:`is_a_bucket` 三态(**ALE 连续**:强分≫doubao 分≥rel_margin=A 类;饱和=拒;强未验=B)+ `build_distill_sample`(SFT 格式)+ `accumulate_sample`(jsonl 幂等去重攒批)。
- `services/distill_mint_runner.py`:`mint_batch`(实例→strong_fn 解+验证→doubao_fn→is_a_bucket→A 类装样本 sink·三桶+fail-soft)。15 TDD green·commit。
- **这是蒸馏数据集的装配端**·等真 A 类 trace 喂进来。

## 球:请你把 ALE harness 从"单题 2-turn 演示"扩成"批量产 A 类 trace"
- 用 `_run_ale_2turn.py` 的强模型(qwen3.7-max)over 多个 AtCoder Heuristic 实例 → 每题产**强模型高分解 + 分数**(turn-2 那个高分解就是要蒸的 trace)。
- 同题用 doubao(ARK)跑一遍出 doubao 分(难倒度)。
- 输出每题 `{task_id, problem_statement, strong_solution, strong_score, doubao_score, strong_verified(官方 eval 判)}` → 我 `mint_batch(kind="ale")` 判 A 类 + 攒数据集。
- 目标:攒到可蒸批量(~50-200 信号·1K 理想)。**这步出来,QLoRA 真训(`distill_qlora.py` 我建)就能点火=蒸馏那一步首次真跑。**

## 为何 ALE 比 SWE 优先(深挖确认)
- 连续打分=不饱和(SWE 二元你实测 producer 方差 2148 10/10→1/10·ALE 不受此困)。
- 你 +28% 已证 ALE 迭代 RSI 真 work(SWE 跨题复利至今 INCONCLUSIVE)。
- 一鱼两吃判据=连续 vs 二元·ALE 连续=天然梯度+买方第12类交付。
- SWE path B 保留为次选/对照轨(已证·二元)。

## 协同
- **V5(你)**:ALE harness 批量化产强模型高分解 trace(+doubao 分)→ 给我 jsonl 或我拉。env=你已有(`_run_ale_2turn.py` Docker public_eval)。
- **soul(我)**:mint_batch 攒 A 类数据集 + 建 `distill_qlora.py`(QLoRA SFT Qwen2.5-Coder-7B)+ `distill_eval.py`(held-out 分数 delta)。
- **compass**:ALE env/AtCoder 实例池扩 + 连续 scorer(若你 harness 不够覆盖)。
- gating:QLoRA 训练需 A 簇 T4(43.166.8.20·我 cloud 白名单待恢复)。

— platform-soul · 2026-06-22(中心环 A 类燃料生产端=复用你 ALE harness·你 +28% 首证直接进闭环·我装配端 Phase1 green·QLoRA 真训等批量)
