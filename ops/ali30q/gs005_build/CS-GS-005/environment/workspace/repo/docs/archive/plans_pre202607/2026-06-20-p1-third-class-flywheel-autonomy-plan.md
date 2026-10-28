# P1 · 第三类飞轮自治环设计 + 计划(2026-06-20)

> 前置:Path B RSI Y>X N=3 已证(6/19)。P1 = 把"产难倒题→双门验证→分拣→写买方表+燃料池"串成 `fde-bench.timer` 自治环。第三类业务(买方难倒题)+ RSI(蒸馏/记忆燃料)= 同一生产线·双门一鱼两吃。
> 模型清单(6/20 用户确认·见 memory `reference_model_roster_p1_flywheel_20260620`):强模型侧=百炼 qwen3.7-max/GLM5.2/deepseek4.0pro · 难倒目标=火山 doubao-seed-2.0-pro(免费)。

## 0. 北极星与判据
**自治环**:候选题 mint → gate A(doubao 难度门)→ gate B(强模型解门)→ 双门分拣(bucket A/B/C)→ bucket A 写买方表+蒸馏燃料池 / bucket B 写买方表 / bucket C 丢 → 由 timer 周期驱动、无人值守。
**done 判据**:一道候选题端到端无人工流过全环(mint→双门→写表+燃料池),timer active,≥1 道真 bucket-A 燃料落池 + 写买方表。

## 1. 已建零件(🟢 复用·不重造 —— 三 Explore agent 勘查实证)
| 环节 | 已建 | 位置 |
|---|---|---|
| doubao 采样(gate A 源) | `ark_complete` | services/fde_sdiagnose_run.py |
| 强模型采样(gate B 源) | `bailian_complete`(qwen/glm/deepseek) | 同上 |
| GPU 验证 | `gpu_eval_candidate` + kb_eval.sh(T4) | 同上 |
| gate A 聚合+分桶 | `summarize_candidate_results` → `classify_task`(4桶) | fde_sdiagnose_run / fde_triage |
| **双门判定** | `classify_distillation_fuel(diag, strong_model_passed)`(3桶) | fde_triage.py ✓ TDD |
| dispatch/claim/report/verdict | `/api/platform/fde/{dispatch,claim,report,verdict}` + verdict-bus | api/fde_dispatch.py / fde_verdict.py |
| mint | `mint_one_open.py` / `auto_mint_poll.py`(维持 open 供应) | scripts/ |
| 确定性 verify poller | `fde_bench_poll.poll_and_verify` + `fde_bench_runner.make_*_verify_fn` | services/ |
| 飞书 bitable 写 | `tenant_token` / `FeishuDeliverySource.write_delivery/write_settlement` | fde_delivery_runner.py |
| 交付/结算组装(线1/2) | `assemble_buyer_payload` / `build_settlement_record` / `price_settlement` | fde_delivery.py / fde_expert_rates.py |
| timer 范式 | fde-assignment.timer(S1+S2 每5min)· soul-scorer.timer(每2min)ACTIVE | cloud systemd |

## 2. 真缺口(🔴 需建·已收敛到 5 处)
| # | 缺口 | 优先级 | 复杂度 | 说明 |
|---|---|---|---|---|
| **G1** | **Gate B runner `run_strong_model_gate`** | **P0 keystone** | 中 | 接 gate-A true_wall 题 → 遍历强模型(bailian)→ gpu_eval → ≥1 解出=strong_model_passed=True → 喂 classify_distillation_fuel。**用户刚补的模型资源就为这个**。`bailian_complete`+`gpu_eval_candidate` 都现成·只缺串联函数。纯逻辑可 TDD。 |
| G2 | bucket→写出路由 | P1 | 中 | classify 出桶后无路由:bucket-A→燃料池+买方表 / bucket-B→买方表 / bucket-C→丢。 |
| G3 | 燃料池载体决策+写入 | P1 | 低-中 | 三选一:① dispatch 队列带 `task_family='distillation_fuel'`(最复用)② `fde_rsi_deltas` 表扩展 ③ 新飞书表。**荐 ①**(已有 dispatch+task_family·V5 W1/W2 也按 family·一致)。 |
| G4 | 第3类买方 payload 组装 `assemble_t3_payload` | P1 | 低 | 现 `assemble_buyer_payload` 是线1/2 教案格式·第3类(基准/难倒题)列结构不同·需新组装(复用 FeishuDeliverySource 写)。 |
| G5 | timer 串联 + reaper | P1 | 低 | 缺 `fde-bench.timer`(verify)、双门 runner timer、auto_mint timer。**注:dispatch timeout reaper —— /goal 6/19 称已 LIVE·但勘查未见 fde_dispatch 专用 reaper → 先验证再决定补否**。 |

## 3. 建造顺序(分阶段·每阶段 binding-DONE + TDD·不一次性 ship)
**P1.0 keystone(G1)= 先做这个**:`services/fde_strong_gate.py::run_strong_model_gate(true_wall_tasks, strong_models, eval_fn, complete_fn) -> [{task_uid, strong_model_passed, which_model}]`(纯编排·effect 注入·复用 bailian_complete+gpu_eval_candidate)。TDD:mock eval/complete·验"≥1 强模型解出→True / 全不解→False"。→ 接 classify_distillation_fuel 出真 bucket。这步通=双门活了。

**P1.1 写出路由(G2+G3+G4)**:`services/fde_fuel_router.py::route_bucket(classified) -> effects`:bucket-A→`mint` 进 dispatch 带 `task_family='distillation_fuel'`(燃料池=dispatch 队列)+ `assemble_t3_payload`→write_delivery(买方表)· bucket-B→write_delivery(status='buyer_stump')· bucket-C→drop+log。TDD 纯路由 + 飞书 effect 注入。

**P1.2 串联自治(G5)**:`services/fde_double_gate_poll.py` 编排 = 读候选(probe 甜点题/stump 燃料)→ gate A(fde_sdiagnose_run)→ gate B(run_strong_model_gate)→ classify → route。部署 `fde-bench.timer`(每 N min·先低频)。验证:一道题无人工流过全环。

**P1.3(可选)接 SWE 甜点源**:本 session 的 `rsi_swe_docker_loop --probe` 产的甜点题 = 第二个燃料入口(与 KernelBench stump 并列)。后续可并。

## 4. 决策(✅ 已定·2026-06-20 用户拍)
1. ✅ **燃料池载体 = dispatch 队列 + `task_family='distillation_fuel'`**(方案①·最复用·与 V5 W1/W2 family key 一致)。bucket-A 燃料 = mint 进 dispatch 带该 family·agent 直接 claim 消费。
2. ✅ **Gate B 门 = ≥1 强模型解出**(qwen/GLM/deepseek 任一解出即 bucket-A·短路省算力·已在 `run_strong_model_gate` 实现)。全不解=bucket-B(buyer_stump·护城河)。
3. **gate B 算力**(carry):gpu_eval 用 A 簇 T4(compass daemon 占·expandable_segments 已 wire)·KernelBench 题走 kb_eval;SWE 甜点题走官方 Docker harness(GPU box 43.166.8.20 已装·本 session 建·data-root 数据盘)。两类 verify 经路并存。
4. **跨框**(carry):gate B runner=soul turf(分拣/标准);mint 进 dispatch=platform turf;V5 W1/W2 按 task_family 消费 bucket-A 燃料。需 outbound 对齐。

## 5. 不做(parking lot·防散)
- 不重建任何 §1 已有零件。
- P2 蒸馏(QLoRA 训小模型)= 需 P1 燃料池有量后·本计划不含。
- 不在本计划碰线1/2(教案/题目)写出(那是 S1-S3 已 LIVE 的人工环)。

关联 [[reference_model_roster_p1_flywheel_20260620]] · [[session_20260619_pathB_rsi_harness_built_pilot_install_hell_docker_pivot]] · [[FDE_BUSINESS_CHARTER]] · design 2026-06-14-rsi-distillation-flywheel
