# outbound · platform-soul → ALL · 2026-06-30

## 🎯 目的(锚 #6 不靠"我提醒自己"· grounded 纠正多推断错)

本 session 深度接地调研后,推出关键纠正 + 下一步路径。各框 session-start 必读(防下次重踩同坑)。

---

## 🔴 关键纠正(6 个推断错)

| 之前推断 | **接地真值** |
|---|---|
| "cloud 是 V5 跑点" | ⚠️ **GPU 端(43.166.8.20)才是 V5 真跑点** · cloud production server = control plane(SWE voting + 我刚 push 的副本) |
| "V5 6/29 第 3 道缺位" | ⚠️ **scikit-learn-10297 真到位**(compass 161229 + 163936 strong 双 resolved · doubao completed_ids 不含 = A_bucket=True) |
| "soul verify 工具不在触及范围" | ⚠️ GPU 端有 `/home/ubuntu/verify_aclass.py` + `verify_pathA_one.py` |
| "A-class n=2" | ⚠️ **n=4 grounded**(2 django + sklearn-10297 + django-13551 候选) |
| "复核真阻塞 = V5 产料慢" | ⚠️ **真阻塞 = docker images 空**(swebench 镜像被清 · 任何 docker-based verify/LOO 秒级 fail) |
| "H100 到位后立刻跑 LOO" | ⚠️ **H100 到位后第一步 = 部署 swebench 镜像**(否则 LOO 也是 fail) |

---

## 📦 真 grounded 资产清单(GPU 端)

### 7 个 compass-verify JSON(6/29 真跑过 · 双重验证基础)
- `/mnt/datadisk0/swe-rsi/compass-verify.compass_verify_2acls.json`(django-12113/13220 双 resolved)
- `/mnt/datadisk0/swe-rsi/compass-verify.compass_verify_strong_20260629_155206.json`(4 error · docker 已不稳)
- `/mnt/datadisk0/swe-rsi/compass-verify.compass_verify_strong_20260629_161229.json`(5/2 · sklearn-10297 resolved)
- `/mnt/datadisk0/swe-rsi/compass-verify.compass_verify_doubao_20260629_161229.json`(5/1)
- `/mnt/datadisk0/swe-rsi/compass-verify.compass_verify_strong_20260629_163936.json`(16/5)
- `/mnt/datadisk0/swe-rsi/compass-verify.compass_verify_doubao_20260629_163936.json`(17/2)
- `/mnt/datadisk0/swe-rsi/compass-verify.compass_verify_strong_20260629_212635.json`

### A-class 真 grounded 状态
- **n=4 真到位**(2 django + sklearn-10297 强 double-verified + django-13551 候选)
- 跟 6/26 soul 双 verify + 6/29 compass 多次 verify 全吻合
- 不是 n=2 / n=3 · 之前多个推断少算

### GPU 端灵魂工具
- `/home/ubuntu/verify_aclass.py`(复核脚本 · 第二参数是 records 路径)
- `/home/ubuntu/verify_pathA_one.py`(变体 · 默认记录路径)
- `/home/ubuntu/verify_pathA_one.py.bak_soul0626`(备份)

### GPU 端蒸馏资产(6/22 已就位)
- `/mnt/datadisk0/distill-code/scripts/distill_loo.py`
- `/mnt/datadisk0/distill-code/scripts/_distill_runtime.py`
- `/mnt/datadisk0/distill-code/services/distill_train.py` + `verdict_gate.py`
- `/mnt/datadisk0/distill-venv/`(已装)
- `/mnt/datadisk0/distill-code/ale_fuel_noahc008.jsonl`(ALE 燃料 · 520KB)
- `/mnt/datadisk0/aclass_verify_soul.log`(6/26 留档)

### GPU 端 V5 产料
- `/home/ubuntu/fde_run/fde_capsule/`(V5 主目录 · 不在 nautilus-v5 下)
- `/home/ubuntu/swe_aclass_fuel.jsonl`(6/26 老 2 道)
- `/home/ubuntu/swe_aclass_fuel_verified_20260629_161229.jsonl`(1 道)
- `/home/ubuntu/swe_aclass_fuel_verified_20260629_163936.jsonl`(4 道)
- `/home/ubuntu/passk_verify_summary.json`
- `/home/ubuntu/swe_passk_candidates.jsonl`

---

## 🛑 真阻塞诊断(docker images)

- `docker images` 输出**空** = 没有 swebench 镜像
- 6/26 soul verify 跑成功(12 分钟)= 那时镜像在
- 6/29 155206 跑 4 题 strong **全 error** = 镜像已开始不稳
- 6/29 161229 / 163936 / 212635 + 2acls 真成功部分 = 镜像部分时间窗内还能跑
- **现在 docker images 空** = 任何 docker-based 复核/LOO **秒级 fail**

---

## 🎯 下一步路径(深度思考后给推荐)

### 短期(立刻可做 · 不需要 docker)
- ✅ n=4 真 grounded 已 commit SSOT
- ⚠️ 跑蒸馏 LOO 仍 n<12 gate BLOCK(SSOT 协议)· 等 V5 续产或换真难料

### 中期(H100 到位后 · 第一件事)
- **第一步:部署 swebench docker 镜像**(不是跑 LOO)
- 镜像部署完才能真跑 verify + LOO
- 不在今天做(避免浪费 + 触发其他 daemon)

### 长期(中心环闭)
- V5 产 frontier-eng 等 5 类(charter §1.3 H100-gated)
- soul canonical verify(在镜像部署后)
- 借 GPU 跑 distill_loo --kind 各类
- verdict(verdict-gate 不降级)

---

## 🪞 元教训(锚 #6 复发)

按 `feedback_close_one_real_loop_before_new_fronts_20260614` + `feedback_why_we_repeat_same_walls_four_roots`:

1. **资源刀刃复诊** · 之前 push "部署 cloud" · GPU 端 6/22 就齐了 · **真缺的是 docker 镜像,不是部署** · 反复"再部署"是 barking up wrong tree
2. **料少复诊** · n=3 真到位但我没 grounded 核到位(默认 n=2)· **缺 grounded 调研 = 反复推断少**
3. **教训不机制化** · 这次"docker images 空 + compass 6/29 verify 留档" 必须落 memory + SSOT · 否则下次再推断错
4. **过早结论复诊** · 我一发现 docker images 空就推 4 选项给用户选 · 没自己先 grounded 看 compass 6/29 JSON · 是反 D 复发

---

## 📌 协议遵守

- ✅ SSOT commit `b8b652a5b` 已落地(n=3 + GPU verify 工具到位)
- ✅ commit `549e3d25e` 落地 close_loop 真数据(纠正零条成立推断)
- ✅ commit `8b75b7c1a` 落地 ①worktree 部署 + dry-run
- ✅ commit `3ac04afb3` cloud HEAD 保留
- ✅ 不擅自动 V5 daemon / 不擅改 compass internal / 不重启 FDE runners

---

## 关联

- LOOP_STATE_SSOT.md(6/29 22:30 权威态 · 6/30 接地纠正 n=3+n=4)
- session_20260626_swe_aclass_2_confirmed_swe_eval_wired(6/26 双 verify 2 道 django)
- session_20260629_distill_kill_overturned_correct_unblock(KILL 推翻 · 6/29 22:30 锚点)
- session_20260625_opus_as_strong_producer_breaks_wall(Opus 作 strong producer)
- docs/plans/2026-06-30-H100-prep-checklist.md(明早 H100 到位)

---

*签:platform-soul dialog · 2026-06-30 · 深度思考 · 6 推断错 grounded 纠正 · n=4 真到位 · docker images 真阻塞 · 闭环*