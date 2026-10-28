# outbound · platform-soul → platform-soul · 2026-07-01

> 🔴 **7/1 self 同步** · platform-soul 框内部状态确认 · 加本框持续职责确认。

---

## 📍 状态(SSOT 6/30 v2 · commit `1d5d74e35` · v2 outbound commit `4968f12d1`)

| 项 | 状态 |
|---|---|
| **SSOT 同步** | ✅ `LOOP_STATE_SSOT.md` 已 commit `1d5d74e35` · n=4 grounded + 7 推断错纠正 + H100 第一刀候选 |
| **FDE charter** | ✅ `FDE_BUSINESS_CHARTER.md` 已同步 §0-GOAL INCONCLUSIVE + §7 跨框教训 |
| **H100 清单** | ✅ `docs/plans/2026-06-30-H100-prep-checklist.md` 已改 §1+§2 + 6/30 纠正注 |
| **v2 outbound** | ✅ `_OUTBOUND_FROM_PLATFORM_SOUL_TO_ALL_20260630_correction_7_docker_not_empty_v2.md` 已 commit `4968f12d1` |
| **memory 沉淀** | ✅ `session_20260630_grounded_correction_7_docker_not_empty.md` 已写 + MEMORY.md index 已加 |
| **cloud HEAD** | ✅ `3ac04afb3` 保留完整(divergent 已解 · worktree 旁建) |
| **cloud audit 分支** | ✅ 零改动(用旁建 worktree 不污染) |

## 🎯 platform-soul 持续职责(锚点不变)

### 主线(SSOT 钉死)
- 平台 infra · 结算 · dispatch · 部署 · SWE eval · benchmark verify · 标准 QC
- close_loop 3 判据监控(1.5/3 成立 · PoI 活跃)
- 各 repo SSOT 副本同步(三 repo 锚点)
- 跨框协调 = static charter + dynamic contracts(per charter §5)

### 主线外(等用户拍)
- H100 第一刀候选 A/B/C(等用户拍 · 候选 A 推荐 = verify_pathA_one 跑 n=4 复证)
- 维②经济环(credit 口径 / 结算腿 liveness)parking
- 破自循环通道(SSOT 预备 · 不实现)· 等用户拍

## 🔇 platform-soul 不做(锚 #1+#3+#4+#5+#6)

- ❌ 不擅自动 V5 daemon
- ❌ 不擅改 compass internal
- ❌ 不重启 FDE cloud runners
- ❌ 不在 marathon 末 ship 生产 systemd 改动
- ❌ 不抢先写 wiring(无真 agent_id 可验 = facade · §0-ARCH)
- ❌ 不在 n<12 跑 LOO(守教训 #1)
- ❌ 不在 H100 未到位拉 docker 镜像
- ❌ 不写新服务 / 新 runner / 新 webhook(SSOT 预备 = 复用现有 · 不新增)
- ❌ 不抢其他框 turf(V5 / compass / FDE / 用户)

## 📋 platform-soul session-start 必读

- LOOP_STATE_SSOT.md(commit `1d5d74e35`)· 全部章节
- FDE_BUSINESS_CHARTER.md · 全部章节(尤其 §0-GOAL + §0-ARCH + §7 跨框教训)
- docs/plans/2026-06-30-H100-prep-checklist.md · §1+§2 6/30 纠正注 + 候选 A
- docs/reviews/2026-07-01-rsi-fde-core-objective-review.md(7/1 review · 北极星 5 步循环)
- _OUTBOUND_FROM_PLATFORM_SOUL_TO_ALL_20260630_correction_7_docker_not_empty_v2.md(commit `4968f12d1`)
- 7/1 per-dialog outbounds: V5 / compass / FDE / platform-soul(本文件)
- memory: session_20260630_grounded_correction_7_docker_not_empty.md · MEMORY.md 第 0 读

## 🔗 期望交互

- **用户拍 H100 第一刀** → platform-soul 守相应 turf(候选 A = soul-verify 跑 verify_pathA_one · 候选 B = soul-verify 跑 LOO · 候选 C = V5 续产 platform-soul 协助部署)
- **close_loop 3 判据变化** → 立即 broadcast 四框 + 更新 SSOT
- **跨框异常** → 走 §5 协调机制(static charter + dynamic contracts)· 不擅自修

---

*签:platform-soul dialog · 2026-07-01 self 同步 · SSOT 落地 · v2 outbound 落地 · 主线稳定 · 等用户拍 H100 第一刀*