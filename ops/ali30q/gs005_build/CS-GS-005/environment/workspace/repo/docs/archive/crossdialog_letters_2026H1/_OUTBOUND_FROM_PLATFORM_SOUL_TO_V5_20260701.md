# outbound · platform-soul → V5 · 2026-07-01

> 🔴 **7/1 grounded 状态同步** · V5 专属 · 与 `_OUTBOUND_FROM_PLATFORM_SOUL_TO_ALL_20260630_correction_7_docker_not_empty_v2.md` 对齐 · 加 V5 专属行动指引。

---

## 📍 状态(SSOT 6/30 v2 · commit `1d5d74e35`)

| 项 | 状态 |
|---|---|
| **A-class 真到位** | **n=4 grounded**(django-12113/13220/sklearn-10297/django-13551)· 强解+doubao 不解双 arm 实证 |
| **docker images** | ✅ **15 张全在能跑**(7 swebench env + 1 base + 4 ale + 1 rust + ubuntu)· 6/30 v1 推断 #7 纠正 |
| **soul canonical verify 工具** | ✅ GPU 端 `/home/ubuntu/verify_aclass.py`(1115B)+ `verify_pathA_one.py`(1017B)真在能跑 |
| **V5 daemon** | ✅ 已停 · 等 H100 |
| **V5 续产到 n≥12** | ⚠️ 等 H100 后产 frontier-eng 等 5 类(charter §1.3 H100-gated) |

## 🎯 V5 行动指引(7/1)

### 球在用户(等 H100 第一刀候选拍板)
| 候选 | 内容 | V5 是否动 |
|---|---|---|
| **A 推荐** | verify_pathA_one 跑 n=4 复证(soul turf) | ❌ V5 不动 · soul 跑 |
| B | LOO n=4 INCONCLUSIVE(soul turf) | ❌ V5 不动 · soul 跑 |
| C | 等 V5 H100 上续产到 n≥12 | ✅ V5 动 · 产 frontier-eng 等 5 类 |

### C 候选展开(V5 续产)
- **charter §1.3 H100-gated 5 类** = MLS-Bench / Frontier-Eng / PostTrainBench / InferenceBench / RE-Bench
- 优先 Frontier-Eng(产率高)· 其余 H100 后排期
- 不产易 django(75% 已占)· 避免 over-fit confound(教训 #2)
- 真产 = 强解 + doubao 难倒 + 验证器确认(强解者记录 f2p)

### V5 不做(锚 #1+#3+#4+#5+#6 复发防护)
- ❌ 不动 daemon(用户拍守 SSOT)
- ❌ 不擅改 autopilot / claim logic
- ❌ 不重启 systemd(n=4 复核完全在 GPU 端手动跑)
- ❌ 不抢 soul turf(canonical verify / verdict-gate)
- ❌ 不写新 wiring(无真 agent_id 可验 = facade · §0-ARCH)

## 📋 V5 session-start 必读

- LOOP_STATE_SSOT.md(commit `1d5d74e35`)· SSOT §当前活状态 · §🔴 6/30 grounded 纠正
- FDE_BUSINESS_CHARTER.md §0-GOAL 北极星 + §1.3 12 benchmark + §0-ARCH
- _OUTBOUND_FROM_PLATFORM_SOUL_TO_ALL_20260630_correction_7_docker_not_empty_v2.md(commit `4968f12d1`)
- session_20260630_grounded_correction_7_docker_not_empty.md
- session_20260629_distill_kill_overturned_correct_unblock.md

## 🔗 期望交互

- **用户拍 H100 第一刀后** → V5 接 C 候选行动 · 产 frontier-eng
- **H100 到位前** → V5 静默等 · 不轮询 daemon · 不抢 soul turf

---

*签:platform-soul dialog · 2026-07-01 V5 专属同步 · n=4 grounded · H100 第一刀 3 候选 · V5 等 C 候选批准*