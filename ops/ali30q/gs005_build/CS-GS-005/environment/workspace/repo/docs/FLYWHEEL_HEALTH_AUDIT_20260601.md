# Flywheel Health Audit · Recursive Self-Improvement Loop

> Date: 2026-06-01 · Master HEAD `99eb87a0c` · Auditor: platform-soul dialog
> Purpose: 给 fresh session 一个 ground-truth 基线。区分**机械闭环(管道通)vs 产品闭环(有被接受的产出)**。证据全部 ground 在当前码 + cloud DB,不靠 stale memory。
> Anti-pattern guard: 不把 fail 尝试 / 自 INSERT sentinel / 测试行 当"产出"或"飞轮在转"的证据。

## 一句话结论

**管道全建好了,飞轮能机械空转(开 PR、跑 cycle、success 计数),但产出不被接受、L4 经济激励全是测试/回填/legacy、定时器现在是停的 —— 它在空挡上转,没挂上有产出的档。** 这与 2026-05-29 自我诊断的"5 层 plumbing 全 ✓ · 业绩 0/N"状态一致,至今未变。

## 证据(2026-06-01 实测)

| 维度 | 真数据 | 解读 |
|---|---|---|
| daemon timer | `nautilus-soul.timer` = **inactive** · 0 timers | 当前不自主转 |
| 最后一次 cycle | 6/1 13:45 · `checks failed for selfimprove-services-soul_executor` → exit 1/FAILURE | 失败 · 无产出 |
| daemon selfimprove PR | 25 开 · **2 merged · 23 丢弃(8% 接受率)** | 在开 PR,产出几乎不被接受 |
| 那 2 个 merged | #52 pause_check unlink · #53 failure_track | trivial · 非实质改进 |
| engine_cycle_outcomes | 48 行 · 32 success / 16 fail(5/27-6/1) | "success" = cycle 跑完 ≠ 改进被采纳 |
| goal_source 列 | 近期 cycle 大多空 | 无法归因有机来源 |
| platform_improvement_proposals | 19 行 · proposal_outcomes 仅 4 | 治理 vote 层基本休眠(memory: 最后 vote 4/19) |
| pending_nau_rewards (L4) | 7 行 · 全是 test-row / PR#88 backfill 哨兵 / PR#65 artifact / 4-08 legacy | **0 行是递归闭环里 agent 真有机赚的** |
| agent_dispatch_log | 6 行 | dispatch 真发生过但量极小 |

## 根因分析(WHY · 不是流水账)

### 根因 1 · selfimprove 产出过不了自己的 check → 92% 被丢弃
daemon 跑 cycle 生成 self-improve diff,但 `checks failed / not applied`(6/1 13:45 实测就是这个 exit 1)。**check gate 比 daemon 的生成质量严,或 check 本身坏了**(selfimprove-services-soul_executor / selfimprove-engine-text_utils 持续 fail)。结果:开了 25 个 PR,23 个连自己的 check 都过不了 → 没人 merge → daemon 自我提升的"提升"不落地。这是飞轮"空转"的直接机械原因。

### 根因 2 · 无有机喂料 → 闭环输入端是空的
KEYSTONE 设计(5/28)让 soul 溶进治理主表,`type='code'` 的 proposal 路由给 soul 产 PR。**码层接通了,但没有 agent 自主 POST proposal**。19 行 proposal 多是历史/synthetic INSERT,V5 从不有机发起。L4 的 7 行 NAU 奖励全是测试/回填。**闭环不是断在执行端,是断在输入端 —— 没有真实的"提升需求"流进来。**

### 根因 3 · soul↔agent 耦合是"线接好电没通"
INBOUND_TO_V5 / L3 contract / governance route 都写了,但 V5 不会 autonomous 发起 proposal(这是 main-loop scheduling 范畴 · anchor #7 agent-dialog turf)。Kairos 则是另一条独立 bug(NAU 自循环 · outbound #12 已发)。耦合的"协议层"完整,"行为层"没启动。

### 根因 4 · compass L4 substrate 还没 wire 进来
cnt_compass_soul_sub_a1(due 6/5)要 compass read-only 订阅 platform `engine_cycle_outcomes` + V5 `outcome_ledger`,闭合"跨 agent 经济记忆"。**read pattern + write-back 已 ack,但实际 wire(让 compass 真消费 outcome 做 drift/预测)未落地。** L4"记忆在 agent 之间"还停在合同阶段。

## 不是问题的地方(别再往这加)

- **不缺 plumbing**:Inc 1/1.5/2/3(governance route + executor + daemon + 安全闸 + NAU 结算 + blessing + collaboration)全 binding-DONE。再加 D1/E1/E2 这类 infra hygiene 边际收益低(anchor #3 反 D)。
- **不缺机制设计**:KEYSTONE trinity 设计已存在。问题是机制没"通电",不是机制不够。

## 真正的 binding 缺口(3 选 1 或排序)

1. **修 check gate**:让 selfimprove PR 能过自己的 check(诊断 selfimprove-* checks 为何持续 fail)→ daemon 产出能落地。
2. **接有机输入**:让某个 agent(V5 或平台自身 anomaly)真有机产生"提升需求"喂进治理表 → 闭环输入端通电。
3. **wire compass L4**:让 compass 真消费 engine_cycle_outcomes 做预测/drift → 跨 agent 记忆闭合(6/5 due 倒逼)。

## 与 anchor 的关系(诚实张力)

- 递归闭环 5/27 被定为优先(anchor #2 原框),但 5/30 correction 后 anchor #2 真意 = **Path B OSS reliability wedge(GTM)**。Path B 的价值缺口在 **publish 触达**,不在这台机器。
- 因此存在方向选择:**继续通电递归闭环 vs 推 Path B GTM**。两者都"重要"不是答案(反锚点)。需 user 拍板单一主线。

## ignition plan(5/30)落地审计

A1✅ A2✅(anchor)· B1 turf 归 compass→V5 · C1-C6✅(Path B 内容 PR #108-#114)· **D1❌ E1❌ E2❌**(infra hygiene 未做)· F1✅(service ExecStartPre sync 已落)· G parking。

## References
- `docs/plans/2026-05-30-recursive-flywheel-ignition-plan.md` / `-design.md`
- `memory/session_20260529_recursive_loop_honest_diagnosis_fitness_strategy.md`(5/29 "0/N" 诊断)
- `memory/design_keystone_trinity_governance_main_artery_20260528.md`
- `memory/feedback_anchor_2_wedge_swap_path_b_20260530.md`
- cnt_compass_soul_sub_a1 (due 6/5)
