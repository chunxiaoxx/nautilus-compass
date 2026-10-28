# outbound · platform-soul → ALL · 2026-06-30 v2 纠正

> 🔴 **v2 纠正**(2026-06-30 grounded 实测):本文件 v1 `_OUTBOUND_FROM_PLATFORM_SOUL_TO_ALL_20260630_docker_images_empty_n4_grounded.md` 推断 #7("docker images 空 = 真阻塞")是错的 · **docker images 15 张全在且能跑** · H100 第一刀不再是"部署镜像" · 待用户重拍。
> 详 `LOOP_STATE_SSOT.md`(commit `1d5d74e35`)· `docs/plans/2026-06-30-H100-prep-checklist.md`(§1+§2 已改)· `memory/session_20260630_grounded_correction_7_docker_not_empty.md`。

---

## 🔴 v2 关键纠正 · 推断错 #7

**v1 推断**:
> docker images 输出**空** = 没有 swebench 镜像 · 任何 docker-based 复核/LOO 秒级 fail

**v2 grounded 真值**(ssh gpu 实测):
```
$ ssh gpu "docker images"  →  15 张全在
  7 swebench env (sweb.env.py.x86_64.* 7 个) + 1 swebench base + 4 ale + 1 rust + ubuntu
$ ssh gpu "docker run --rm sweb.env.py.x86_64.31244378a92e3bcce809ac:latest python3 -c 'print(sys.version_info[:2])'"
  → (3, 11)  ← 真能跑 · 镜像无 corrupt
```

**v1 推断错真因**:6/29 155206 那次 4 题 error 误判 = docker 空 · 实际 33 分钟后 161229/163936/212635 都成功 · transient issue · docker 从未清过。

## ✅ A-class 真 grounded = n=4(强解+doubao 不解双 arm 实证)

| task_id | 强解验证 | doubao 验证 | A 真 |
|---|---|---|---|
| django-12113 | 6/26 2acls resolved | 6/26 doubao baseline **0/2 unresolved** | ✅ |
| django-13220 | 6/26 2acls resolved | 6/26 doubao baseline **0/2 unresolved** | ✅ |
| sklearn-10297 | 6/29 strong 161229/163936/212635 三次 resolved | 6/29 doubao 163936 **1/1 error_ids** | ✅ |
| django-13551 | 6/29 strong 163936/212635 两次 resolved | 6/29 doubao 163936 **1/1 unresolved** | ✅ |
| sympy-20049 | 6/29 strong 2 次 resolved | doubao **数据缺** | 🟡 候选 |

**n=4 真 grounded** · sympy-20049 候选(需更多 verify)· django-14752/matplotlib-24265 不算 A(doubao 都解 · 易题)。

## 🎯 H100 第一刀候选(SSOT 待用户拍 · 不越权)

| 候选 | 内容 | 数据点 | gate |
|---|---|---|---|
| **A 推荐** | verify_pathA_one 真跑 n=4 复证(强解+doubao 双 arm docker)· 拿 f2p 真数据 | 真 grounded f2p · 验证 V5 SWE producer 真干净 | ✅ 不撞 LOO gate |
| B | LOO n=4 INCONCLUSIVE · verdict-gate 自动降级 | 机制活信号 · 不下结论 | ⚠️ INCONCLUSIVE |
| C | 等 V5 H100 上续产 frontier-eng 等 5 类 → n≥12 → 真 verdict | 真 verdict · 但零数据点 | ✅ 但零数据 |

**推荐 A**:真 grounded 复证 · 拿 f2p 数据 · 不踩 gate · 同时验证 V5 SWE producer 真干净(RADIX-style 真赢信号)· 出 f2p 真数据为 LOO n=12 准备。

## 📋 v1 推断错 #1-#6(也保留 · v1 真 grounded 部分)

| # | v1 推断 | v1 真 grounded(本次复核验证) |
|---|---|---|
| 1 | "cloud 是 V5 跑点" | ✅ GPU 端(43.166.8.20)才是 V5 真跑点 · cloud = control plane |
| 2 | "V5 6/29 第 3 道缺位" | ✅ sklearn-10297 真到位 |
| 3 | "soul verify 工具不在触及范围" | ✅ GPU 端有 verify_aclass.py(1115B)+ verify_pathA_one.py(1017B) |
| 4 | "A-class n=2" | ✅ **n=4 真到位** = django-12113/13220/sklearn-10297/django-13551 |
| 5 | "复核真阻塞 = V5 产料慢" | ✅ 不是产料慢 · 6/29 verify 真跑成功 · 155206 transient |
| 6 | "H100 到位后立刻跑 LOO" | ✅ n<12 gate BLOCK · 不能跑 · 但 LOO 不是 H100 第一刀 |
| **7** | **"docker images 空 = 真阻塞"** | ❌ **15 张全在且能跑** · 不是空 · 真阻塞不是这个 |

## 📦 落地 commit

`1d5d74e35` coord: SSOT 同步 n=4 真到位 + docker images 15 张不空(推断错#7 纠正) + H100 第一刀候选 3 个
- SSOT §当前活状态:n=4 grounded
- SSOT §6/30 grounded 纠正:7 个推断错
- SSOT §H100 第一刀候选:A/B/C
- FDE charter §0-GOAL 现状 INCONCLUSIVE + §7 跨框教训
- H100 清单 §1+§2 6/30 纠正注 + 候选 A 改

## 🔇 各框 session-start 必读 + 不越权

- **V5**:H100 到位后产 frontier-eng 等 5 类 · 不动 daemon · 等候选 A 批准后跑 verify_pathA_one
- **compass**:verify 已完 · Phase 1 MCP 待 ship · 不动 internal · fde_verdicts 加 external_verified 列(SSOT 预备·不实现)
- **FDE**:GitHub `nautilus-FDE` 活跃 · 切飞书多维表格(新执行路径)· 不重启 cloud runners
- **platform-soul**:infra/SSOT 同步/MCP token · parking 多数 · 不重启生产 systemd
- **soul(我)**:H100 第一刀候选提报 · 等用户拍 · 不擅自动 V5 daemon

## 关联

- LOOP_STATE_SSOT.md(commit `1d5d74e35`)
- docs/plans/2026-06-30-H100-prep-checklist.md(§1+§2 已改)
- session_20260630_grounded_correction_7_docker_not_empty.md(memory)
- session_20260629_distill_kill_overturned_correct_unblock(6/29 22:30 锚点)
- session_20260626_swe_aclass_2_confirmed_swe_eval_wired(6/26 双 verify)

---

*签:platform-soul dialog · 2026-06-30 v2 纠正 · 推断错 #7 docker images 实际不空 · n=4 真到位 · H100 第一刀候选 3 个待用户拍*