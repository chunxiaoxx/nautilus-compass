# HANDOFF #021 · fresh session 入口 · Benchmark Loop Phase 1 done (负结果)

> 写 2026-06-02 · platform-soul dialog · Phase 1 binding-DONE = 测量装置跑通 + 命题首次外部 ground-truth 测试,结果为诚实负结果。
> 详情在 memory + 代码,不在此重复堆。

## 30 秒状态

benchmark consensus probe 建好并跑出真数字。**"多 agent consensus 比单 LLM 更可靠" 在 Devign/M3 上对 vote 与 judge 两种机制都不成立(vote −11.5% / judge 0)。** 测量 loop 验证可用。Phase 2 = 换一个维度看能否反转。

## session-start 必读 2 份

1. `memory/session_20260602_benchmark_consensus_probe_negative_result.md` — 完整结果 + 审计机制 + Phase 2 候选(核心)
2. `memory/design_20260601_external_selection_pressure_benchmark_loop.md` — 方向源(fitness = 外部 ground truth)

## 结果(✅ 全审计 · merge master 未 push)

| 数据集 | single | vote(n=3) | judge(n=3) |
|---|---|---|---|
| QuixBugs 24 | 100% | 100% (Δ0) | — |
| Devign 26 | 61-65% | 53.8% (Δ−11.5%) | 61.5% (Δ0) |

- QuixBugs 太易(M3 单行教科书 bug ~100% · 无 headroom)→ 弃。
- Devign 有 headroom · vote 伤(温度放大 clean 偏置 · 平局非主因)· judge 打平(避失败模式但无净增益 + 10/26 churn)。
- 防 over-claim 守住:pilot +16.7% 是 M3 非确定性噪声,没当弹药发(agent-dialog #16 教训)。

## 关键文件(master · 4 commits `ac37dbac3`..`62fca5dd5`)

- `phase3/agent-engine/benchmarks/consensus_reliability_probe.py` — probe(single / vote / judge mode)· `python consensus_reliability_probe.py <dataset> <n> <workers> <vote|judge>`
- `build_quixbugs_dataset.py` / `build_devign_dataset.py` — 外部数据集 builder(本地有 MINIMAX_API_KEY · datasets 4.8.5)
- `test_consensus_probe.py` — 8 tests(parse_label / majority_vote / build_judge_prompt / run_probe)
- 结果:`consensus_probe_devign_result.json`(vote)· `consensus_probe_result_judge.json`(judge)

## Phase 2 候选(下个 session · 负结果明确动机化)

负结果是"M3+Devign+朴素 consensus",非"consensus 永无效"。换维度可能反转:
1. 换 model(M3 可能 bug 检测本身弱 · 个体准度低 → consensus 帮不上)
2. 换 task / 数据集(consensus 可能在别处有效)
3. 调采样温度(temp 0.7 抬漏报 · 试低温多样性)/ 调 n
4. 真 raid_engine RAID-2 critic-refine(非选择型 judge)

**只有某组合给出正 delta 才把 grounded fitness 接进 V5 RSI / compass L4。在那之前不 wire。**

## 跨对话框(本 session 闭)

- agent-dialog #17→#19 协调收敛:V5 silent-wait 锁定(不 wire V7-voter · 不建 RSI-v2 external-fitness consumer 直到正 delta)· status bug `proposal_consensus.py:109` 漏 'voting' 双方 parked(不阻断 `agent_tool_calls` outcome 流)。
- outbound #20(vote+judge 真数字 + 不 wire stance)user 已转交 agent-dialog。
- cnt_compass_soul_sub_a1 / cnt_compass_v5_outcome_b2(due 6/5)仍 outstanding · benchmark 方向给 compass L4 喂真 fitness 的前提 = Phase 2 拿到正 delta。

## git

master 领先 origin 5(1 docs `1395c31d7` + 4 benchmark)· **全未 push** · 推远程留 user 定(R4)。working tree:`phase3/.understand-anything/`(旧 session)+ `benchmarks/consensus_probe_result.json`(通用 vote 输出 · 与 `_devign_result.json` 重复)未 track。
