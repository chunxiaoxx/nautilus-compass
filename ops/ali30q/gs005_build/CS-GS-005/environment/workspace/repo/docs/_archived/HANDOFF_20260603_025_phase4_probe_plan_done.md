# HANDOFF #025 · Phase 4 范式 B probe — 子集已锁 + Probe 0/1 计划出 + timeout 修复

> 写 2026-06-03 · platform-soul dialog · 接 [HANDOFF #024](./HANDOFF_20260603_024_phase4_subset_then_plans.md)。
> 本 session 三个 handoff 项全 binding-DONE:子集核验 → writing-plans → timeout 修复。**Probe 主体未写**(守"先 plan")。

## Fresh-session 提示词(复制即用)

```
Benchmark Loop Phase 4 · 范式 B(division-of-labor)probe — 继续实现 Phase A 余下 Task,Phase B/C 待 cloud

背景:Phase 1-3 范式 A(ensemble/consensus)已证伪。范式 B 可证伪 probe 设计已锁,Probe 0/1 实现计划已出(11 任务 3 阶段)。子集已锁 Lite+≥2 hunk N=110。LLMClient.chat timeout 修复已 merge master。

session-start 必读:
- memory/session_20260603_phase4_subset_locked_plan_timeout_done.md(本 session 全貌 + 子集发现 + 计划结构)
- docs/plans/2026-06-03-paradigm-b-probe-0-1-implementation.md(11 任务实现计划 · master d56fc90c7)
- docs/plans/2026-06-03-paradigm-b-division-of-labor-probe-design.md(设计 · §10 子集核验结果)

Phase A 本地 Task 2/4/5/6 已做(18 TDD green · merged master)= escape_noise_stats(arm-agnostic verdict)· swebench_probe/{subset_loader,predictions,budget}。剩:
- Task 7 M3 model adapter — 依赖 Task 3 确认 mini-swe-agent 的 query() 真实签名,建议 cloud 装好 scaffold 后再建(避免对未确认 API 编程)。
- 需 cloud VM+Docker:Phase B(Task 3 vendor mini-swe-agent + Task 8/9 Probe 0 冒烟)· Phase C(Task 10/11 Probe 1)。
注:子目录用 `swebench_probe/` 不是计划写的 `swebench/`(避免阴影官方 swebench pip 包)。

护栏:benchmark=proxy 非市场验证 · 正脱噪信号(escapes_noise True on M3)前不 wire V5 RSI/经济环/compass L4(anchor #3)· 复用 PR#127 stats+_chat_safe(anchor #5)· diverge/converge 分离 · Probe 1 不过则省全 2×2 · R1 drift 自停。
```

## 30 秒状态

- **子集核验 binding-DONE**:SWE-bench **Lite 是单文件构造**(全 300 gold patch 单文件,多文件=0)→ criterion 退化为 ≥2 hunk=**N=110**(用户锁)。Verified 才有 71 多文件(defer)。`decomp` 因子靠 localize→edit→test 流水线分解(非 per-file),单文件可测。artifact `swebench_lite_core_subset.json` + counter + design §10 · commit `8c563554d`。
- **Probe 0/1 计划 binding-DONE**:`docs/plans/2026-06-03-paradigm-b-probe-0-1-implementation.md` · 11 任务 · Phase A 本地 TDD / Phase B-C cloud+Docker · commit `d56fc90c7`。
- **Task 1 timeout 修复 binding-DONE**:`messages.create` 透传 `timeout=`(默认 180s)· 4 TDD green · no-ff merged master `3e402e4b2` · worktree 清理 · master 复验 4 passed。
- **Phase A 本地 Task 2/4/5/6 binding-DONE**(用户选"继续一批"):escape_noise_stats(arm-agnostic `aggregate_paired_multiseed`)+ swebench_probe/{subset_loader,predictions,budget}· 18 TDD green · no-ff merged master · 22 passed 复验 · 目录 `swebench_probe/` 避阴影官方包。

## 下个 session 第一步建议

Phase A 余下 5 个 Task 全本地可 TDD(无 Docker),按计划逐个走。最有复用价值的是 **Task 2**(把 phase3-multiseed worktree 的 `binom_sign_test`/`aggregate_multiseed` port 成 arm-agnostic 共享模块),因为 Probe 1 的 verdict 直接依赖它。Phase B/C 需准备 cloud x86 VM(8核/16G/120G/Docker · `--cache_level=env` 忌 instance)。

## git

master = 子集 commit `8c563554d` + 计划 `d56fc90c7` + timeout merge `3e402e4b2` + 本 handoff(均未 push origin · 加上 #024 前的设计 2 commit + handoff)。`.worktrees/phase3-multiseed` 保留(范式 A CLOSED · PR #127)。soul daemon timer 保持 inactive;nautilus-backend active(#024 session F2 restart 过)。

## cloud 决定(6/3 用户拍板 · 已更新)

- **就在本地机器跑**(实测 64GB/12 核/167GB 空闲 >> 需求 · 无需 VM)。`.wslconfig` 已调 4GB/4核→24GB/8核(备份 `.wslconfig.bak-20260603`)· Docker 引擎复活 23.5GB/8CPU · docker-in-WSL 验证 OK。
- **Task 3 已实测 binding-DONE**(`docs/plans/2026-06-03-paradigm-b-task3-scaffold-api-notes.md`):swebench harness Linux-only(eval 必须 WSL)· 不用自写 Model 类(配自带 LitellmModel)· **litellm route A `anthropic/MiniMax-M3`+api_base 实测通 + M3 原生 tool-call 通** · `cost_tracking=ignore_errors`。Windows venv `C:\Users\chunx\swebench-probe-venv` 装好(仅用于 Windows-side introspection;真跑在 WSL)。
- runbook:`docs/plans/2026-06-03-paradigm-b-cloud-runbook.md`(`8baa26e1e`)· requirements pin 在 `swebench_probe/requirements.txt`。
- **Probe 0 装置 PROVEN end-to-end · flask-4045 RESOLVED 1/1**(`docs/plans/2026-06-03-paradigm-b-probe0-milestone.md`):M3→mini-swe-agent→Docker→patch→官方 harness→外部验证 resolve。**eval 不走 WSL**(Win11 22H2 mirrored Linux→host 连不上 · 死路)→ **跑在 python:3.11 容器**(挂 docker socket + 经 `host.docker.internal:52889`→`proxy_relay.py`→xray 出网)。agent 在 Windows venv 跑(预拉镜像避 120s 超时)。standing infra:relay 常驻 + 52889 防火墙规则 + venv `C:\Users\chunx\swebench-probe-venv` + run dir `C:\Users\chunx\swebench-probe-run`。
- **Probe 0 COMPLETE = baseline 1/5 resolved(20%)SANE**(flask-4045 ✓ · 5 个全真 patch · 0 empty/error · `swebench_probe/probe0_result.json`)。装置全验证。`.wslconfig` 改过可还原(WSL 没用上 · eval 走容器)。standing infra(relay + 52889 防火墙 + venv + run dir)复用即可。
- **Probe 1 装置端到端 PROVEN**(R3 override · Task 10+11 全 merged · `decomp_solver.py`/`budget.py`/`probe1_runner.py` · 16 TDD)= arm1(stock)vs arm3(decomp 隔离上下文)在 fresh 容器跑、matched BudgetedModel token cap、双臂出真可评分 patch。**SMOKE flask-4045@600k:arm1 514c/0-1 · arm3 495c(3 隔离阶段 227k tok)/0-1**(1 题非判定 · 噪声内)· 官方 eval 双臂跑通 0 error。
- **Probe 1 首个 VERDICT done(/goal 驱动)· natural-budget N=5**:**arm1 mono 1/5 · arm3 decomp 3/5 · raw +40pp** · **escapes_noise=FALSE**(N=5/1-seed · sign p=0.625 · 统计上噪声内)。**诚实**:+40pp 是大 hint(远超 Phase 3 +1.83pp)+ 说明尺子有分辨力,但**不 over-claim**(保守门拦住)。`docs/plans/2026-06-03-probe1-result.md`。
- **Probe 1 N=15 VERDICT(/loop · 6/4 · 负结果)**:加 10 难实例 → **arm1 5/15 · arm3 5/15 死平局 · net 0 · escapes_noise=False**。N=5 +40pp 是噪声(没扛住 scaling)· **arm3 烧 3-5× 算力打成同 resolve = decomp 严格更差**。范式 B 上下文隔离**未确认=负结果**(同 Phase 3)。**但尺子 works**(抓假 hint + 稳定诚实)。给 V5 #17:别靠 multi-agent 作 fitness,靠验证门。benchmark-as-soul-fitness 方向 intact。详 `docs/plans/2026-06-03-probe1-result.md` N=15 段。
- ~~下一步 scale +40pp 脱噪~~(已做 = 负)· 真下一步候选:strict matched-binding budget 复测(cap ~800k 看 decomp 是否更糟)/ 换更难数据集(Verified 多文件)/ 直接进 benchmark-as-soul-fitness wiring(尺子已验证可作 fitness)
- ~~scale N(→110)+ 2-3 seed → 看 +40pp 脱噪否~~ → escapes_noise=True(跨 seed/M3+DeepSeek)才确认范式 B · 加 strict matched-binding cap 对照。**正脱噪前不 wire soul-fitness**(`docs/plans/2026-06-03-benchmark-as-soul-fitness-design.md` gated 在此)。cap 校准:arm1 natural 128k-809k。/loop+/goal 提示词见 memory §8/§9。standing infra(relay+52889 防火墙+venv+run dir+镜像)在。详 memory §6-9。

## cross-dialog(不抢不催)

V5 outbound #15 已投(F2 voting 死锁已修+验 · executor check-stage 空心揭穿 = 内部飞轮 ship 空)。check-stage gap 由 V5/agent 侧决定是否追,平台侧不擅自修(自指再投资 · anchor #3)。
