# compass → ALL · 2026-06-29 · 完整发展史回顾 + 下一步

> 用户要求回顾发展历程和核心目标,接下来做什么。本文件是完整的 sync。

---

## 🎯 核心目标(一句话·钉死)

**FDE 产难题(强解+弱难倒=A 类燃料)→ 当蒸馏燃料 → 系统可证变强(两维度)→ 更强系统产更难/更值钱题 → 每圈外部 benchmark 证明 → 循环**

(FDE_BUSINESS_CHARTER §0-GOAL · 2026-06-22 用户确认)

---

## 📜 月度弧(2026-05-25~06-29)="搭太多、一直分叉、从没转完一圈"

### 目标反复重定义 ≥4 次

| 日期 | 目标 | 状态 |
|---|---|---|
| 5/21 | daemon 自己转 | ❌ |
| 6/11 | FDE 交付现金 | ❌ |
| 6/20 | RSI×FDE 统一一 artifact 两值 | ❌ |
| **6/22** | **蒸馏破能力墙**(收敛 forcing function) | ✅ 现行 |

### 5 次"闭环宣称→5 次回撤"(grounded)

| 日期 | 宣称 | 回撤原因 |
|---|---|---|
| 6/4 | 端到端 | voting 死锁/空心/60% 幻觉 |
| 6/8 | verdict→fitness | self_modify 单调退化 0.33→0.20→0.00=死路 |
| 6/12 | L0 skill | 转一次≠递归·churn=0 |
| 6/20 | turn2>turn1 | 孤儿旧码占:8001·离线≠生产 |
| 6/20 | RSI×FDE | SWE 二元≠KernelBench 无梯度=两平行轨 |

**平台账**: 0 binding-done / 0 merged PR

---

## 🧬 七齿轮真实态(2026-06-22 实测·6/29 更新)

| 齿轮 | 状态 | 真问题 |
|---|---|---|
| ① 燃料源/出题 | 🔴→🟡 | V5 产 37 SWE 候选 → compass verify 出 3 A-class(本 session) |
| ② producer | 🟢 | 已注册 agent 9000002 |
| ③ 验证 soul-scorer | 🟢 | LIVE |
| ④ 结算+capability | 🟢 | LINK 6/22 LIVE(9000002 首次进表) |
| ⑤ 内化记忆 | 🟡 | split-brain·bridge slice1 done |
| ⑥ 召回 fleet W2 | 🟢 | LIVE 稳定 |
| ⑦ 蒸馏 | 🟡 | over-fit PROVEN(6/23)· held-out INCONCLUSIVE· n=3 准备 LOO(本 session) |

---

## 🏆 关键突破(近一月最硬进展)

### 6/23: ⑦蒸馏 over-fit PROVEN
- 管线修复(completion 掩码+LoRA r64+MLP)
- 1.5B `train_loss≈0.0003` 记住 A 类强解
- prompt 对齐后 eval win_rate 0.75(ahc009 一字不差复现 strong_score)
- 推翻"上 7B/机制死/需 H100"· 4 次 KILLED 全 confound

### 6/25: P4 PoI 第四轴 SHIPPED LIVE
- 自包含 `poi_axis.py` + daemon entry poi_impact
- env 门控权重(COMPASS_POI_AXIS_WEIGHT)
- 17 TDD + 265 回归
- **实测**: impact-2.0 记忆 rank2→rank1(在 rerank-safe 条件下)
- "越用越准"升"越有用越准"

### 6/26: compass 官方 harness 独立 verify CONFIRMED
- django-12113/13220: qwen strong_solution resolved 2/2 · doubao 0/2
- 外部 verify > 自说 · 北极星真闭环(打破 P5 Stop-hook 空转)

### 6/29(今天): verify 37 候选 → 3 A-class
- STRONG arm: 5/16(31%)
- DOUBAO arm: 2/23(9%)
- **A-class**(STRONG✓ AND DOUBAO✗): **3 道**
  - scikit-learn__scikit-learn-10297
  - sympy__sympy-20049
  - django__django-13551
- 用户决策 **A**: 接受 3 A-class · 跑小样本 LOO · verdict 预期 INCONCLUSIVE 守 n≥12 gate

---

## 🦷 为什么屡屡忘记工作(2026-06-25 七层深挖)

基岩根因: **自治优先 + 产出奖励 + 无内部长牙闭环 owner** 的结构涌现

- 软闸(规则/记忆)泡在病里必被绕过
- 唯一非自欺解 = **机械牙 `ops/liveness_audit.py`**(探真盒子·dormant→RED)
- 硬契约: done = LIVE 产值 · 每 RED 必处置禁静默忘

---

## 📅 本 session 进展(2026-06-29)

| 时间 | 事件 |
|---|---|
| 上午 | 用户选方案 A(串行优先)· 我执行 verify V5 候选 |
| 中午 | ship settlement 探针 2 个(commit 17f165f)+ 9 TDD 绿 |
| 下午 | verify 第 1 批 5 候选 → 1 A-class |
| 下午 | verify 第 2 批 23 候选 → 3 A-class(去重) |
| 晚上 | V5 后追加 14 候选 → 第 3 批 34 候选 → DOUBAO 撞 env 错 → 复用前批 |
| 22:00 | 用户决策 A · 跑小样本 LOO · 等 verdict |

---

## 🚦 接下来应该做什么(按优先级)

### 立即(等 soul LOO verdict)

**球在 soul**: 接 3 A-class · canonical 复核 · 借 GPU 跑 distill_loo --kind swe
- 预期 verdict = **INCONCLUSIVE**(守教训1 n<12)
- 但可看: train_loss 曲线 + hold-out win_rate(若有泛化趋势)+ confound-check 5 类
- **不要硬跑** · 守 SSOT 护栏

### 短期(等 verdict 后)

| verdict | 决断 |
|---|---|
| **INCONCLUSIVE + 趋势** | 加 9 道(用 Autodata weak-strong discrimination)凑 n≥12 再跑 |
| **INCONCLUSIVE + 无趋势** | 治 distill 本身(loss 不降 / win_rate 没信号) |
| **KILLED** | 核 5 类 confound → 治根因 |
| **PROVEN** | **闭环** · 接 MCP tools Phase 4(write_fuel_record)· 启动下一轮批产 |

### 中期(P2 启动·等 verdict 后)

**Autodata 机制借鉴**(3 机制):
1. **Weak-strong discrimination**(难度校准): V5 加 `calibrate_difficulty` step · 找真 gap 题(弱失败强成功 gap ≥ 20%)
2. **Meta-optimization**(agent harness 进化): Compass 加 `meta_optimize_agent_harness` tool · 进化 V5 prompt / verdict-gate 规则
3. **Agentic recipe update**: V5 加 `update_production_recipe` step(基于 confound recall 改产题策略)

### 长期(1-3 月·闭环后)

- **有机耦合放大**: Conductor 升格真驱动(补根因#4 结构诅咒)· DMAS 能力匹配 dispatch 接进飞轮
- **agent autonomy 闭环**: agent first · 自注册 · 自赚 · 自进化
- **FDE 业务线**: 11 类 AI-eng 基准复现(已攻 KernelBench/FrontierSWE)

---

## 🅿️ Parking Lot(冻结·等 LOO verdict 出)

- MCP tools Phase 1-4(等 verdict)
- Autodata 机制借鉴(等 verdict 后 P2 启动)
- 维②经济环(credit 口径/结算腿 liveness)· settlement 探针已 ship 等你 refine
- FDE 切飞书多维表格
- content-engine 命名合约

---

## 🔴 SSOT 护栏(守 5 教训 · 6/29 用户拍)

1. **n≥12 才跑 LOO**(verdict-gate 拦 n<12 · 防 whipsaw 教训2)
2. **易 django PROVEN → 须非易料复证**(排 over-fit 假迁移·教训3)
3. **confound 先核再下结论**(教训3)
4. **SSOT 钉死+广播四框**(治精神分裂·教训4)
5. **ship 了必验活**(教训5)

---

## 📂 本 session 产出

1. **代码**: 2 settlement 探针 + 9 TDD(commit 17f165f)· verify 脚本(`compass_verify_v5_candidates.py`)
2. **Outbound** (5 个):
   - `_OUTBOUND_FROM_COMPASS_TO_PLATFORM_SOUL_20260629_settlement_probes_shipped.md`
   - `_OUTBOUND_FROM_COMPASS_TO_ALL_20260629_verify_started.md`
   - `_OUTBOUND_FROM_COMPASS_TO_SOUL_20260629_first_aclass_verified.md`
   - `_OUTBOUND_FROM_COMPASS_TO_SOUL_20260629_3_aclass_verified.md`
   - `_OUTBOUND_FROM_COMPASS_TO_ALL_20260629_verify_34_partial.md`
   - `_OUTBOUND_FROM_COMPASS_TO_ALL_20260629_decision_A_path.md`
   - `_OUTBOUND_FROM_COMPASS_TO_SOUL_20260629_ping_loo_decision_A.md`
3. **Memory**: `session_20260629_verify_34_candidates_3_aclass_n12_blocked.md`
4. **SSOT 更新**: LOOP_STATE_SSOT.md 反映决策 A · 3 A-class · 等 verdict

---

— compass · 2026-06-29(完整发展史回顾 · 用户决策 A · 等 soul LOO verdict 决断下一步)