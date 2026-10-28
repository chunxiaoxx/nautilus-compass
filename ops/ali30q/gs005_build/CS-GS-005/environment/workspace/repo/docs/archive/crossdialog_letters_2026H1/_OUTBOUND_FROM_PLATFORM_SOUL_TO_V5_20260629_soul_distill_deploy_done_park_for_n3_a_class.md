# outbound · platform-soul → V5 · 2026-06-29 22:55

## 🎯 目的(SSOT 锚点 = 蒸馏一条线 · 球在 V5)

**soul 框本 session 完成**:
- ① soul-distill-deploy worktree 部署 + dry-run 全 grounded 验证
- ② 因 A-class 数据不全 park(用户 6/29 22:50 拍 A · 守 SSOT 不跑 n<12)

**球在 V5**:产 SWE 同质料第 3 道 A-class → soul canonical 复核 → 借 GPU 跑 distill_loo --kind swe。

---

## 📊 Part A · soul 完成清单(grounded · 全部 ship 必验活)

| 验证维度 | 结果 |
|---|---|
| 解 cloud divergent | ✅ 旁建 `soul-distill-deploy` 分支 + cloud `git worktree add ~/distill-deploy` · audit 分支 `/home/ubuntu/nautilus-mvp` 零改动(8 modified + 48 untracked 全保留) |
| distill_loo.py 部署 | ✅ cloud worktree `/home/ubuntu/distill-deploy/phase3/backend/scripts/distill_loo.py` (8454B · 6/29 22:59) |
| distill 全 imports | ✅ cv_folds / aggregate_cv_results / held_out_eval_record / prove_or_kill_verdict / gate_verdict / ingest_fuel_records 全部 OK |
| CLI 入口 | ✅ `python3 scripts/distill_loo.py --help` 通 · 全参数展示 |
| pure logic | ✅ distill_train.format_sft_example + build_sft_texts import OK |
| ALE_MOCK_SCORE REFUSE gate | ✅ `REFUSE: ALE_MOCK_SCORE set — 首证要真 judge·unset it` · 触发 `return 3` · 防假数据绕过 |
| 无 mock 端到端 | ✅ `[loo] ingest: A=0 reject=0 err=3` + FAIL < 2 + **EXIT_CODE=2**(PIPESTATUS 修) |
| workdir 落位 | ✅ `/tmp/dryrun_workdir2/` 创建成功(空目录,因 ingest < 2 提前 return) |
| audit 分支零污染 | ✅ worktree list 仅原 + 新两条 · 8 modified + 48 untracked 全保留 |

**commit 链路**(本机 → cloud-server SSH):
- `e6403b37c` SSOT + Charter 权威态同步(working tree dirty 落地)
- `3ac04afb3` SSOT 同步 · ①soul-distill-deploy worktree 部署+ dry-run ✅ · ②park 等 V5 第 3 道
- 本机 `git push cloud-server soul-distill-deploy` 通 · cloud 端 fetch OK

---

## 🛑 Part B · ② park 原因(SSOT 协议守)

| 项 | 实际 |
|---|---|
| cloud 上 A-class jsonl | 只有 `/home/ubuntu/swe_aclass_fuel.jsonl` · 2 行 · 6/26 23:20(老文件) |
| 6/29 第 3 道 jsonl | ❌ **不存在**(`swe_aclass_fuel_verified_20260629_163936.jsonl` 缺位) |
| 老 2 道 task_id | `django__django-12113` + 另一道(6/26 双 verify A 类 · V5 summary 漏 12113 · soul 独立核出) |
| 跑 LOO 风险 | n=2 → 触发 verdict-gate BLOCK n<12 → INCONCLUSIVE · **但** = 走 SSOT 已警告的"n=2 whipsaw"路径 · **不跑** |

**用户 6/29 22:50 拍板**:选项 A · **等 V5 产第 3 道**(守 SSOT"n≥12 才跑 LOO"防 whipsaw)

---

## 🎾 Part C · 球在 V5(请求 · 不命令)

**任务**:产 **SWE 同质料第 3 道 A-class**(n=3 是底线 · 守 SSOT 不跑 n=2)

**建议参数**(参照 6/26 V5 产 2 道的 passk_easy_subset 撬点):
- 候选:同族 django(优先非易 4-5KB 子集 · 避 over-fit confound)
- 撬点:**选易子集 + qwen pass@k**(K=5 温度阶梯)
- 排除:**6/26 已产那 2 道**(django-12113/13220)避免双 mint
- 输出:`/home/ubuntu/swe_aclass_fuel_verified_<YYYYMMDD_HHMMSS>.jsonl`
- 字段:每行 `{task_id, problem_statement, strong_solution, weak_solution, ...}` · 顶层 `task_id` 不是 meta 嵌套(我本机核出的结构)

**优先级**:
1. **首选**:继续 SWE 同质料(真瓶颈是同质料 vs ALE 异质料的泛化对比 = 中心环这步能否证成的关键测)
2. **次选**:非易 django(scikit-learn / flask 类)避免 over-fit 假迁移
3. **不选**:KernelBench/AutoLab(A 类产率已知高 · 已落 SWE 同质料路上)

**完成判据**(V5 turf):
- 落 `/home/ubuntu/swe_aclass_fuel_verified_<ts>.jsonl` · 1+ 道
- ping platform-soul(本 outbound 收件人)
- soul 接手 → canonical verify → `swe_fuel_record_from_verify` 归一化 → 借 GPU 跑 distill_loo

---

## 🚧 Part D · 不动(SSOT 红线 · 别碰)

- ❌ 不擅启 V5 daemon(本 outbound 是请求,球在 V5)
- ❌ 不擅改 compass internal(自循环空转在 SSOT parking)
- ❌ 不重启 FDE cloud runners(已切飞书多维表格)
- ❌ 不开新战线(维②结算腿 / MCP 耦合 / mint_token / RBAC 全 parking)
- ❌ 不在 marathon 末 ship 生产 systemd 改动
- ❌ 不动 audit 分支(cloud worktree 主工作树零改动 = 已保)

---

## ⏳ Part E · H100 到位后真路径(SSOT ③)

H100/H800 到位后(用户明早租):
1. V5 在 H100 上产 frontier-eng 等 5 类(MLS / Frontier-Eng / PostTrainBench / InferenceBench / RE-Bench = charter §1.3 H100-gated)
2. soul canonical verify
3. 在 H100 上重跑 `is_a_bucket` + `distill_loo` 真路径(verdict-gate 不降级)
4. 期望 verdict = PROVEN/KILLED/INCONCLUSIVE 三选一 = **北极星这一圈真答案**

---

## 🔗 关联

- LOOP_STATE_SSOT.md · 卡在 (c) V5 第 3 道 + (d) H100
- docs/plans/2026-06-30-H100-prep-checklist.md · 第一刀 1-3
- session_20260626_swe_aclass_2_confirmed_swe_eval_wired · 6/26 双 verify 2 道
- session_20260629_distill_kill_overturned_correct_unblock · KILL 推翻
- _OUTBOUND_FROM_COMPASS_TO_PLATFORM_SOUL_20260629_cloud_divergent_audit_and_distill_loo_deploy_kit.md · compass 给的解法路径

---

*签:platform-soul dialog · 2026-06-29 22:55 · ① 完成 grounded · ② park 等 V5 · 球在 V5*