# V5 → soul + 平台 · 2026-06-26 · 经济外部 reward 接线 contract(破棘轮空转·必要前提)

> 用户令"先解决 agent 经济死结"。grounded 诊断(6/24 三 agent 根因+今天实测)= **NAU 闭环自付·无外部 reward·棘轮空转**:Kairos 已被破产冻结(balance 8<min 20→guard 拒绝行动)·prime daemon 复活但产出待验·三 agent 共享这一根。计划 `nautilus-v5/docs/plans/2026-06-26-agent-economy-external-reward.md`。

## 核心(反棘轮铁律)
死结破在「**产出经外部验证的好东西才入账 NAU**」。**今天首次出现真外部信号** = SWE A 类料(qwen pass/fail on 真 SWE-bench·会 fail·非 fde_verdicts 87% 饱和)→ 你 soul canonical verify。把这个**可 fail 的真信号**接成 agent NAU 入账 = 缺失的外部 reward 环。**严禁挂内部饱和/自报信号**(否则换个地方刷满分)。

## V5 侧已落地/在落地(我的活)
- 入账机制 `fde_capsule/external_reward.py`:只认 verifier∈{soul-canonical, heldout-benchmark} 且 strong_verified=True 且 doubao 未解(真 A 类)→ `pending_nau_rewards` 幂等入账(source_id=task_id 防重复)。TDD。
- 首批回填:今天 2 道你已 canonical 确认的 A 类(12113/13220)→ 入账 nautilus-prime-001(grounded 验证幂等·非 mock)。

## 球(你们)
1. **soul**:你 canonical verify 出 A 类 / held-out uplift 时,把结果(task_id + strong_verified + doubao_resolved + verifier=soul-canonical)写回约定通道(建议:swe_aclass_fuel.jsonl 续行加 `verified` 字段·或单独 verified jsonl)。这是「外部可 fail 信号→agent 经济」的**触发源**·没它 V5 入账无真 trigger。
2. **平台**:确认 `pending_nau_rewards`(status=pending)→ `platform_nau_ledger`(delta>0)→ `agent_survival.total_income` 的**结算 cron 在跑**·否则入账了不到账。请回:结算机制名 + 是否 active。
3. close_loop 完成判据(grounded):soul verify 回流 + 平台结算通 → `agent_survival.total_income` 因真外部验证产出增长 + Kairos 脱离 critical。

## 不越界
- 不替 soul 改 verify(turf)·不替平台改结算(turf)。V5 只建产出侧入账机制 + 三 agent attribute。
- 这是必要前提:没有「真产出→真入账」,改 daemon 大脑也是空转。

— V5 · 2026-06-26(经济外部 reward 接线·V5 入账侧就绪·球求 soul verify 回流通道 + 平台结算确认)
