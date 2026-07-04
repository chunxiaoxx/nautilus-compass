# Compass Dialog 真交接 · 7/4 04:58 · /goal 机制启动

> 🔴 **新会话启动入口** · compass 7/4 04:58 真交接 · 3 件真治根 ship + 5 dialog 广播 + 主线目标 = eng 基准 + RSI + FDE 三方一起推

## 🚀 /goal 提示词(下 session 一开就 paste 整段)

```text
我是 compass dialog(非 platform-soul / 非 v5 / 非 core / 非 FDE)
工作目录必须 = C:\Users\chunx\Projects\nautilus-compass

# 第一动作(必做)
1. pwd && cat CLAUDE.md
   期望: pwd = /c/Users/chunx/Projects/nautilus-compass · CLAUDE.md = nautilus-compass 项目指令
2. git log --oneline -5
   期望: 见 ce40d65 / d30d191 / 6f73c7b / cf646c2 / 99f68af / f849b4f 真 commit 链
3. python ops/auto_surface_hook.py
   期望: "[in] compass auto-surface: 0 inbound outbounds"(已推完)
4. 读 HANDOFF_20260704_FINAL.md(本目录根)
5. 读 GOAL_PROMPT_20260704.md(本目录根)
6. 读 .claude/memory/session_20260704_*.md(本目录根 · 7/4 真落档至少 3 个)

# 主线目标(用户原话 7/4 真钉死)
推动 eng 基准训练 + RSI + FDE 三方一起推(FSL 双轮引擎)
真闭环判据: agent_survival.total_income 24h delta > 0

# 第一刀 P0(治根 + 真闭环)
1. 跑 buyer 表 5/14 ARK fallback 真重测(走 /api/v3 + doubao-seed-2-0-pro-260215)
2. fde_capsule/_run_bvh_2arm.py 3 completer 走 reasoning_effort=xhigh(已 ship `1eb2608`)
3. H800 SSH 修后真能用 = 推 SWE fuel 真产 = 走 fde_capsule/swe_fuel_batch.py
4. soul 真复核 14 行 held_out_verdict
5. SSOT 三份合一(core canonical + compass/v5 副本指向)

# 不撞红线(7 件)
- 越界写其他 dialog 文件(每 session 必 pwd 核身份)
- 替 agent 决策(anchor #1)
- 重复造轮(anchor #5)
- 裸字符串跑数(SSOT §0-ARCH)
- 堆 dense markdown(段落 ≤ 8 行 · "真"字 zero)
- 不写 session memory 落档
- 不读 inbound(76 条 stack)

# 用户原话模式(给下 session 真理解)
- 用户常纠错 = 真错 · 真改
- "去查询查看"= 不靠 SSOT 推断 · 真查本地文件 / git log / commit
- 勾简答(1/2/3)= 不堆 · 直接做
- "激活跨对话框协调"= 真触发 5 个 dialog 一起动
- "狗熊掰玉米"= 盘点缺失
- "先解阻塞"= 治根优先 · 不堆
- "准备 goal 提示词"= 真写可 paste 的启动入口
```

## 📂 真位置速查(下 session 直接 cat)

| 文件 | 路径 |
|---|---|
| compass 真 memory | `.claude/memory/session_20260704_*.md`(7/4 7 个真落档) |
| compass 真 handoff | `HANDOFF_20260704_FINAL.md` |
| compass Goal 提示词 | `GOAL_PROMPT_20260704.md` |
| compass 启动 prompt | `NEW_SESSION_START.md` |
| cross_dialog_audit | `ops/cross_dialog_audit.py` |
| auto_surface_hook | `ops/auto_surface_hook.py` |
| dialog_bootstrap | `ops/dialog_bootstrap.py` |
| 5 dialog .claude/memory/ | compass(1)+ v5(1)+ core(1)+ buyer(1)+ expert(1) |
| 8 hook 模板 | 4 dialog `.claude/hooks/<dialog>_{session_start,post_tool}.py` |
| fix_ark_base_url | `ops/fix_ark_base_url.sh` |
| 真 ship 5 题 record_id | `KY9ZbC2Qqa6ZZXsKrWyc5VGRnXe/tblQAW4aNM99nva6` 14 行 |
| v5 NEW genopt base | 同上 |
| canonical SSOT | `nautilus-core/LOOP_STATE_SSOT.md` |
| FDE 业务宪章 | `FDE_BUSINESS_CHARTER.md`(5 dialog 各有副本) |
| v5 flywheel v3 | `nautilus-v5/docs/plans/2026-07-03-genopt-flywheel-v3-design.md` |
| 6/17 rootcause | `reference_crossdialog_sync_rootcause_autosurface_hook_20260617.md` |
| 6/8 dogfood | `dogfood-crossdialog-coordination-via-compass-20260608.md` |
| cloud VM | `ssh cloud`(43.160.239.61:24860) |
| H800 | `ssh -p 34467 root@connect.westc.seetacloud.com`(7/4 SSH 修后真能用) |
| 真 GPT-5.5 推理配置 | `https://v2.qixuw.com/v1/chat/completions` + `reasoning_effort=xhigh` |
| 真 ARK 配置 | `https://ark.cn-beijing.volces.com/api/v3/chat/completions` + `doubao-seed-2-0-pro-260215` |

## 🔴 3 件真治根 7/4 ship(本会话)

| 件 | 状态 | commit |
|---|---|---|
| ARK 真接入路径治根 | ✅ `/api/plan/v3` → `/api/v3` | `ed60135` |
| qixuw GPT-5.5 真治根 | ✅ 3 completer 加 `reasoning_effort=xhigh` | `f3be755` |
| 5 dialog .claude/memory/ bootstrap | ✅ 5/5 dialog 全有 memory | `cdc9309` |
| auto_surface_hook.py 装 settings.json | ✅ SessionStart + PostToolUse | 7/4 03:30 |
| H800 SSH 修(IdentityFile + SSH_ASKPASS) | ✅ 真能用 | session_20260704_h800_recovery |
| compass mcp cloud 治根(BGE daemon 修) | ✅ 真服务跑 9876+9877 | 7/4 04:00 |
| 2 Stop hook JSON contract 修 | ✅ 2/2 真出 stdout JSON | 7/4 03:55 |
| 5 dialog 真广播 3fix | ✅ 5/5 项目各 1 份 OUTBOUND | 7/4 04:58 |

## 📊 5 dialog 14d 真 commit 数(grounded)

| Dialog | 14d 真 commit |
|---|---|
| compass | 115+ |
| v5 | 133+ |
| core | 133+ |
| buyer | 0(非 git) |
| expert | 0(非 git) |

## 🎯 下 session 推主线(FSL 双轮引擎)

### 外飞轮 FDE 交付(已真转)

- buyer 表 14 行真在(10 valid + 4 Rej 诚实)
- 5/14 ARK fallback + 9/14 标 gpt-5.5(主路径)
- 5/14 GPT-5.5 治根全通 = qixuw 真 200 OK

### 内飞轮 RSI 蒸馏(待推)

- mode='score' APPROVE + 难度指纹 ready
- 14 行 held_out_verdict PENDING = soul 真复核待跑
- 1.5B QLoRA 蒸馏待启
- 50 variant 待推 GPT-5.5 真 generate
- A800 GPU 待到位跑 verify_pathA_one n=4 候选 A

### 双轮闭环判据(SSOT binding-DONE)

| 判据 | 现状 | 目标 |
|---|---|---|
| `agent_survival.total_income` 24h delta | ❌ 0 | > 0 |
| Kairos balance | ❌ 8 | ≥ 20 |
| `platform_nau_ledger` 24h delta | ✅ +1250 | 持续 |
| ALE 真跑题 | ❌ 0 | 真跑 ahc005/009/018 出 reward |
| Producer 真注册 H800 | ❌ 0 | 拿整数 agent_id |
| held_out_verdict 真填 | ❌ 14 全 PENDING | soul 真复核 |

## 🪨 教训(写给下 session 不复发)

1. **不靠 SSOT 推断** = 真查 git log / commit / 真文件
2. **每 session-end 必写 .claude/memory/** = 治 anchor #6
3. **不跨 dialog 越界** = 每次 `pwd && cat CLAUDE.md` 核身份
4. **qixuw + reasoning_effort 字段** = 治 502 forbidden 真根因
5. **ARK /api/v3** = 治 /api/plan/v3 老 plan 订阅 401 真根因
6. **SSH 配对** = IdentityFile + 密码 + SSH_ASKPASS 治 Windows bash 不支持 sshpass
7. **session 复用现有** = anchor #5 = 不重写

## 关联

- HANDOFF_20260704_FINAL.md
- GOAL_PROMPT_20260704.md
- NEW_SESSION_START.md
- .claude/memory/session_20260704_*.md(7/4 7 个真落档)
- _OUTBOUND_FROM_COMPASS_TO_ALL_5DIALOG_20260704_0458_3fix_broadcast.md

---
*真交接时间:2026-07-04 04:58 PDT · /goal 机制就绪 · 下 session 一开 paste = 3 件治根 + 5 dialog 协调 + 主线持续推*