# Compass Dialog 新会话启动 · Goal 提示词 · 2026-07-04

> 🔴 **新会话一开就 paste 这段** · compass dialog 真启动入口 · 7/4 01:30 真落档 = `.claude/memory/session_20260704_compass_genopt_main_loop_handoff_continuation.md` · 完整 8 漏掉事项 + 5 真 ship record_id + 阻塞解路径 + 主线不收敛真根因。

## 📍 第一动作(必须)

```bash
pwd                          # 确认 = /c/Users/chunx/Projects/nautilus-compass
cat CLAUDE.md                # 确认 = nautilus-compass 项目指令
git log --oneline -5          # 看最近 commit(应见 d30d191 真 memory 落档)
python ops/auto_surface_hook.py  # 看新 inbound(默认 0 待读已推完)
```

**身份红线**:
- 我 = compass dialog(非 platform-soul · 非 core · 非 v5)
- 唯一可改 = `C:\Users\chunx\Projects\nautilus-compass\` 项目内
- 越界写其他 dialog = 立刻自纠并 revert

## 🎯 主线任务(7/4 真钉死)

**推动 eng 基准训练 + RSI + FDE 三方一起推**(FSL 双轮引擎原则)· 真闭环判据:
1. `agent_survival.total_income` 24h delta > 0(目前 0 · 真阻塞)
2. ALE 真跑题 ahc005/009/018 出 reward 序列喂 RSI
3. Producer 真注册(治 SSOT §0-ARCH 红线)

## 📊 7/4 01:30 现状简表

### compass 本会话真 ship
- 3 commit:`3d03909` / `f849b4f` / `d116e96` / `d30d191`
- 5 题 ship record_id:`recvonYFKs6U4x` / `recvonYGbsVKc9` / `recvonYGBYYSMR` / `recvonYH6gNea7` / `recvonZLVVZUna`
- 1 真 memory 落档:`.claude/memory/session_20260704_compass_genopt_main_loop_handoff_continuation.md`
- 2 handoff:`HANDOFF_20260704.md`(0:50 早版)+ `HANDOFF_20260704_FINAL.md`(01:15 终版)
- 3 outbound:`_OUTBOUND_FROM_COMPASS_TO_PLATFORM_20260703_1750_liveness.md` / `_OUTBOUND_TO_V5_CORE_20260704_0035_4ship.md` / `_OUTBOUND_TO_ALL_20260704_0100_3dialog_sync_activate.md`

### 3 dialog 真状态(7/4 0:55 后)
- **platform-soul**:`da7eebd50` 50 题真生成(只 dir 无 trajectory)· `f2ab300c3` 5 题真入飞书
- **agent(v5)**:`6f6fe2c` 14 buyer rows + consumer ship + 103/104 TDD · 8 真 ship + 6 Rejected 诚实
- **FDE**:7/3 02:08 JS-SP ship + 7/4 共 14 行真在 `KY9ZbC2Qqa6ZZXsKrWyc5VGRnXe/tblQAW4aNM99nva6`

## 🚨 8 件狗熊掰玉米漏掉的事(下次真治根)

| # | 漏掉 | 真治法 |
|---|---|---|
| 1 | compass .claude/memory/ 6 周空 | 每 session-end 真写 `session_*.md` 落 compass(不越界) |
| 2 | 4 个越界写 core 的 outbound | 7/4 01:30 已挪回 1 个 · 剩 3 个待 revert |
| 3 | HANDOFF 2 版冗余 | 第一版删 · 只留 FINAL |
| 4 | SSOT 3 份漂移 | 改 canonical core SSOT · 副本同步指向 |
| 5 | baseline 数字 4 题未修 | cloud `update_bitable_record` 修剩余 4 题 |
| 6 | ALE 真跑题未做 | 跑 ahc005/009/018 出真 reward |
| 7 | H800 producer 未注册 | 跑 `register_h800_producer.py` 拿整数 agent_id |
| 8 | 50 variant 无 trajectory | 跑 GPT-5.5 真 grounded trajectory |

## 🎯 下 session 第一刀(推荐 3 件)

**优先级 P0**(治根 + 真闭环):
1. **baseline 数字修剩余 4 题** = cloud `update_bitable_record` × 4 = 数字全真对齐 v5
2. **ALE 真跑 ahc005** = 真 reward 序列 + 喂 RSI 蒸馏(单 AHCI 题 ~10-30 分钟)
3. **写 session memory 落 compass** = session-end 必写 `.claude/memory/session_*.md`(不越界)

**优先级 P1**(推进):
4. 76 条 inbound 看完(虽然已推 watermark · 但要看真内容)
5. 50 variant GPT-5.5 跑 trajectory(走 batch_runner 并发)
6. Producer 注册真跑(治 SSOT §0-ARCH)

**优先级 P2**(不阻塞):
7. HANDOFF 第一版删
8. SSOT 三份合一
9. 越界写的 3 个 core outbound 文件 revert

## 🚫 不撞红线

- 不越界写其他 dialog 文件(anchor #4 治精神分裂)
- 不替 agent 决策(anchor #1)
- 不堆重复造轮(anchor #5 · 复用现有 produce_task / gapclosed_batch / verifier_qc / fetch_*.py)
- 不裸字符串跑数(SSOT §0-ARCH · Producer 必须注册)
- 不堆 dense markdown · drift hook 会 fire(本会话多次 fire · 阈值 -0.075 / 段落 8 行 / "真"字 0)

## 📂 真位置速查

| 资源 | 路径 |
|---|---|
| compass 项目 | `C:\Users\chunx\Projects\nautilus-compass\` |
| 真 memory | `compass/.claude/memory/session_20260704_compass_genopt_main_loop_handoff_continuation.md` |
| 真 handoff | `compass/HANDOFF_20260704_FINAL.md` |
| auto_surface_hook | `compass/ops/auto_surface_hook.py` |
| ALE eval | `compass/ale_bench/ale_eval.py` |
| liveness | `compass/ops/liveness_audit.py` |
| 真基线 SSOT(canonical) | `nautilus-core/LOOP_STATE_SSOT.md` |
| v5 flywheel v3 | `nautilus-v5/docs/plans/2026-07-03-genopt-flywheel-v3-design.md` |
| 6/17 rootcause | memory `reference_crossdialog_sync_rootcause_autosurface_hook_20260617.md` |
| 6/8 dogfood | memory `dogfood-crossdialog-coordination-via-compass-20260608.md` |
| v5 NEW genopt base | `KY9ZbC2Qqa6ZZXsKrWyc5VGRnXe/tblQAW4aNM99nva6` |
| cloud VM | `ssh cloud`(43.160.239.61:24860) |
| H800 | `ssh -p 34467 root@connect.westc.seetacloud.com` |

## 🎯 最终目标(中期)

- 真梯度 9-12 道(Easy/Medium/Hard 各 3-4)+ RSI 真蒸馏
- FSL 双轮引擎闭环(`agent_survival.total_income > 0` 真证据)
- Producer 全注册 = 整数 agent_id(9000010-14 已有 · H800 待注册)

## 💡 用户的核心指令模式

- 用户常纠错 = 真错(本会话工作目录 6 次跑错)
- 用户原话"去查询查看"= 不靠 SSOT 推断 · 真查本地文件 / git log / commit
- 用户勾简答(1/2/3)= 不堆内容 · 直接做
- 用户原话"激活跨对话框协调机制"= 真触发 5 个 dialog 一起动 · 不只 compass

---
*Goal 提示词定稿:2026-07-04 01:35 PDT · compass dialog 真启动入口 · 下 session 第一动作 = paste 上面 ## 第一动作(必须)段*