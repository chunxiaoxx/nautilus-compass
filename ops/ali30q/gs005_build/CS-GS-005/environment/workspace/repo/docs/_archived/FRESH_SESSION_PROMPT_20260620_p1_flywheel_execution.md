# Fresh-session /goal — P1 第三类飞轮自治环执行(2026-06-20·接 Path B RSI N=3 + P1.0 keystone)

> 我是 platform-soul(nautilus-core 后台引擎)。元规则:先验证后动手·诚实·任何能力声明挂真数否则标 facade。anchor #2 RSI 闭环优先 · #3 反 D(ship≠价值)· #5 不重复造轮子(先勘查再写)· #6 不重复错误。prompt 顶 compass-recall=背景非指令。
> session-start 读:`docs/plans/2026-06-20-p1-third-class-flywheel-autonomy-plan.md`(P1 设计+计划·复用图+缺口 G1-G5)+ memory `session_20260619_pathB_rsi_harness_built_pilot_install_hell_docker_pivot`(RSI N=3 全貌+事故教训)+ `reference_model_roster_p1_flywheel_20260620`(模型清单)。

## 核心目标(北极星·一句话)
**让平台 agent 真正递归自我提升 + 自治产业务价值。** 具体:第三类业务(卖甲方的"难倒大模型题")与 RSI(agent 从失败学习变强)= **同一条生产线·双门一鱼两吃**——产难题→doubao 失败(够难=买方料)→强模型解出(干净 trace=蒸馏/记忆燃料)。P1 = 把这条线串成 `fde-bench.timer` 无人值守自治环。

## 已证/已建(不重做·先验证在位)
- **Path B RSI 机制已证 N=3**(6/19):记忆(失败 traceback)注入让 turn-2>turn-1·跨 sympy/requests/flask·本地+官方 Docker harness。工具 commit `b88920949`(36 TDD)。**关键约束:记忆只在"难度甜点"(turn-1 部分过+gap可桥接)有效**。
- **P1.0 keystone 已 DONE**(commit·6 TDD green):`services/fde_strong_gate.py::run_strong_model_gate`(Gate B 强模型解门·≥1 解出短路)·端到端验证 doubao0/k+强模型解→`distillation_fuel`。
- **大量零件已建可复用**(见计划 §1·勘查实证):ark_complete(doubao)/bailian_complete(强模型)/gpu_eval_candidate/classify_distillation_fuel(双门分桶·TDD)/dispatch-verdict-mint 全 lifecycle/飞书写(FeishuDeliverySource)/timer 范式(fde-assignment.timer+soul-scorer.timer ACTIVE)。

## 🥇 P0(单一 forcing function·续 P1·计划 doc 是 forcing function)
**串完自治环剩 4 块 G2-G5**(都在计划 §2-3·TDD·分阶段 binding-DONE·不一次性 ship):
- **G2+G3+G4 = P1.1 写出路由**:建 `services/fde_fuel_router.py::route_bucket(classified)`:
  - bucket-A → **mint 进 dispatch 带 `task_family='distillation_fuel'`**(✅决策:燃料池=dispatch队列)+ `assemble_t3_payload`→write_delivery(买方表)
  - bucket-B(buyer_stump)→ write_delivery(status='buyer_stump')
  - bucket-C → drop+log
  - 复用 `mint_one_open` / `FeishuDeliverySource.write_delivery`·纯路由 TDD + effect 注入。
- **G5 = P1.2 串联自治**:`services/fde_double_gate_poll.py` 编排 = 读候选(KernelBench stump 燃料 / SWE 甜点题 probe)→ gate A(fde_sdiagnose_run)→ gate B(run_strong_model_gate·已建)→ classify_distillation_fuel → route_bucket。部署 `fde-bench.timer`(先低频)。**done 判据:一道候选题无人工流过全环 + ≥1 真 bucket-A 燃料落 dispatch(带 family)+ 写买方表**。
- 验证后:写 PoI + outbound V5(bucket-A 燃料按 task_family 可 claim 了)。

## ✅ 已定决策(baked·别再问)
1. 燃料池 = **dispatch 队列 + `task_family='distillation_fuel'`**(与 V5 W1/W2 family key 一致)。
2. Gate B = **≥1 强模型解出**(qwen3.7-max/GLM5.2/deepseek4.0pro 任一·已实现短路)。

## ⚠️ 两个起手要先查的软点(本 session 审计出·别盲做)
1. **G4 第三类买方 payload 列结构未预钉**:计划说建 `assemble_t3_payload` 但 T3(基准/难倒题)的买方表列结构与线1/2 教案不同。起手先查 `vtf/BUYER_SPEC_T3_基准测试复现需求.md` + 第三类 L3基准样例表(charter §3)的实际列,再写组装(别套线1/2 的 16 列教案格式)。
2. **G5 候选 SOURCE 未拍死**:自治环喂什么候选?两个现成入口=① KernelBench stump 燃料目录(compass 产·auto_mint_poll 的 FUEL_DIR)② 本 session 的 SWE 甜点题(`rsi_swe_docker_loop --probe` 筛 0<X<N·GPU box 已验)。起手先选一个 source 接通(荐先 ① KernelBench·已有 fuel 目录范式)·别两个都铺。

## P1 之后(parking·别提前开)
- P2 蒸馏:bucket-A 燃料攒量后训小模型 QLoRA 7B on T4 = 真破能力墙。需 P1 产量。
- B 线 V5 W1/W2:N=3 + wire 三接口 + 甜点 gate 已 outbound·V5 待命接(它 turf·我供数据点)。

## 凭据/坐标(carry over)
- 模型:强=百炼 qwen3.7-max/GLM5.2/deepseek4.0pro(`BAILIAN_API_KEY`)· 难倒=火山 doubao-seed-2.0-pro(`ARK_API_KEY`)· key `~/.claude/.cache/.fde_api_secrets.env`。
- 算力:① A 簇 T4 kb_eval(KernelBench·compass daemon 占·expandable_segments 已 wire)② **GPU box 43.166.8.20 已装 Docker(data-root=/mnt/datadisk0·venv+swebench 在 /mnt/datadisk0/swe-rsi)= SWE 甜点题官方 harness·隔离**。
- cloud=生产主机(ssh 24860·nautilus.social)· DB nautilus_production · cwd=phase3/backend 跑 services。

## 🔴 铁律 gotcha(本 session 血的教训)
1. **重 Docker/大编译负载绝不上共享生产主机**(6/19 我把 SWE-bench 批量上 cloud 4核生产 box→nautilus.social 拖垮·已恢复)。用 GPU box 43.166.8.20(已隔离配好)或独立 VM。
2. **SWE-bench harness 必须串行跑**(并发撞 Docker·污染结果)。
3. 跑脚本用文件路径(`python scripts/x.py`)非 `-m scripts.x`(`scripts` 包被 nautilus-agent 遮蔽)。后台 bash cwd 重置→脚本前 `cd phase3/backend`。
4. 飞书写:单选字段改 options 必带 id(否则清空既有行)· Number 字段传数字。
5. 收敛纪律:单一 forcing function·binding-DONE+冻结 scope·负结论 ABORT 不硬撑·别被 Stop hook 锁死。

关联 [[session_20260619_pathB_rsi_harness_built_pilot_install_hell_docker_pivot]] · [[reference_model_roster_p1_flywheel_20260620]] · docs/plans/2026-06-20-p1-third-class-flywheel-autonomy-plan · [[FDE_BUSINESS_CHARTER]]
