# GenOpt RL 5-task delivery (2026-07-03)

> Task count: **5** / 1000 (0.5%, 7/9 推进目标 1%)  
> Domain coverage: **5/5** (OR / KernelEng / ComputerSys / Quantum / Robotics) — OR 3 题 / 其他各 1 题  
> Difficulty bands: **2 Easy + 2 Hard + 1 Medium(漂移)**  
> GPT5.5 behavior: **可重现**(v7 二次标定 3/4 一致 · Attention seed 漂移真证)  
> Producer identity: `h800-genopt-001` (offline registry, SSOT §0-ARCH)  
> Status: **provisional · author=platform** (待 FDE 框接球真回转终品)

## 18-col 机密交付格式 (GenOpt 第 3 类 · S3 交付表)

| task_uid | task_title | domain | subdomain | task_type | buyer_spec_ref | n_instances | n_hard | n_medium | n_easy | baseline_score | reference_score | best_score | gap_closed | difficulty | deliverable_files | trajectory_provenance | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| genopt_or_jobshop_orlib_v1_001_20260702 | Job-Shop Scheduling: Minimize Makespan on Classic OR-Library Instances | operations_research_and_decision_science | JobShop | code_optimization | vtf/BUYER_SPEC_GenOpt_RL_20260702.md | 6 | 0 | 0 | 1 | 24.68 | 90.50 | 94.89 | 0.7022 | Easy | Task.md, baseline/init.py, reference/solve.py, verification/evaluate.py, data/{6 instances + optima.json + SOURCE.txt}, frontier_eval/{9 txt}, gpt55_trajectory_h800.json | gpt55_trajectory_h800.json (H800 端 OPENAI_BASE_URL 直连 qixuw) | provisional · author=platform · producer=h800-genopt-001 |
| genopt_or_tsp_tsplib_v1_001_20260702 | Traveling Salesman: Minimize Tour Length on TSPLIB Synthetic Instances | operations_research_and_decision_science | TSP | code_optimization | vtf/BUYER_SPEC_GenOpt_RL_20260702.md | 6 | 1 | 0 | 0 | 89.51 | 99.83 | 100.00 | 0.1048 | Hard | Task.md, baseline/init.py, reference/solve.py, verification/evaluate.py, data/{6 instances + optima.json + SOURCE.txt}, frontier_eval/{9 txt}, gpt55_trajectory_h800.json | gpt55_trajectory_h800.json (H800 端 OPENAI_BASE_URL 直连 qixuw) | provisional · author=platform · producer=h800-genopt-001 |
| genopt_ke_attention_flash_v1_001_20260702 | Scaled Dot-Product Attention: Speedup on Synthetic Workloads | kernel_engineering_and_systems | Attention | code_optimization | vtf/BUYER_SPEC_GenOpt_RL_20260702.md | 4 | 1 | 0 | 0 | 0.87 | 8.73 | 23.06 | 0.2293 | Hard | Task.md, baseline/init.py, reference/solve.py, verification/{evaluate,_run_one,_naive_one}.py, data/{4 instances + SOURCE.txt}, frontier_eval/{9 txt}, gpt55_trajectory_h800_v7.json | gpt55_trajectory_h800.json (H800 端 OPENAI_BASE_URL 直连 qixuw) | provisional · author=platform · producer=h800-genopt-001 |
| genopt_cs_cache_lru_v1_001_20260702 | Cache Eviction Policy: Minimize Miss Rate on Synthetic Traces | computer_systems | CacheLRU | code_optimization | vtf/BUYER_SPEC_GenOpt_RL_20260702.md | 5 | 1 | 0 | 0 | 0.00 | 11.42 | 10.92 | 0.1092 | Hard | Task.md, baseline/init.py, reference/solve.py, verification/{evaluate,_run_one}.py, data/{5 instances + SOURCE.txt}, frontier_eval/{9 txt}, gpt55_trajectory_h800_v5.json (v5 fix) | gpt55_trajectory_h800.json (H800 端 OPENAI_BASE_URL 直连 qixuw) | provisional · author=platform · producer=h800-genopt-001 |
| genopt_or_bin_packing_ffd_v1_001_20260702 | Bin Packing: Minimize Number of Bins | operations_research_and_decision_science | BinPack | code_optimization | vtf/BUYER_SPEC_GenOpt_RL_20260702.md | 5 | 0 | 0 | 1 | 0.00 | 66.67 | 66.67 | 0.6667 | Easy | Task.md, baseline/init.py, reference/solve.py, verification/{evaluate,_run_one}.py, data/{5 instances + optima.json + SOURCE.txt}, frontier_eval/{9 txt}, gpt55_trajectory_h800_v7.json | gpt55_trajectory_h800.json (H800 端 OPENAI_BASE_URL 直连 qixuw) | provisional · author=platform · producer=h800-genopt-001 |

## 已 commit 链 (7/2-7/3 13 件)

- `4e42082a4` GenOpt RL 主线 7/2:JobShop Easy + TSP Hard 双题真证 + producer 注册化协议
- `b8ecc36ea` GenOpt RL 三题扩域 7/2:KernelEngineering + ComputerSys + BinPack
- `deb0df8a7` GenOpt RL 5 题真测:Easy x2 + Hard + Medium + Rejected 全 grounded
- `be43fe4fc` Cache verifier 路径 bug 修复 + ARCHITECTURE.md 框架钉死
- `1672791de` producer_registry 离线版 + weekly review 索引
- `db81d20cb` Cache v5 真 grounded Hard 0.1087:verifier fix 治根 + harness 加 --baseline
- `773d20e16` 4 框催球 outbound(7/3 0:35 · 截止 9:00)
- `1df0b9e31` GenOpt RL 5 题 v7 二次标定(3 难度档 · 可重现)
- `19bc936d9` Attention Flash v7 真 grounded Hard 0.2293(漂移 Medium→Hard)
- `433ac08a6` GenOpt RL 第 6 题 Quantum:qaoa_maxcut_v1_001 端到端通
- `8a79a1779` SSOT 7/3 0:55 grounded
- `0ff21bc7c` PARKING_LOT.md 钉死
- `04cf6a7ce` GenOpt RL 第 7 题 Robotics:pathplan_astar_v1_001 框架完成 (partial)

## 7/3 1:35 跨对话框协议真发

4 框催球 outbound 真发 cloud `~/nautilus-soul-workspace/docs/`(非 git,治 6/2 复发):

- `OUTBOUND_TO_V5_DIALOG_20260703_4panel_cuipang_GenOpt_mainline.md`
- `OUTBOUND_TO_COMPASS_20260703_4panel_cuipang_GenOpt_mainline.md`
- `OUTBOUND_TO_SOUL_20260703_4panel_cuipang_GenOpt_mainline.md`
- `OUTBOUND_TO_FDE_20260703_4panel_cuipang_GenOpt_mainline.md`

## 阻塞清单(待 4 框 + backend + A800 真回)

1. FDE 框接球真回 → 飞书 14 列 S1 派活表 + S3 交付表真入 + S3 结算表
2. backend conn refused → producer 注册脚本真跑(目前用 `producer_registry.json` 离线版)
3. A800 真 verified verdict → 破自循环 Step 2/3
4. QAOA 第 6 题 H800 标定重跑(中转 502 临时拒)
5. 4 框真接球真回(等 V5/compass/soul/FDE session 真开)

## 真 closure 标的 (7/4 14:00 自查)

- 5 题入飞书表(此文件 + xlsx 是 upstream artifacts · FDE 框真入表后 closure)
- 0 题入表不算 closure(锚 #3 anti-D = 不维护 = 清单 ≠ 闭环)