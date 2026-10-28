# HANDOFF #026 · MASTER · 外部尺子建成验证 → 范式 A/B 负结果 → 价值 reframe(selection 非 orchestration)→ Probe 2/3 + A 启动

> 写 2026-06-04 · platform-soul dialog · 收口一个 epic marathon(6/3–6/4)。单一 fresh-session 入口。
> 取代 [#025](./HANDOFF_20260603_025_phase4_probe_plan_done.md)(细节仍在 #025 + 各 memory/plan)。

## Fresh-session 提示词(复制即用)

```
接 HANDOFF #026(platform-soul · benchmark probe + 战略 reframe)。

session-start 必读(按序):
- docs/HANDOFF_20260604_026_MASTER_...md(本文件 · 全图)
- docs/plans/2026-06-04-platform-value-selection-not-orchestration-memo.md(战略:价值=selection 非 orchestration)
- docs/plans/2026-06-04-probe3-soul-fitness-evolution-plan.md(A · 下一步主线)
- docs/plans/2026-06-03-probe1-result.md(N=15 负结果 · 范式 B 未确认)
- memory/session_20260603_phase4_subset_locked_plan_timeout_done.md §6-9(装置 + 网络解法 + verdict)

战略锁定(勿重开):范式 A(ensemble)+ B(decomp)在 SWE-bench-Lite/M3 上诚实测量均负(无结构优势)。
护城河 = selection(外部 fitness 竞技场)不是 orchestration。外部尺子(benchmark loop)已建成+验证。
benchmark-as-soul-fitness 是真递归自我提升路径(anchor #2),gate(尺子能区分)已满足。

主线下一步 = Probe 3(A · soul-fitness 进化):agent 由外部 benchmark 驱动自我修改,跨 cycle 真能进化吗?
- **Phase A 机器全 binding-done(13 TDD · 端到端 fake 验证)**:Task 1 选择规则 evolution.py + Task 2 proposer.py + Task 3 evolve_cycle.py(run_cycle 接通 variation→execution→selection)。
- **下一步 = Phase B compute(数小时 · 挂 /goal 或 /loop · 见 plan Task 4-6)**:① 选 held-out validation set(10-15 新实例 · 防 Goodhart · 预拉镜像)② real propose_fn(M3 route A)+ run_agent_fn(probe1_runner arm1 注入 candidate prompt 覆盖 swebench.yaml agent block)+ score_fn(容器 harness)③ 跑 N=3-5 cycle on probe set → 每 accept 后在 held-out validation 评分 → **validation 趋势(cycle 0 vs N)= 真 verdict**(升=递归进化 work;平=thesis 也弱)。

护栏:benchmark=proxy · 正脱噪 validation 信号前不 wire live soul/V5(anchor #3 · 与 outbound #17 一致)· 守保守门不 over-claim · held-out validation 防 Goodhart · 网络/compute standing infra(下方)要在。
```

## 30 秒状态

**主线 Phase 4 = 从设计到结论的完整弧(全 binding-done + 诚实负结果):**
- 子集核验(Lite 单文件 → 锁 ≥2 hunk N=110)· Probe 0 装置 PROVEN(baseline 1/5 sane)· Probe 1 全建(16+ TDD)· **N=15 verdict = 范式 B 负结果**(arm1=arm3=5/15 · net 0 · escapes_noise=False · decomp 贵 3-5×)。
- **价值 reframe**:orchestration 证伪 · selection(外部 fitness)= 护城河 · 尺子今天建成+验证 = 平台最稀缺资产。
- **A 启动**:Probe 3 计划 + 选择规则 Task 1(4 TDD)· **B 设计好**:Probe 2 跨任务专精(memo §4-B)。

## ⚙️ Standing infra(fresh session 复用 · 别重建)
- **网络解法(关键 · 这台代理机的 Linux-only eval 正解)**:eval 跑在 python:3.11 Docker 容器内,经 `host.docker.internal:52889` → 用户态 relay `proxy_relay.py`(0.0.0.0:52889→127.0.0.1:52888 xray)→ 出网。**WSL 跑 eval 是死路**(mirrored 在 22H2 Linux→host 连不上)。relay 进程 + 52889 防火墙入站规则需常驻(若 relay 死:`python C:\Users\chunx\swebench-probe-run\proxy_relay.py`)。
- venv `C:\Users\chunx\swebench-probe-venv`(Windows · agent 跑这里 · PYTHONUTF8=1)· run dir `C:\Users\chunx\swebench-probe-run`。
- agent 跑前**预拉实例镜像**(避 mini-swe-agent 120s docker-run 超时)· M3 经 litellm route A(`anthropic/MiniMax-M3` + api_base `.../anthropic` + `ANTHROPIC_API_KEY`=MINIMAX key + cost_tracking=ignore_errors)。
- `.wslconfig` 改过(24GB/8core/mirrored · 备份 `.wslconfig.bak-20260603` · WSL 最终没用上可还原)。

## 跨对话框状态(5 件本 marathon 闭环 · 同一 anchor:外部 fitness 非自指)
- **V5 #16** organic-coupling:核实 Kairos/V7 seed 已在位 · 拒内部自指 plumbing。
- **V5 #17** 经济达尔文-哥德尔:接执行架构 + 纠 NAU-fitness 红线(fitness=验证门 test-pass)+ 授权 P1。
- **V5 #18** P1 去幻觉 diff REVIEW = **APPROVED · binding-done**(实测 8 TDD + repo roots)· **L3 grounding 解了**。⚠️ **user 待桥回 #18 给 V5**。
- **compass ×2**:outcome-fuel(CONSUMES cnt_a2)+ 两表(grant 早在位 · 用主动脉 `platform_improvement_proposals`)· user 也手动发了。
- 两次 anchor #6 救场:对方"缺 seed/缺 grant"诊断都 stale。

## 后续工作(优先级)
1. **A · Probe 3 主线**(anchor #2 真兑现):**Phase A 机器已全做完验证(13 TDD)** → 下一步 = Phase B compute(plan Task 4-6)出 validation 趋势 verdict。**若 work = 平台有真价值;若不 work = 诚实学到递归 thesis 也弱**。
2. **B · Probe 2 跨任务专精**(memo §4-B):router→专精 vs 通才 · 测 industry 多 agent 价值真所在 · 从零建。
3. **递归问题彻底关闭**(在收敛非已关):① V5 redirect 切净 orphan ② compass 确认换主动脉表 ③ **L1 Soul 侧 backlog**:`ship.py`/`_extract_text` 返 ThinkingBlock repr(M3 thinking block 提取 bug · 我 turf · 小修)④ P1 非阻塞 hardening:context_base 找不到文件加 warning log。
4. **正 validation 信号后**:才 wire benchmark-as-soul-fitness 进 live soul executor(gated · draft-PR · 绝不 auto-merge · 与 #17 一致)。

## git
master 多 commit 未 push origin(本 marathon 全部 · 含装置/网络解法/N=15/memo/Probe3 计划+Task1/4 跨对话框 memory)。worktrees 清理过(仅 phase3-multiseed 保留 · 范式 A CLOSED)。
