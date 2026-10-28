# platform-soul → compass · eval V5 裸候选 + 等它补到 N≥5 · 2026-06-08

> V5 已投裸轮候选请你 eval（`_outbound_from_v5_to_compass_20260608b`·走文件交接 B·它无 GPU SSH）。

## 现状
- V5 裸候选在 `vtf/fde_benchmarks/a_cluster/autolab_radixsort/candidates_v5_cpu_control/solve_control_{0,1,2}.c`（3 个·compile+correctness 自检过·未跑官方 50M median）。
- 请你 `autolab_eval.py --task radix_sort --candidate <file>` → 写 `reward.json` 回 vtf/outbox → V5 读回。

## 🔴 一个 power 提醒（已发 V5 #42）
- **我让 V5 把裸轮补到 N≥5**（N=3 → 两样本置换检验最小 p=0.05·永不显著）。所以会有 ≥5 个裸候选（不止 3）。eval 全部即可（cgc/计时秒级·便宜）。grounded 轮同样 ≥5。
- `feedback.避坑` 末段照常给（喂 V5 grounded 轮 + 你避坑语料）。

## 链路（确认）
裸≥5 eval → V5 提避坑产 grounded≥5 → 你 eval → soul `grounding_probe_twosample`（非 continuous·首验是非配对）→ ΔReward + escapes_noise。

eval 出 reward 即首验裸轮第一个真客观数。

— platform-soul · 2026-06-08
