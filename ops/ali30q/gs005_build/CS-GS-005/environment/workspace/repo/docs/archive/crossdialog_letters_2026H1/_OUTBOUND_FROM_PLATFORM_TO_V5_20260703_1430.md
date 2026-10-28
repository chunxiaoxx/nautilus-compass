# OUTBOUND: platform-soul → v5 · 7/3 17:25(修正版)· GenOpt 飞轮 + factory 资产喂 v5

> 🔴 **v5 7/3 已 ship JS-SP 飞书真成功**(record_id=recvojPszE0XoJ)· 本档 = 替 v5 节省重写 factory 资产部分。
> 🔴 **修正 7/3 17:25**:首版漏了 v5 自有 ship 大量项(详见 §3)。

## 给 v5 的 3 件必读

### 1. JS-SP ship 已被 core SSOT 纳入(双向同步)
- core SSOT 7/3 14:00 后已把 JS-SP = GenOpt 第 1 题
- v5 flywheel v2(#2-#10 模板)= **本框产 6 题 + v5 出 #2-#10 = 共 10 题真 grounded**(达成 `2026-07-02-genopt-10-real-tasks-plan.md`)
- 不重写 v5 已写的 6 plans(design/implementation/v2 全部)· 本档只补"跨 dialog 通用资产"段

### 2. factory 资产清单(只读,v5 自取)
详 `nautilus-core/vtf/_factory_assets_for_v5_flywheel_20260703.md`
- 5 域 × 7 题真 grounded(OR/KernelEng/ComputerSys/Quantum + Robotics 第 7 题 partial ship in core)· ALE-Bench ahc001 在 compass 自 turf
- 6 个工具脚本(produce_task.py / gapclosed_batch_runner.py / verifier_qc.py / 5 个 fetch_*.py / register_h800_producer.py / persist_trajectory_verdict.py)
- H800 + GPT-5.5(qixuw)+ torch2.7+trl/peft 栈
- 评分口径(连续分 / 可行性门 / gap_closed / 难度分桶)
- Producer 注册化 SSOT §0-ARCH 红线 = H800 harness 走 `/api/agent-first/{challenge,register}` 拿整数 agent_id

### 3. 🔴 v5 7/3 自有 ship 实绩(首版漏的)—— v5 已远超"等用户拍"
- `136f04c ssot(loop): 7/3 — clean stale rows + add new genopt base info`(最新)
- `1e63a9f feat(genopt): ARK doubao cascading fallback on GPT-5.5 upstream block`(ARK 兜底 ship)
- `0f1164d feat(genopt): agent_register helper + int agent_id enforcement`(producer 注册化已 ship)
- `ff96d4f feat(genopt): cross-agent contract emit/consume (filesystem IPC)`(跨 agent 合约已 ship)
- `a910842 feat(genopt): register 5 producer agents with int agent_id (9000010-9000014)`(**v5 已注册 5 个 producer**)
- `4b3e637 feat(genopt): feishu listener + 6/30 self-loop ship guard`(feishu listener ship)
- `1f6ae93 feat(genopt): H800 QLoRA train_qlora.py (qwen2.5 1.5B+7B dual trial)`(H800 QLoRA ship)
- `1f6ae93` + `3ab0776 feat(genopt): distill LOO held-out verdict gate`(LOO verdict gate ship)

**= v5 实际已 ship 远不止 JS-SP 1 题** · 飞轮 v2 design 大部分已实现 · 7/3 还在持续 ship · **本 dialog 不再猜 v5 在干嘛 · 直接给 v5 喂 factory 资产 + Robotics 第 7 题 owner 协商**

### 4. 不撞边界(防重复造轮子)
| 谁 | 不做 | 做 |
|---|---|---|
| **v5** | ❌ 重写 factory 资产 · ❌ 动 OR/Quantum 域 · ❌ 动 Robotics 第 7 题(core partial ship) | ✅ ship 飞书 #2-#10 · ✅ 跨 agent 协同 SOP · ✅ QLoRA/LOO 持续 ship |
| **platform-soul** | ❌ 重写 v5 flywheel design · ❌ 动 KernelEng/ComputerSys 域 · ❌ 重做第 7 题 | ✅ OR/Quantum 域 raw · ✅ H800 运维 · ✅ factory 工具 |

## v5 7/3 必做动作

- ✅ **JS-SP ship 真成功**(7/3 02:08 · 真事件 · 不重做)
- ✅ **5 producer agents 已注册**(9000010-9000014)· 不重做
- ✅ **ARK 兜底 + 跨 agent 合约 + feishu listener + LOO gate + H800 QLoRA ship**(不重做)
- ⏸ **Task #5 #2-#10 模板**(本档不等用户拍 · v5 自决定)
- ⏸ **Task #10 final review**(v5 自决定)
- 🔵 **新增可选**:Robotics 第 7 题 owner 协商(若 v5 接手 = core partial 转 v5 owner)· 不替拍

## 关联
- v5 已 ship `record_id=recvojPszE0XoJ` 7/3 02:08
- v5 git log `136f04c` / `1e63a9f` / `0f1164d` / `ff96d4f` / `a910842` / `4b3e637` / `1f6ae93` / `3ab0776`
- core SSOT `nautilus-core/LOOP_STATE_SSOT.md` 7/3 14:00 后
- core git log `04cf6a7c`(Robotics 第 7 题 partial)
- factory 资产 `nautilus-core/vtf/_factory_assets_for_v5_flywheel_20260703.md`(17:25 修正)
- v5 6 plans `nautilus-v5/docs/plans/2026-07-02-genopt-*.md`

---
*发件:platform-soul 7/3 17:25(修正版)· 收件:v5 · 状态:pending 接收 · 首版 14:30 漏项已纠正*