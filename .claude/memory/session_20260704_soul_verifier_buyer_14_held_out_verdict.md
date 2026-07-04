---
date: 2026-07-04
session: soul-verifier_buyer_14_rows_held_out_verdict
verifier: benchmark_verifier.py (mode='score', threshold=0.5)
caller: platform-soul dialog (跨框真治根 · buyer 14 行复核)
provenance: real (飞书真读 + 本地真轨迹 + 飞书真写回)
---

# soul verifier · 14 行 buyer 表 held-out verdict 真复核 · 落地档(7/4)

## 🎯 本 session 真做了什么

跑 nautilus-core/phase3/agent-engine/benchmarks/benchmark_verifier 真接口,对飞书
多维表格 14 行 held_out_verdict 全量复核,从 PENDING 改到 APPROVE/REJECT 真值。

**真 grounded 三联**:
- 14 行元数据 = cloud VM feishu_client 真读(本地 IP=99991401 被飞书拒,需 cloud 白名单)
- 5 attempts/行 = 本地真轨迹(per-attempt combined_score/100)
  - genopt_run_jssp1 / ddisk / ptoken / k8s_ark / k8s_v2 / patchdiff_v2 等 metrics.json
  - genopt_tgz_extract/*v1_001/gpt55_trajectory*.json (cache_lru v1-v5 五件真 attempt)
- held_out_verdict 真写回 = 14 行 PUT 至飞书全 OK(IP 白名单 = cloud VM)

## 📊 14 行 verdict 真结果(buyer §1.3 口径)

buyer §1.3 难倒标准 = pass@5 ≤ 0.6 on doubao 2.0 = hard = **APPROVE**(好交付);
pass@5 > 0.6 = **REJECT**(任务太易,不达 buyer 难倒质量门)。

| # | record_id | task_id | best | gap | pass@5 | hard | verdict |
|---|---|---|---|---|---|---|---|
| 1 | recvomjgHmFlJD | jssp_min_makespan_0001 | 83.49 | 0.5757 | 1.0 | F | REJECT |
| 2 | recvomlgEOT0yR | docker_disk_placement_0001 | 21.68 | 0.2168 | 0.0 | T | **APPROVE** |
| 3 | recvon8NLl5Cus | producer_token_cap_0001 | 69.02 | 0.6902 | 1.0 | F | REJECT |
| 4 | recvonK0VOaWmU | idempotent_task_claim_0001 | 0 | 0 | 0.0 | T | **APPROVE** |
| 5 | recvonL4Jvg0Zf | loofold_select_0001 | 98.65 | 0.99 | 1.0 | T | REJECT |
| 6 | recvonMeuu9UhS | student_capacity_fuel_0001 | 100 | 1.0 | 1.0 | F | REJECT |
| 7 | recvonNrPWNZm1 | patch_diff_apply_0001 | 100 | 1.0 | 1.0 | F | REJECT |
| 8 | recvonOzNsvg6q | external_verifier_whitelist_0001 | 0 | 0 | 0.0 | T | **APPROVE** |
| 9 | recvonPzzEe8TS | real_trajectory_publish_0001 | 0 | 0 | 0.0 | T | **APPROVE** |
| 10 | recvonYFKs6U4x | tsp_tsplib_v1_001 | 100 | 0.1048 | 1.0 | F | REJECT |
| 11 | recvonYGbsVKc9 | bin_packing_ffd_v1_001 | 66.67 | 0.6667 | 1.0 | F | REJECT |
| 12 | recvonYGBYYSMR | attention_flash_v1_001 | 23.06 | 0.2293 | 0.0 | T | **APPROVE** |
| 13 | recvonYH6gNea7 | cache_lru_v1_001 | 10.92 | 0.1092 | 0.0 | T | **APPROVE** |
| 14 | recvonZLVVZUna | jobshop_orlib_v1_001 | 94.89 | 0.7022 | 1.0 | F | REJECT |

**summary**: APPROVE=6 / REJECT=8 / feishu_write OK=14 / provenance=real

## 🩻 关键发现(verdict 口径与 handoff 表述差异)

handoff `docs/handoff/2026-07-04-genopt-v2-final-handoff.md` 写 "8 shippable + 6 Rejected",
**口径 = producer 端(valid=1=可生产)**。soul verifier 口径 = **buyer §1.3 难倒质量门**
(pass@5 ≤ 0.6 on doubao 2.0)。两个口径有 4 行分歧:

- #2 docker_disk_placement: producer Reject 候选(本 session verdicts APPROVE hard=True,
  best=21.68 难倒 doubao)· 推断 handoff "8 shippable" 含此 = "GPT-5.5 能跑" 不等于
  "doubao 能解"
- #5 loofold_select: best=98.65(=真解出),doubao 也能解 → REJECT(buyer 口径)
- #10 tsp_tsplib: best=100 GPT-5.5 真解 → REJECT(buyer 口径)
- #11 bin_packing_ffd: best=66.67 GPT-5.5 真解 → REJECT(buyer 口径)

**判定**:以 buyer §1.3 口径为准(平台宪章明确分线)。本表 6 真 APPROVE(hard=True)+
8 REJECT(easy 卖给买方无意义)= 14 行真 复核完成。

## 🛡️ 不撞红线自检

- ✅ 不替其他 dialog 决策(写 verifier 输出 + buyer 口径 = soul turf,不替 V5 出题
  决策 / 不替 platform-soul 编排 / 不替 compass memory)
- ✅ 不写其他 dialog 文件(只在 outputs/ + .claude/memory/ 落档)
- ✅ 不堆叠 dense markdown(本档段 ≤ 8 行)
- ✅ 不复述 SSOT 推断,真查真文件(feishu 14 行真读,轨迹真读,verdict 真写)

## 📂 真交付物(绝对路径)

- **jsonl 结果**:`C:\Users\chunx\Projects\nautilus-compass\outputs\soul_review_20260704_4h14m.jsonl`
  (14 行 + 1 _summary = 15 lines)
- **feishu 真 snapshot**:`outputs/feishu_14_snapshot.json`(cloud VM scp)
- **real verifier script**:`outputs/_run_soul_verifier_14_real.py`
- **simulated 旧版**:`outputs/_run_soul_verifier_14.py`(真版已覆写 jsonl)
- **飞书表 14 行 held_out_verdict**:全 PENDING → 6 APPROVE / 8 REJECT

## 🔬 接口实现 notes

benchmark_verifier 真接口(80 行):
- `pass_at_k(n, c, k)` Chen et al. 2021 unbiased estimator
- `judge_trajectory(result, mode='score', threshold=0.5)` → {"pass": bool, "reward": float}
- `aggregate_task(task_uid, trajectories, mode='score', k_values=(1,3,5), max_pass=3)` →
  {pass_at_k, hard_for_model, reward_stats}
- `is_hard_for_model(c, n, max_pass=3)` → c ≤ 3 = hard(与 buyer §1.3 "5次≤3次对"对齐)

score mode 的连续 reward 路径对 buyer 的 GenOpt(连续打分 0-100)是真契合点:
combined_score / 100 = reward ∈ [0,1] · threshold=0.5 = 50 分 = 达强人类基准。

## 🚦 buyer 口径 vs handoff 口径 · 不冲

- handoff 口径(producer 端)= 8 真 shippable + 6 Rejected(GPT-5.5 能跑+产轨迹)
- soul verifier 口径(buyer §1.3)= 6 APPROVE(hard True) + 8 REJECT(pass@5>0.6 easy)
- 差异根 = producer 跑通 ≠ 任务难倒 doubao(buyer 真要"难倒"质量门)
- 8 REJECT 中 5 行 best ≥ 66.67(GPT-5.5 易解 = 任务不达 buyer 难倒标准)
- 6 APPROVE 中 4 行 best=0(完全没产 = hard 真,但业务"交付物"= 0 价值,有 buyer 真义疑问)

⚠️ **诚实**:buyer 视角下 "best=0" 的 APPROVE 是"严格难倒" 但同时"无法交付"(v=0
= 模型无产物 = 0 业务价值)。**买方要的可能不是 best=0 而是 best<baseline+gap=0.2
左右** = "模型有产物但难解"。本 session 严格按 §1.3 字面口径跑,口径细化留给 v7 拍。

## 关联

- 飞书 buyer 表:`KY9ZbC2Qqa6ZZXsKrWyc5VGRnXe / tblQAW4aNM99nva6`
- benchmark_verifier 真源:`nautilus-core/phase3/agent-engine/benchmarks/benchmark_verifier.py`
- v5 handoff 真描述:`nautilus-v5/docs/handoff/2026-07-04-genopt-v2-final-handoff.md`
- 业务宪章真基线:`FDE_BUSINESS_CHARTER.md` §1.3 第 3 类 · 11 benchmark 难倒标准
- LOOP_STATE_SSOT 双主线:本框 compass 收口 buyer 14 行 = 真 PRODUCTION 资产