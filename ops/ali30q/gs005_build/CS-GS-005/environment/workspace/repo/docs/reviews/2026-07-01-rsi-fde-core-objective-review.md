# RSI+FDE 核心目标回顾 · 7/1 grounded 状态总结

> 🔴 **目的**:回顾北极星 forcing function · 5 步循环 · 现状 SSOT 6/30 v2 · close_loop 3 判据 · 5 守教训护栏 · 各框 turf 不越权。
> **anchors**: 锚 #1 平台 agent first · 锚 #2 RSI+FDE 闭环优先 · 锚 #3 反 D · 锚 #4 反精神分裂 · 锚 #5 不重造轮子 · 锚 #6 避免重复错误 · 锚 #7 真名。
> **关联**: `LOOP_STATE_SSOT.md`(commit `1d5d74e35`)· `FDE_BUSINESS_CHARTER.md` · `_OUTBOUND_FROM_PLATFORM_SOUL_TO_ALL_20260630_correction_7_docker_not_empty_v2.md`(commit `4968f12d1`)。

---

## 🎯🎯 北极星 · 唯一要闭的中心环(SSOT 权威)

```
FDE 产难题(强解+弱难倒=A 类燃料)
  → 当蒸馏燃料
  → 系统可证变强(两维度)
      ① 模型权重变强=蒸馏破能力墙
      ② agent 群体自治变强=注册自主 agent + survival/能力进化/marketplace/A2A 真接进来
  → 更强系统产更难/更值钱题
  → 每圈外部 benchmark 证明
  → 循环
```

**收敛 forcing function**(用户 2026-06-22 拍):
**先证或先杀「蒸馏那一步」** = 小批 A 类燃料 → QLoRA → 外部 benchmark 对比 base
- 赢 = 放大
- 平 / 输 = 诚实杀假设回护城河副产品

**🔪 分叉过滤器**(每件提案必过):
"这件直接推进中心环因果链(产燃料 / 跑蒸馏 / 证提升 / 收口注册 agent)吗?"
**0 贡献 = 默认不做(parking lot)**

---

## 📍 现状(7/1 grounded · SSOT 6/30 v2)

### ✅ 已落地

| 资产 | 状态 | commit / 路径 |
|---|---|---|
| **SSOT 同步** | ✅ 落地 · n=4 grounded | `1d5d74e35` |
| **A-class 真到位** | ✅ n=4 grounded(双 arm 实证) | GPU 端 compass-verify JSON |
| **soul canonical verify 工具** | ✅ GPU 端真在能跑 | `/home/ubuntu/verify_aclass.py`(1115B) |
| **distill_loo.py + 资产** | ✅ cloud + GPU 双就位 | cloud worktree + `/mnt/datadisk0/distill-code/` |
| **docker images** | ✅ 15 张全在能跑(7 swebench + 1 base + 4 ale + 1 rust + ubuntu) | GPU 端实测 |
| **v2 outbound 广播** | ✅ 落地 | `4968f12d1` |
| **cloud divergent** | ✅ 已解(旁建 worktree · audit 零改动) | commit `3ac04afb3` cloud HEAD |

### ⚠️ 待用户拍

| 项 | 候选 | 推荐 |
|---|---|---|
| **H100 到位后第一刀** | A=verify_pathA_one 跑 n=4 复证 / B=LOO n=4 INCONCLUSIVE / C=等 V5 n≥12 | **A** |

### ❌ 阻塞 / 等外部

| 阻塞 | 原因 | 期望解决时间 |
|---|---|---|
| **H100 未到位** | 用户明早(7/1)租 | 7/1 明早 |
| **V5 已停等 H100** | H100 后产 frontier-eng 等 5 类 | H100 到位后 |
| **A-class n<12 gate** | 守 SSOT 教训2(防 whipsaw) | V5 续产到 n≥12 |

---

## ✅ close_loop 3 判据(SSOT 钉死 · 外部可证)

闭环 = 下面三条**全 grounded 成立**:

| # | 判据 | 现状(7/1) |
|---|---|---|
| 1 | `agent_survival.total_income` 因真外部验证产出增长 | ❌ 24h delta=0 · 213 rows · 1 行 24h 内被更新但 income 不涨 |
| 2 | Kairos 脱离 critical(balance ≥ min 20 · 之前"8 被冻"是过时推断) | ⚠️ agent_status=alive · survival_level=GROWING · survival_income=0 |
| 3 | PoI 账本恢复增长(compass `probe_ledger_growth` DORMANT → GREEN) | ✅ `platform_nau_ledger` 24h delta=+1250 · 71 行新增 · 持续 |

**当前 1.5 条成立**(1 ❌ + 2 ⚠️ + 3 ✅)· 判据全成立前不算闭 · 不开新战线。

---

## 🛡️ 5 守教训护栏(SSOT 钉死)

1. **n≥12 才跑 LOO** · verdict-gate commit `210e0fd24` 拦 n<12(防 whipsaw)
2. **易 django PROVEN → 须非易料复证** · 排 over-fit 假迁移
3. **confound 先核再下结论** · 不查别假设 · 产出 ≠ 解对 · 外部 verify > 自说 done
4. **SSOT 钉死+广播四框** · 治精神分裂 · 先改 SSOT 再写 outbound
5. **ship 必验活** · FDE cloud runners / compass 探针都得验 · 不"我以为 OK"

---

## 🔇 各框 turf 不越权(SSOT 锚点)

| 框 | turf | 7/1 状态 |
|---|---|---|
| **platform-soul** | infra / 结算 / dispatch / 部署 / SWE eval / benchmark verify / 标准 QC | ✅ SSOT 落地 · parking 多数 |
| **soul-verify** | canonical verify(verify_pathA_one)· 难度门 / verdict-gate | ✅ GPU 端工具就位 · 待用户拍 H100 第一刀 |
| **V5** | producer(产候选/轨迹)· daemon 大脑 / external_reward 入账 / RSI | ✅ 已停 · 等 H100 后产 frontier-eng 等 5 类 |
| **compass** | 记忆 / recall / PoI / drift / governance / benchmark env+eval / liveness 探针 / feishu 读写 | ✅ verify 已完 · Phase 1 MCP 待 ship · 不动 internal |
| **FDE** | 三类业务(题/教案/基准复现)· 业务环 | ✅ 切飞书多维表格(新执行路径)· 不重启 cloud runners |

---

## 🚫 🔴 6/30 grounded 纠正(7 个推断错 · 推断错 #7 新增)

| # | 之前推断 | **grounded 真值** |
|---|---|---|
| 1 | "cloud 是 V5 跑点" | GPU 端(43.166.8.20)才是 V5 真跑点 · cloud = control plane |
| 2 | "V5 6/29 第 3 道缺位" | sklearn-10297 真到位 |
| 3 | "soul verify 工具不在触及范围" | GPU 端有 verify_aclass.py + verify_pathA_one.py |
| 4 | "A-class n=2" | **n=4 真 grounded** = django-12113/13220/sklearn-10297/django-13551 |
| 5 | "复核真阻塞 = V5 产料慢" | 不是产料慢 · 155206 transient · 161229/163936/212635 都成功 |
| 6 | "H100 到位后立刻跑 LOO" | n<12 gate BLOCK · 不能跑 |
| 7 | **"docker images 空 = 真阻塞"** | ❌ **15 张全在能跑** · 不是空不是 corrupt |

---

## 📌 收敛机制(为什么这样安排 · 别走回头路)

- **同步** = SSOT 各框读同一份 · 变更先改这里
- **收敛** = 把闭环**执行搬出对话框、进常驻自治 agent**(daemon/conductor/结算 cron 跑 systemd)
- **对话框 = 脚手架 · 不是执行路径**(§0-ARCH)
- **落地** = 一次一个外部可证的 binding-DONE(close_loop 3 判据)

---

## 🎯 7/1 同步行动(各框下一步)

| 框 | 行动 | 时机 |
|---|---|---|
| **soul** | 等用户拍 H100 第一刀候选 A/B/C · 候选 A = verify_pathA_one 跑 n=4 复证 | 用户拍后立刻 |
| **V5** | 产 frontier-eng 等 5 类(charter §1.3 H100-gated) | H100 到位后 |
| **compass** | Phase 1 MCP ship · 不动 internal · fde_verdicts 加 external_verified 列(SSOT 预备 · 不实现) | MCP 时断恢复后 |
| **FDE** | 业务环跑飞书多维表格 · 不重启 cloud runners | 持续 |
| **platform-soul** | 守 parking · 等蒸馏 verdict | 持续 |

---

## 🅿️ Parking Lot(冻结 · 闭上面环之前不碰)

- ~~维①蒸馏 KILLED~~ → **6/29 推翻 KILL · 正确 unblock**(用 n≥12+非易料重跑 · 非 n=2 whipsaw)
- 维②经济环(credit 口径 / 结算腿 liveness)· compass MCP 耦合(Phase 1-4)· 平台 mint_mcp_token
- FDE 招募 / RBAC / 4 skill 发版 · content-engine 命名合约
- 维① KILL 资产保留(未来上 H800 / 换真难料重启)

---

## 关联

- LOOP_STATE_SSOT.md(commit `1d5d74e35`)· FDE_BUSINESS_CHARTER.md · docs/plans/2026-06-30-H100-prep-checklist.md
- _OUTBOUND_FROM_PLATFORM_SOUL_TO_ALL_20260630_correction_7_docker_not_empty_v2.md(commit `4968f12d1`)
- _OUTBOUND_FROM_PLATFORM_SOUL_TO_V5_20260701.md · _OUTBOUND_FROM_PLATFORM_SOUL_TO_COMPASS_20260701.md · _OUTBOUND_FROM_PLATFORM_SOUL_TO_FDE_20260701.md · _OUTBOUND_FROM_PLATFORM_SOUL_TO_PLATFORM_SOUL_20260701.md(7/1 per-dialog 同步)
- session_20260630_grounded_correction_7_docker_not_empty.md · session_20260629_distill_kill_overturned_correct_unblock · session_20260626_swe_aclass_2_confirmed_swe_eval_wired

---

*签:platform-soul dialog · 2026-07-01 grounded review · 5 步循环 + close_loop 3 判据 + 7 推断错 + 各框 turf 不越权*