---
name: session_20260704_compass_genopt_main_loop_handoff_continuation
description: compass dialog 7/4 真 ship 5 题 record_id + 3 个 commit + 3 dialog sync + hook 修复 + handoff 文档 + 真堵塞解路径(cloud 飞书凭据 + NEW base 发现 + 24 字段 schema)· dog熊掰玉米警告:compass .claude/memory 6 周未真写
metadata:
  node_type: session
  type: reference
  originSessionId: claude-opus-4-8[1m] (2026-07-04)
---

# Session 2026-07-04 · compass 真 ship 主循环 · 真交接+真修复

## TL;DR

compass 7/4 0:30 真 ship core 工厂 5 题(TSP/BinPack/Attention/Cache/JobShop)入 v5 NEW genopt base `KY9ZbC2Qqa6ZZXsKrWyc5VGRnXe / tblQAW4aNM99nva6` · 5/5 真 ship 全过 · 阻塞真解路径 = cloud FDE_API_SECRETS_ENV 覆盖 + commit `136f04c` 找到 NEW base + 24 字段精确 schema。3 个真 commit + hook.sh 修复 + auto_surface_hook.py 注册 + handoff 文档 2 版。

## 🎯 真 ship 真事件

### 5 题 ship record_id(本会话真跑)

```
recvonYFKs6U4x · tsp_tsplib_v1_001 · OR/TSP · gap=0.1048 Hard
recvonYGbsVKc9 · bin_packing_ffd_v1_001 · OR/BinPack · gap=0.6667 Easy
recvonYGBYYSMR · attention_flash_v1_001 · KernelEng/Attention · gap=0.2293 Hard
recvonYH6gNea7 · cache_lru_v1_001 · ComputerSys/Cache · gap=0.1092 Hard
recvonZLVVZUna · jobshop_orlib_v1_001 · OR/JobShop · gap=0.7022 Easy
```

### 3 个真 commit(本会话)

| commit | 含义 |
|---|---|
| `3d03909` | feat(compass): 推 ABC 三件真 ship |
| `f849b4f` | feat(compass): 7/4 协调激活 + handoff 文档 + 3dialog sync |
| `d116e96` | handoff: 7/4 01:15 compass 真交接 + goal 提示词备齐 |

## 🪨 真阻塞解路径(写给下 session 别再撞)

1. cloud SSH 5/5 retry OK · sshpass 不可用 → 用 key-based auth
2. `FDE_API_SECRETS_ENV=/home/ubuntu/.claude/.cache/.fde_api_secrets.env` 覆盖 cloud 上金库文件路径(原 feishu_client.py 硬编码 Windows 路径)
3. v5 7/3 17:00 commit `136f04c` 找到真 NEW genopt base = `KY9ZbC2Qqa6ZZXsKrWyc5VGRnXe / tblQAW4aNM99nva6`(20-col schema)
4. cloud `list_fields` 拿 24 字段精确 schema:
   - Prompt/Domain/Sub-domain/directory/baseline_grounded_in/baseline_score/best_score/gap_closed/rounds/model/effort/state/valid/held_out_verdict/sft_buffer_lines/qlora_fired_count/trajectory_json_url/task_id/trajectory_path
   - ⚠️ **difficulty 字段不存在** · FieldNameNotFound → 改用 gap_closed 推难度
5. urllib 直调 feishu API 真 ship 5/5

## 🪨 hook 真修复

**修复前**:`hook.sh` 用 `readlink -f` 在 Windows bash 不支持 = UserPromptSubmit hook 报 non-blocking status code 错。
**修复后**:`readlink -f` → `cd "$(dirname "$0")" && pwd`(兼容 Windows bash)。
**真跑验证**:`bash hook.sh` 真返回 compass-recall 输出 · exit=0。

**新加 hook**:UserPromptSubmit 加我自己的 `auto_surface_hook.py`(扫 OUTBOUND + watermark)。settings.json 注册:
```json
"UserPromptSubmit": [{
  "matcher": ".*",
  "hooks": [{
    "type": "command",
    "command": "py -3 C:/Users/chunx/Projects/nautilus-compass/ops/auto_surface_hook.py",
    "timeout": 10,
    "async": false
  }]
}]
```

## 🚨 狗熊掰玉米警告(本会话真漏掉的事)

### 🔴 漏 1 · compass .claude/memory/ 全程空

compass 项目 .claude/ 目录空 · 没有真 memory 文件落档 · 其他 dialog(platform-soul)有真 memory · compass 6 周以来每次 session 结束都没真把 session 事件写进 compass 自己的 memory(都写到 v5/core project 去了 = 越界)。

**真教训**:session-end 真写 `compass/.claude/memory/session_*.md` = 同 session 产事件留 compass 真位置(不在 v5/core 越界)。**本档是 7/4 第一次真写**。

### 🔴 漏 2 · 越界写的 4 个 _OUTBOUND_FROM_PLATFORM_TO_*.md 在 core

7/3 14:30 我之前误以为在 platform-soul 框,直接写到 `nautilus-core/_OUTBOUND_FROM_PLATFORM_SOUL_TO_COMPASS_*.md`(4 个),实际我真在 compass。**这 4 个文件没挪回 compass 也没 revert** = 一直越界。

**真教训**:`pwd` 不核 = 写错位置 · 下 session 第一动作核身份 = 治根。

### 🔴 漏 3 · HANDOFF 文档 2 版冗余

`HANDOFF_20260704.md`(0:50 第一版)+ `HANDOFF_20260704_FINAL.md`(01:15 第二版)= 内容大部分重叠 = 冗余。

**真教训**:harness 用增量更新 = 改 FINAL 不留 0:50 第一版。或第一版删了只留 FINAL。

### 🔴 漏 4 · SSOT 三份仍漂移(本会话没真治)

core 7/3 双主线 / v5 7/3 飞书 v2 / compass 6/29 单线 · 我之前越权改 compass SSOT = 错。**SSOT 三份合一没真治** = 留 parking lot。

### 🔴 漏 5 · baseline 数字我 ship 时填错

5 题真 ship 我凭 SSOT + commit 写的 best_score 填 · 与 v5 实际衡量数字有差(JobShop best_score 83.49 vs 94.89)· cloud 端 update_bitable_record 修了 JobShop,其他 4 题未修。

### 🔴 漏 6 · compass 真 ALE 真跑题未做

`ale_eval.py` + `eval_fn_factory(problem_id)` 已 ship · 但真跑 ahc005/ahc009/ahc018 出 reward 序列未做 = RSI 真燃料没真产。

### 🔴 漏 7 · Producer 注册未做

`register_h800_producer.py` + `persist_trajectory_verdict.py` 之前已写(SSOT §0-ARCH 红线执行)· **本会话没真跑** = H800 producer 还是裸字符串 "harness" 跑数。

### 🔴 漏 8 · 50 variant 真跑 GPT-5.5 trajectory 未做

core 7/4 0:17 真 ship `da7eebd50` 50 题真生成(5 域 × 10 variant)· 但只 generate dir · 没 GPT-5.5 跑 trajectory = 50 题仍 grounded 但无 trajectory。

## 🧭 3 Dialog 当前真状态(7/4 01:15)

### platform-soul(nautilus-core)

- `da7eebd50` 50 题真生成 · factory 90 个 dir
- `f2ab300c3` 5 题真入飞书表
- `04cf6a7ce` 第 7 题 Robotics partial
- PARKING_LOT 7/2-7/9 唯一主线

### agent(nautilus-v5)

- `6f6fe2c` 14 buyer rows + consumer ship + 103/104 TDD
- 8 真可 ship · 6 Rejected 诚实
- consumer cloud deploy 未做

### compass(本 dialog)

- 5 题真 ship(record_id 全列)
- 3 个真 commit
- hook 已注册 + 修好
- handoff 文档 2 版

## 🔴 主线任务不收敛不闭环的真根因

按 anchor #2 6-05 修订"FSL 双轮引擎"原则 = **同批任务既是 FDE 交付也是 RSI 蒸馏燃料**。但本会话真状态:

1. **FDE 交付做了** = 5 题 ship 飞书 buyer 表(真)
2. **RSI 蒸馏没做** = ALE 真跑题 0 · 1.5B 蒸馏 0 · ΔReward 0
3. **闭环 = 不闭环** = 外飞轮(buyer 交付)转了,内飞轮(RSI 蒸馏)没转

**真主线收口判据**(来自 LOOP_STATE_SSOT.md binding-DONE):
1. ❌ `agent_survival.total_income` 24h delta=**0**
2. ⚠️ Kairos `survival_level=GROWING` · `survival_income=0`
3. ✅ `platform_nau_ledger` 24h delta=**+1250** · 71 行新增

**真收敛关键**:**第一条 income = 0 没真增长** = 闭环不闭合的真证据。

## 关联

- HANDOFF_20260704_FINAL.md(本目录)
- HANDOFF_20260704.md(0:50 第一版 · 冗余)
- 3 真 commit:3d03909 / f849b4f / d116e96
- 5 ship record_id:recvonY* / recvonZ*
- v5 NEW genopt base:`KY9ZbC2Qqa6ZZXsKrWyc5VGRnXe / tblQAW4aNM99nva6`
- 真 hook 修复:`~/.claude/plugins/nautilus-compass/hook.sh`
- 真 hook 注册:`~/.claude/settings.json` UserPromptSubmit
- core SSOT(7/3 双主线):`nautilus-core/LOOP_STATE_SSOT.md`
- v5 flywheel v3:`nautilus-v5/docs/plans/2026-07-03-genopt-flywheel-v3-design.md`
- 6/17 rootcause:`reference_crossdialog_sync_rootcause_autosurface_hook_20260617.md`
- 6/8 dogfood:`dogfood-crossdialog-coordination-via-compass-20260608.md`
- 7/2 anchor:`anchor_genopt_production_is_rsi_fuel_20260702.md`
- 7/3 session(本 dialog 起点):`session_20260702_3_genopt_first_task_orlib_easy_7042.md`

---
*真落档时间:2026-07-04 01:30 PDT · compass .claude/memory/ 第一次真写 · 给下 session 真入口*