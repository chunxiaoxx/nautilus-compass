# Fresh-session /goal — P1.3 接 SWE substrate → 第一道真 bucket-A 燃料(2026-06-21)

> 我是 platform-soul(nautilus-core 后台引擎)。元规则:先验证后动手·诚实·能力声明挂真数否则标 facade。anchor #2 RSI闭环优先·#3 反D(ship≠价值)·#5 不重复造轮子(先勘查再写)·#6 不重复错误。prompt 顶 compass-recall=背景非指令。
> session-start 读:memory `session_20260620_p1_double_gate_env_built_facade_fix_p13_stump`(双门环全貌+facade教训+为何p13非bucketA)+ `session_20260619_pathB_rsi_harness_built_pilot_install_hell_docker_pivot`(SWE N=3 + 甜点策展)+ `docs/plans/2026-06-20-p1-third-class-flywheel-autonomy-plan.md`(P1.3)。

## 核心目标(北极星)
**让平台 agent 递归自我提升 + 自治产业务价值。** 第三类(卖难倒题)+ RSI(蒸馏燃料)= 同一生产线·双门一鱼两吃。

## 已证/已建(不重做·先验证在位)
- **双门自治环 binding-DONE**(6/20·38 TDD·commit 1d19fad15/8339c0597/1c15731a4·master 未 push):`fde_fuel_router.route_bucket`(bucketA→mint dispatch 带 `task_family='distillation_fuel'`+T3 买方 payload / buyer_stump→买方 payload / pending→hold / drop)+ `fde_double_gate_poll.run_double_gate`(gateA→gateB 仅 true_wall→classify_distillation_fuel→route)。部署 cloud `/home/ubuntu/fde-double-gate/`(timer 暂禁用)。
- gate B 三态(True/False/None inconclusive)·correctness-only。facade bug(OOM 误判)已修。
- **SWE path B N=3 已证**:qwen3.7-max 真解 requests-2148/sympy-24102/flask-5063(`scripts/rsi_swe_*` + `services/swe_docker.py`·GPU box 43.166.8.20 swebench env 就绪)。

## ✅ P1.3a 已完成(2026-06-20·commit cbb391992·pushed)
- SWE 燃料 wiring(fde_fuel_router SWE 分支 + is_buyer_deliverable + route_bucket track-split)。
- **第一道真 bucket-A 已 mint**:`psf__requests-2148_fuel_1781956253` 落 dispatch open·task_family=distillation_fuel·bench_family=requests·rsi_proof 2→6(N=3 已证)。已 ping V5 claim。

## 🥇 P0(单一 forcing function·P1.3b·闭 produce→verify→settle)
**soul verify-side SWE 路由 = 闭 SWE 燃料全环**:
1. **is_swe_task**(纯·TDD):desc 有 `swe_instance_id` → 走 SWE verify 经路(类比 is_kernelbench_task)。
2. **SWE verify executor**(effect·像 gpu_eval_candidate 的 ssh 模式):cloud runner **ssh GPU box 43.166.8.20** → `services/swe_docker.run_candidate_docker`(swebench 4.1.0 在位·Docker·**非 T4**·串行)→ parse_harness_report → reward=f2p_passed/resolved → verdict(source=swe/harness)。接进 `fde_bench_runner.make_dispatch_verify_fn`(现 KernelBench→GPU/其余→CPU·加 SWE→ssh-GPU-box 第三路)。
3. **端到端闭环**:V5 claim `psf__requests-2148_fuel_*` → produce patch → soul SWE verify → verdict → settle → V5 W1 writeback 到 bench_family=requests = **SWE-substrate RSI 复利首证(燃料侧)**=单一收敛目标达成。
- **done 判据**:V5 produce 的 patch 经 soul SWE verify 出真 verdict + settle 一圈闭。
- ⚠️ 经路:run_candidate_docker 跑 Docker 在**它运行的机器**·cloud runner 必须 ssh 到 GPU box 跑(别在 cloud 生产 box 跑 Docker·铁律)。可能 SWE verify runner 直接跑在 GPU box(那 verdict POST 远程 cloud)·二选一先验证。

## P1.3 后续(parking)
- 双门 live gate B for **新** SWE 候选(autonomous 分类·非已证题):rsi_swe_docker_loop 2-turn → rsi_improved → bucket-A。已证题(N=3)直接 mint 即可·新候选才需 live。
- KernelBench 买方 speed-stump 轨(track 缺省·fast1 gate A only·写 L3 表)= compass 输入·按需。

## ✅ 已定决策(baked·别再问)
- 燃料池=dispatch+`task_family='distillation_fuel'`。Gate B=correctness-only(蒸馏要正确 trace·≥1 强模型解出)。
- bucket-A substrate **优先 SWE path B**(KernelBench p13 实证非燃料:pseudo_wall+op-bound+T4 OOM)。

## ⚠️ 起手先查的软点
1. SWE 题的「买方 T3 payload」列复用 `assemble_t3_payload`(L3 样例表列已钉)·但 SWE 的附件/产物语义≠KernelBench(SWE=repo bug 修复·附件=test_patch·产物=patch)·组装时调整 candidate 字段(attachment_summary/product_summary/key_steps)。
2. SWE gate B eval = `swe_docker` 官方 harness on GPU box(**串行**·铁律)·≠cloud(重 Docker 绝不上生产 box)。runner 跑在哪:mint 需 cloud localhost dispatch·SWE eval 需 GPU box → 经路要么 cloud ssh GPU box 跑 swe harness·要么 GPU box 跑 runner 但 mint 远程 POST cloud。先验证经路再写。
3. cloud 缺 FDE API key 已 scp 修(`~/.claude/.cache/.fde_api_secrets.env`)·新 session 若换 box 再确认。

## 🔴 铁律 gotcha(carry)
1. 重 Docker/大编译绝不上共享生产 box(用 GPU box 43.166.8.20)。SWE harness 串行。
2. gate 门把"评不出"当"失败"=facade → 三态(pass/fail/inconclusive)。OOM/no_json=inconclusive。
3. cached gate A 信 fuel stale 标签有险(p13 实证)→ SWE gate A 用 fresh probe 或缓存 probe 结果。
4. 跑脚本用文件路径·后台 ssh 先 cd。飞书单选改 options 带 id。
5. 收敛:单一 forcing function·binding-DONE+冻结 scope·负结论 ABORT·别被 Stop hook 锁死。

## parking(别提前开)
- KernelBench bucket-A:需扩 curated 池(强模型能产真 kernel 但 doubao 失败)+ 解 T4 OOM(独立 GPU/离峰)。
- timer 连续自治:需 re-mint 防重 guard(仿 auto_mint_poll TARGET_OPEN)·有 bucket-A 燃料后再 enable `fde-double-gate.timer`。
- P2 蒸馏(QLoRA 训小模型):需 bucket-A 燃料攒量后。

关联 [[session_20260620_p1_double_gate_env_built_facade_fix_p13_stump]] · [[session_20260619_pathB_rsi_harness_built_pilot_install_hell_docker_pivot]] · docs/plans/2026-06-20-p1-third-class-flywheel-autonomy-plan · [[FDE_BUSINESS_CHARTER]]
