# W-V · soul benchmark 判分底座 → compass 交接(2026-06-07)

> platform-soul-dialog → compass。compass 领 11-benchmark 复现 env(T4 GPU·Hybrid A 复现 + B 自有旗舰)。
> soul 不重搭 env,只出 **验证器 / pass@k 判分底座** + 交接 **swebench_probe** 给 compass 复用。
> 收敛 W-D(FDE 闭环 soul scorer→verdict 同一套验证器底座)。

---

## 1. 你(compass)调的接口 = `benchmark_verifier.py`

位置(repo):`phase3/agent-engine/benchmarks/benchmark_verifier.py` · 纯函数 · 14 TDD green · 0 第三方依赖(stdlib `math.comb`)。
交接副本:`cloud:/home/ubuntu/fde-toolbox/benchmark_verifier.py`。

买方"核心资产 = 验证器 + 判分"就是这一层。三段:

```python
# ① 判一个解题轨迹 pass/fail(统一 SWE resolve 与 RUBRIC 两种判法)
judge_trajectory(result, mode="resolve")  # result=bool(test grader 是否 resolve)→ {"pass": bool}
judge_trajectory(scored, mode="rubric")   # scored=checklist_scorer 评分 dict → 读 overall_pass

# ② pass@k 无偏估计量(Chen et al. 2021 / Codex)
pass_at_k(n, c, k)                 # n=采样数 c=正确数 k=pass@k 的 k · 1 - C(n-c,k)/C(n,k)
pass_at_k_from_results(results, k) # results=[bool,...] 直接算

# ③ 难倒标注(买方判据:doubao 2.0 pass ≤ 3/5 = 难倒目标样例)
is_hard_for_model(c, n, max_pass=3)  # c ≤ max_pass → True

# ④ 一题 N 次采样 → 你 env 直接消费的 per-task 判定
aggregate_task("swe_001", trajectories, mode="resolve", k_values=(1,5), max_pass=3)
# → {task_uid, n, c, pass_at_k:{"1":..,"5":..}, hard_for_model: bool, per_attempt:[...]}
```

**你的 env 干的事**:复现 bench → 跑 agent 产 N 条解题轨迹 → 对每条调你的 grader(SWE 官方 harness resolve / RUBRIC checklist)→ 把 N 条结果丢给 `aggregate_task` → 拿 pass@k 报告 + 难倒样例标注。**判分逻辑你别自己写,调这个底座。**

## 2. 交接 swebench_probe(不重造 env)

`phase3/agent-engine/benchmarks/swebench_probe/` → SCP `cloud:/home/ubuntu/fde-toolbox/swebench_probe/`。组件:
| 文件 | 用途 |
|---|---|
| `subset_loader.py` | SWE-bench-lite 110 题单文件子集加载(已筛 ≥2 hunk) |
| `predictions.py` | 产 predictions.jsonl(喂官方 harness) |
| `budget.py` | token 预算控制(买方 token 计成本对齐) |
| `decomp_solver.py` / `proposer.py` | 子任务分解 solver(paradigm-B arm3) |
| `evolution.py` / `evolve_cycle.py` / `evolve_run.py` | evolve 出题/难度演化 |
| `probe1_verdict.py` | SWE resolve 报告 → escape-noise 判定(配 `escape_noise_stats.py`) |

配套:`escape_noise_stats.py`(paired 多 seed arm 对比 + sign test + escapes_noise gate)→ SCP `cloud:/home/ubuntu/fde-toolbox/`。子集артефакт:`swebench_lite_core_subset.json`。

## 3. 与 W-D / verdict-bus 的收敛(同一底座)

- RUBRIC 判分器 = vtf `harness/checklist_scorer.py`(`score_checklist` + `make_llm_judge`)。FDE 买方题用它,benchmark 的 RUBRIC 类题也用它 → `judge_trajectory(scored, mode="rubric")`。
- benchmark 的 pass@k 判分 = FDE verdict-bus 同一验证器底座。soul 打分 poller(`services/fde_scorer_poll.py` + `fde_scorer_runner.py`)已生产闭环(data_002 settled·source=soul·6/7)。
- 难倒样例 = 买方要的"难倒模型样例(pass≤3/5)",和 RSI 缺的外部 fitness 同构。

## 4. turf 边界(守)

- **compass own**:11-benchmark 复现可执行 env(T4 GPU·官方 harness·复现现成 bench)+ 跑出 N 条轨迹。
- **soul own(本交接)**:验证器/pass@k 判分/难倒标注接口 + swebench_probe 工具 + RUBRIC scorer。**我不搭你的 env,你别重写我的判分。**
- **算力开放问题(待你+用户对齐)**:KernelBench/RE-Bench/PostTrain/Inference 这类要真 GPU/训练执行,买方"不涉算力·token 计成本"矛盾 → token-only 轻判分 vs 真 eval 算力边界,你的 env 决定判分接口跑在哪;我只保证判分接口(本底座)与跑在哪无关(纯函数·你本地调)。

## 5. 你接下来(建议)
1. 拉 `benchmark_verifier.py` + `swebench_probe/` + `escape_noise_stats.py`(已 SCP fde-toolbox)。
2. 复现 1 个 bench(建议 FrontierSWE·swebench_probe 最直接)→ 跑 N 轨迹 → `aggregate_task` 出 pass@k + 难倒样例 = 第一个完整交付样例(先质后量)。
3. 判分接口有缺口(新 mode / 新聚合)→ outbound 提,我加在底座,不你那边各写一份。

> 关联:`docs/plans/2026-06-07-benchmark-reproduction-business-strategy.md`(11-bench 战略 + 四框分工)· `docs/plans/2026-06-03-benchmark-as-soul-fitness-design.md` · W-D `session_20260607_wd_fde_scorer_poller_data002_settled`(FDE 闭环首例)。
