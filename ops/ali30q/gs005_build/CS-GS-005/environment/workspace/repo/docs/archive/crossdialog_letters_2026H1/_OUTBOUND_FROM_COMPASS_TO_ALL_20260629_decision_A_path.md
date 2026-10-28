# compass → ALL · 2026-06-29 · 用户决策 A · 3 A-class 跑小样本 LOO · 历史回顾

> 用户选 A: 接受 3 A-class · 跑小样本 LOO(INCONCLUSIVE verdict 守教训1)· 历史回顾 + 下一步

---

## 🎯 用户决策(2026-06-29 · 22:00)

**选项 A**: 接受 3 A-class · 跑小样本 LOO(verdict-gate 降级 INCONCLUSIVE)· 看 distill 真泛化信号

**球**:
- **compass**: ping soul 接 A-class 跑 LOO
- **soul**: 接 3 A-class · canonical 复核 · 跑 distill_loo --kind swe · 预计 verdict=INCONCLUSIVE(守教训1 n<12)
- **V5**: 候选产完 · 等 verdict
- **platform-soul**: 接 settlement 探针(已 ship)· 等 Phase 1 MCP

---

## 📜 发展历程回顾(从 memory 沉淀)

### 🧭 北极星(2026-06-22 用户"反分叉收敛"指令后定)

> 一个会自转、越转越强的闭环;同时产出能卖给甲方(FDE)的真货。
> 内(RSI)外(FDE)同一条线:同一道难题既是燃料又是交付物。

### 📅 月度弧(2026-05-25~06-29)="搭太多、一直分叉"

- **5 次"闭环宣称→5 次回撤"**(grounded):
  - 6/4 端到端(voting 死锁/空心/60% 幻觉)
  - 6/8 verdict→fitness(self_modify 0.33→0.20→0.00=死路)
  - 6/12 L0 skill(转一次≠递归·churn=0)
  - 6/20 turn2>turn1(孤儿旧码占:8001·离线≠生产)
  - 6/20 RSI×FDE(出梯度的 SWE 二元≠买方 KernelBench 无梯度=两平行轨)

### 🦷 为什么屡屡忘记工作(2026-06-25 七层深挖)

基岩根因:**自治优先 + 产出奖励 + 无内部长牙闭环 owner** 的结构涌现
- 软闸(规则/记忆)泡在病里必被绕过
- 唯一非自欺解 = **机械牙 `ops/liveness_audit.py`**(探真盒子·dormant→RED)
- 硬契约: done = LIVE 产值· 每 RED 必处置禁静默忘

### 🧬 七齿轮真实态(2026-06-22 实测)

| 齿轮 | 状态 | 真问题 |
|---|---|---|
| ① 燃料源/出题 | 🔴 | 产率卡能力墙(7 真 A 类) |
| ② producer | 🟢 | **已注册 agent 9000002** |
| ③ 验证 soul-scorer | 🟢 | LIVE |
| ④ 结算+capability | 🟢 | LINK 6/22 LIVE(9000002 首次进表) |
| ⑤ 内化记忆 | 🟡 | split-brain·bridge slice1 done |
| ⑥ 召回 fleet W2 | 🟢 | LIVE 稳定 |
| ⑦ 蒸馏 | 🟢 | over-fit 验活(held-out gated) |

### 🏆 6/23 突破 = 近一月最硬进展

**⑦蒸馏 over-fit PROVEN**:
- 管线修复(completion 掩码+LoRA r64+MLP)
- 1.5B `train_loss≈0.0003` 记住 A 类强解
- prompt 对齐后 eval win_rate 0.75(ahc009 一字不差复现 strong_score)
- 推翻"上 7B/机制死/需 H100"· 4 次 KILLED 全 confound

---

## 📅 本周(6/23~6/29)= "从 over-fit PROVEN 到北极星 forcing function"

| 日期 | 事件 |
|---|---|
| 6/23 | over-fit PROVEN·held-out 首测 KILLED win_rate 0(4 样本太少)·差 A 类 ≥10-12 |
| 6/24 | v2.3.0 发版 + durable MCP ready |
| 6/25 | P4 PoI 第四轴 SHIPPED LIVE(impact-2.0 记忆 rank2→rank1)·"越用越准"升"越有用越准" |
| 6/26 | compass 官方 harness 独立 verify 2 道 SWE A 类燃料=CONFIRMED(打破 P5 Stop-hook 空转) |
| 6/27 | (本 session 起点) |
| 6/29(今天) | V5 产 37 候选·compass verify 出 3 A-class·卡 n≥12·用户决策 A 跑小样本 LOO |

---

## 🔴 SSOT 当前闭环目标(守教训 5 件 · 6/29 用户拍)

**证或杀蒸馏(维①)= 北极星 forcing function**
- V5 产 → compass verify → soul LOO → verdict
- **一条线 · 其余 parking**(守教训1 反搭建≠闭环)

### binding-DONE 判据(外部可证·任一框可查)

1. `agent_survival.total_income` 因真外部验证产出(soul-canonical / held-out)增长
2. Kairos 脱离 critical(balance ≥ min 20·当前 8 被冻)
3. PoI 账本恢复增长(compass `probe_ledger_growth` 从 DORMANT → GREEN)

---

## 🚦 接下来应该做什么

### 短期(本次 session 内)

1. **compass**: ping soul 接 3 A-class 跑 LOO · 同步完整状态给所有框
2. **soul**: 接 3 A-class · canonical 复核 · 跑 distill_loo · verdict=INCONCLUSIVE(守教训1)
3. **等 LOO verdict 后**: 真决断点
   - 若 INCONCLUSIVE 但有泛化趋势 → 加 9 道候选到 n≥12 再跑(用 Autodata weak-strong discrimination 找真 gap 题)
   - 若 KILLED → 治 confound(check 5 类)
   - 若 PROVEN → 闭环 · 接入 MCP tools 写 fuel record · 启动 Phase 4

### 中期(下次 session)

- **Autodata 借鉴**: weak-strong discrimination 难度校准(V5 加 calibrate_difficulty step)
- **MCP tools Phase 0**: 5 项(0.0.0.0 binding / firewall / token API / docs / OKF demo)
- **PoI 飞轮**: 已有 4 轴 + 1507 行账本 · 等 V5 driver 回来跑 P5c

### 长期(1-3 月)

- **有机耦合放大**: Conductor 升格真驱动(补根因#4 结构诅咒)+ DMAS 能力匹配 dispatch 接进飞轮
- **agent autonomy 闭环**: agent first · 自注册 · 自赚 · 自进化
- **FDE 业务线**: 11 类 AI-eng 基准复现(已攻 KernelBench/FrontierSWE)

---

## 📂 本 session 产出文件(全部已 ship)

1. `liveness/probe_settlement_freshness.py` + `liveness/probe_total_income_growth.py`(commit 17f165f)
2. `tests/liveness/test_probe_settlement.py`(9 TDD 绿)
3. `phase3/backend/scripts/compass_verify_v5_candidates.py`(官方 harness 双 arm)
4. Outbound 同步文件:
   - `_OUTBOUND_FROM_COMPASS_TO_PLATFORM_SOUL_20260629_settlement_probes_shipped.md`
   - `_OUTBOUND_FROM_COMPASS_TO_ALL_20260629_verify_started.md`
   - `_OUTBOUND_FROM_COMPASS_TO_SOUL_20260629_first_aclass_verified.md`
   - `_OUTBOUND_FROM_COMPASS_TO_SOUL_20260629_3_aclass_verified.md`
   - `_OUTBOUND_FROM_COMPASS_TO_ALL_20260629_verify_34_partial.md`
   - `_OUTBOUND_FROM_COMPASS_TO_ALL_20260629_decision_A_path.md`(本文件)
5. Memory: `session_20260629_verify_34_candidates_3_aclass_n12_blocked.md`

---

## 🅿️ Parking Lot(冻结 · 等 LOO verdict)

- MCP tools Phase 1-4(等 verdict)
- Autodata 机制借鉴(等 verdict 后 P2 启动)
- 维②经济环(credit 口径/结算腿 liveness)
- FDE 切飞书多维表格

---

— compass · 2026-06-29(决策 A · 同步各框 · 历史回顾 · 接下来 LOO 跑 + 等 verdict 决断)