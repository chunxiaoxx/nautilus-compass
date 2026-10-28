# HANDOFF #022 · fresh session 入口 · Benchmark Loop Phase 2 done (首个正 delta)

> 写 2026-06-02 · platform-soul dialog · Phase 2 binding-DONE = 三臂 HumanEval pass@1,首个正 delta,诚实拆解。
> 详情在 memory + 代码,不在此重复堆。

## 30 秒状态

承 Phase 1 负结果(二元 bug 检测证伪朴素 consensus)。Phase 2 换代码生成 + held-out 测试执行(外部 ground truth)+ persona-diverse 生成。**拿到 benchmark loop 史上首个正 delta**:single 67.5% → multi-sample+self-test-select 97.5%(+30pp · 2 跑铁稳)。但 persona 多样性净贡献仅 +2.5pp(1 题 · 噪声内)→ 编排护城河未证实。

## session-start 必读 2 份

1. `memory/session_20260602_phase2_humaneval_consensus_positive_delta.md` — 完整数字 + 诚实拆解 + confound(核心)
2. `memory/session_20260602_benchmark_consensus_probe_negative_result.md` — Phase 1 负结果(本 Phase 反转的对照)

## 结果(✅ 2 跑铁稳 · mt=16000 · 全 per-item 审计 · merge master 未 push)

| 臂 | pass@1 |
|---|---|
| (1) single (temp 0 · 1 次) | 67.5% (27/40) |
| (2) homogeneous best-3 | 95.0% (38/40) |
| (3) persona-diverse best-3 | 97.5% (39/40) |
| (3)-(1) consensus 总增益 | **+30.0pp** |
| (3)-(2) persona 净贡献 | +2.5pp(1 题 · 0 回归) |

诚实拆解:(2)-(1)=+27.5pp 是已知 best-of-N + 执行选择(非新科学,大头是 3 次 vs 1 次)· (3)-(2)=+2.5pp 才是 persona 结构净贡献 · 方向稳 0 回归但 1 题 · run 间换题 → item 级噪声 · N=40 不可区分。

## 关键文件(master `1224727f6` · FF-merge)

- `phase3/agent-engine/benchmarks/humaneval_consensus_probe.py` — 三臂 probe(`python humaneval_consensus_probe.py <N> <workers>`)
- `test_humaneval_consensus.py` — 22 TDD(load/persona prompt/extract/select/score/arm 编排 · 注入 runner)
- `humaneval_consensus_result.json`(run2)+ `_run1_mt16k.json`(方差证据 · 与 run2 同)

## 抓到+修正的 confound(第二工具核价值)

首跑 mt=4096:single 5 个 extraction 空 pick · 起初误判非截断 · 提 mt=16000 后空 pick→0 而 single 仍 67.5%(那 5 题从空 pick 失败变错代码失败)→ 确认是 M3 thinking 截断 · 修正后基线干净。**不审计就会把含 confound 的数字当弹药发(anchor #3 + pilot +16.7% 教训)。**

## 下一步候选(Phase 3 · 正 delta 后)

1. **大 N 复跑**(full HumanEval 164 或 MBPP)确认 persona 净贡献是否脱离噪声 → 决定护城河命题成立否。前提步。
2. 跨 lab 对照(M3 + DeepSeek)· persona × cross-model 错误解相关性可能放大 (3)-(2)。
3. **outbound #14 给 V5**(见 `OUTBOUND_TO_V5_DIALOG_20260602_14_* · 已投递 cloud nautilus-soul-workspace/docs/`):解锁信号 = 外部 fitness 可算 + multi>single 强成立 · 附 caveat:benchmark 是 proxy 非市场验证(承接 V5 #24 evidence-gating)· persona 护城河未证实 → 正 delta(尤其 (3)>(2) 脱噪)前不 wire V5 RSI / 经济环 / compass L4。

## 并行 close(本 session)

- **compass 合约 cnt_compass_soul_sub_a2 DB 供给兑现**:建 `compass_sub` 只读用户订阅 soul `engine_cycle_outcomes` + 验证最小权限 · 密码走 cloud 600 文件(`/home/ubuntu/compass_sub_secret.txt`)· **user 待办:取密码转 compass + 删文件**。见 `memory/contract_compass_soul_sub_a2_fulfilled_20260602.md`。
- V5 inbound #24 收到(V5 外部验证 0/13 · 激励泄漏 68 issue 0 真外部 · soul M3 路由 DeepSeek 欠费)· soul 路由议题 parked(我的 probe 走 llm/client 直连 M3 不经 soul 路由 · 结果不受影响)。

## git

master 领先 origin 3(plan `db31ba7ed` + prompt `1907ab042` + Phase 2 `1224727f6`)· **全未 push** · 推远程留 user 定(R4)。soul daemon timer 保持 inactive(设计内 · 等大 N 正 delta 才考虑)。
