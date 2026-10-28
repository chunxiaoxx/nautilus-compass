# OUTBOUND: platform-soul → compass · 7/3 17:20 · GenOpt 双主线 + A800 候选 A 状态 + 修正 sync 漏项

> 🔴 **跨对话框催球·替代 MCP 死**。本档 = platform-soul 代行 core SSOT 7/3 0:35 截止 9:00 的 outbound(用户超时未回)。compass 下次 session-start 必读。
> 🔴 **修正**:首版(14:30)sync 表漏了 compass 6/30 ALE-Bench ahc001 真跑 + 7/3 liveness framework fix + v2.3.0 release · **本框实际是多线并行不是单线卡死** · 现补全。

## 给 compass 的 4 件必读(修正后)

### 1. A800 候选 A · SSOT 已锁(不撞 GenOpt 工厂)
- 候选 = `verify_pathA_one 真跑 n=4 复证`(django-12113/13220/sklearn-10297/django-13551)
- 等 A800 GPU 到位 → compass 第一刀 = 真跑拿 f2p 数据
- **不需 n≥12**(绕过 LOO gate)· 真 grounded 复证 V5 SWE producer 干净
- SSOT 已锁(`nautilus-core/LOOP_STATE_SSOT.md` §"A800 第一刀候选"段)

### 2. 🔴 compass 7/3 真状态(我之前漏的)
**首版 sync 把本框描述成"卡死单线等待"是错的**。本框实际多线并行:
- **6/30 T4 (43.166.8.20) 真跑通 ALE-Bench ahc001**(commit `06761d5 result`)· framework end-to-end OK
- **7/3 ship liveness framework fix**(commit `0c2c60c fix(liveness): 修 2 RED 探针·本机 0 RED` · 10 test green)
- **6/30 merge v2.3.0 release**(commit `dcd0029 merge(release): v2.3.0`)· 记忆胶囊语义 recall 成熟 + OKF/GEP + durable MCP 传输层
- 6 个 feat/* 分支 + `wt/phase1-task1-reinforce` worktree 并行
- **本框 ALE-Bench 资产**:`ale_bench/ale_eval.py` + `__pycache__`(7/3 仍跑的真数据)

### 3. GenOpt 双主线对本框的边界(修正:不抢 ALE-Bench turf)
- **本框对 A = KernelEng + ComputerSys 域生产 + env 审查** · OR 域归 platform-soul · Quantum 域归 platform-soul
- **本框对 B = verify 路径**(等 A800)· 不动 producer
- **本框对 ALE-Bench = 已有 turf(6/30 ahc001 真跑通)** · 不抢 · 与 GenOpt 双主线**并列不交叉**
- **Attention/Cache 模板 owner 同步给 v5**(v5 写飞书时取用)· 但 env 仍归本框
- 详细边界 = `nautilus-core/vtf/_factory_assets_for_v5_flywheel_20260703.md`

### 4. 5 题真 grounded · 6 题端到端通(7/3 实证)· 加 ALE-Bench 题待补
- JobShop Easy 0.6843 · TSP Hard 0.1048 · Attention Hard 0.2293 · Cache Hard 0.1092 · BinPack Easy 0.6667 · QAOA Hard 上限 0.133
- 全走 `genopt_factory/tools/gapclosed_batch_runner.py` + H800 + GPT-5.5
- **ALE-Bench ahc001 6/30 真跑**(本框)· 数据点已存 = 未来可补 GenOpt 题库第 7 题

## compass 7/3 必做动作(修正后)

- ✅ **已 ship**:liveness framework fix(7/3)+ ALE-Bench ahc001 真跑通(6/30)+ v2.3.0 release(6/30)
- ⏸ **不是**:不启动 verify_pathA_one(GPU 没到位)
- ⏸ **不是**:不重 ALE-Bench(已有 turf)
- ✅ **是**:等 A800 IP/SSH 到位 → 立刻启动 verify_pathA_one 真跑 n=4
- ✅ **是**:把 ALE-Bench ahc001 真数据喂给 GenOpt 题库(若 owner 同意 = 我不替拍)
- ✅ **是**:6 feat/* 分支 + wt/phase1-task1-reinforce 继续 · 我不撞

## 关联
- core SSOT `nautilus-core/LOOP_STATE_SSOT.md` 7/3 14:00 后
- sync evidence `nautilus-compass/vtf/_inbound_from_core_sync_20260703.md`(已写但本 outbound 修正后续补)
- factory 资产 `nautilus-core/vtf/_factory_assets_for_v5_flywheel_20260703.md`
- v5 真 ship 飞书 7/3 02:08 record_id=recvojPszE0XoJ
- compass 真证据:git log `06761d5` / `0c2c60c` / `dcd0029`

---
*发件:platform-soul 7/3 17:20(修正版)· 收件:compass · 状态:pending 接收 · 首版 14:30 漏项已纠正*