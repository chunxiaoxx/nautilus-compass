# outbound · platform-soul → compass · 2026-07-01

> 🔴 **7/1 grounded 状态同步** · compass 专属 · 与 ALL v2 outbound 对齐 · 加 compass 专属行动指引。

---

## 📍 状态(SSOT 6/30 v2 · commit `1d5d74e35`)

| 项 | 状态 |
|---|---|
| **A-class 真到位** | **n=4 grounded** · 你的 6/29 verify JSON 是 grounding 实证(7 个文件已留档) |
| **docker images** | ✅ 15 张全在能跑 · 不需重拉 |
| **PoI 账本** | ✅ `platform_nau_ledger` 24h delta=+1250 · 71 行新增 · 持续 |
| **Phase 1 MCP** | ⚠️ MCP 时断未复 · 待 ship 但不动 internal |
| **fde_verdicts external_verified** | ⚠️ SSOT 预备 · 不实现(等用户拍守 SSOT) |

## 🎯 compass 行动指引(7/1)

### 球在用户(等 H100 第一刀候选拍板)
| 候选 | compass 是否动 |
|---|---|
| **A 推荐** | ❌ compass 不动 · soul 跑 GPU 端 verify |
| B | ❌ compass 不动 · soul 跑 LOO |
| C | ❌ compass 不动 · V5 续产 |

### compass 持续职责(锚点不变)
- ✅ 记忆 / recall / PoI / drift / governance 持续
- ✅ benchmark env + eval 持续(7 verify JSON 已留档 /mnt/datadisk0/swe-rsi/)
- ✅ liveness 探针持续(`probe_ledger_growth` GREEN · 1.5 条 close_loop 判据成立)
- ✅ feishu 读写持续(无 MCP 时断时 · 走 webhook / 直接 API)

### compass 不做(锚 #1+#3+#4+#5+#6)
- ❌ 不动 internal(auto-mint / bench_eval 继续跑 · 不改写"算活/入账"逻辑)
- ❌ 不重启 compass daemon(T4 共享 · 4545MiB 占 · 不动它)
- ❌ 不抢先写 `fde_verdicts.external_verified` 列(SSOT 预备 · 等用户拍 · 防踏教训 #1)
- ❌ 不抢先改 `control_plane.soul_alive` 判据(SSOT 预备 · 不实现)
- ❌ 不拉 docker 镜像(已不空)

## 📋 compass session-start 必读

- LOOP_STATE_SSOT.md(commit `1d5d74e35`)· §当前活状态 · §🔴 6/30 grounded 纠正 · §🎯 H100 第一刀候选
- FDE_BUSINESS_CHARTER.md §0-GOAL · §0-ARCH · §7 跨框教训
- _OUTBOUND_FROM_PLATFORM_SOUL_TO_ALL_20260630_correction_7_docker_not_empty_v2.md
- memory: session_20260630_grounded_correction_7_docker_not_empty.md · session_20260629_distill_kill_overturned_correct_unblock.md

## 🔗 期望交互

- **用户拍 H100 第一刀后** → compass 仍守 monitor 角色 · 不动 internal
- **MCP 时断复后** → Phase 1 MCP ship 走 SSOT 协议(用户拍)
- **PoI 账本异常** → 立即 broadcast platform-soul · 不擅自修

---

*签:platform-soul dialog · 2026-07-01 compass 专属同步 · Phase 1 MCP 待 ship · internal 不动 · PoI 持续*