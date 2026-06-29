# 🎯 LOOP STATE · 单一真相源(SSOT)· 所有对话框 session-start 必读

> **这一份是当前闭环状态的唯一权威。** goal 命令 / FRESH_SESSION_PROMPT / 各框记忆与此冲突时,**以此为准**。
> 🔴 **变更协议(治精神分裂·anchor #4)**:任一框改了"当前闭环目标 / 下一动作 / 卡在" → **先改这四行,再开工**。不先改这里 = 各框拿过期框架 = 精神分裂(本 session 的病根)。
> canonical 在 `nautilus-core/LOOP_STATE_SSOT.md` · 副本同步各 repo 根(同 FDE_BUSINESS_CHARTER 机制)。

---

## 📍 当前活状态(四行·last-updated 2026-06-29)

| 字段 | 值 |
|---|---|
| **当前闭环目标** | 闭**维②经济环**:`agent_survival.total_income` 因**真外部验证产出**增长(非内部刷分) |
| **下一动作** | ① platform 修结算 runner liveness(入账→total_income)② soul 落 verified 信号通道 ③ 定"credit 多少算真干活"口径(防自循环空转累积) |
| **负责框** | platform-soul(①)/ soul-verify(②)(③口径)/ V5(③执行)· 三框协同 |
| **卡在** | (a) PoI 账本**已恢复增长**(6/29 +66·1507 行·GREEN)但"credit 是否反映真价值 vs 自循环累积"未定✅ 结构闭·口径未闭 (b) 结算 runner(`flush_pending_nau`)liveness 未确认 + 7天延迟 |

## ✅ binding-DONE 判据(外部可证·任一框可查·治目标无限膨胀)
闭环 = 下面三条**全 grounded 成立**:
1. `agent_survival.total_income` 因真外部验证产出(soul-canonical / held-out)增长
2. Kairos 脱离 critical(balance ≥ min 20·当前 8 被冻)
3. PoI 账本恢复增长(compass `probe_ledger_growth` 从 DORMANT → GREEN)

**判据成立前不算闭·不开新战线。** 不是"我觉得行了",是这三条 SQL/探针返回真值。

## 🅿️ Parking Lot(冻结·闭上面环之前不碰)
- **维①蒸馏**:当前配置(T4+稀缺易料+小模型)**KILLED**(四根结构性不可证)。资产保留(SWE eval 管线 commit `3a03934d4` + 2 道三方 verify A 类)。**未来上 H800 / 换真难料才重启**。
- **SWE 批产到 n≈12**:蒸馏 defer 了·别盲凑(反 D)。
- FDE 三类业务线 / content-engine 命名合约 / 其它 → parking。

## 🧭 收敛机制(为什么这样安排·别走回头路)
- **同步** = 这份 SSOT(各框读同一份·变更先改这里)。
- **收敛** = 把闭环**执行搬出对话框、进常驻自治 agent**(daemon/conductor/结算 cron 跑 systemd·对话框退回战略/验证/纠偏·不 crank)。对话框是脚手架·不是执行路径(§0-ARCH)。
- **落地** = 一次一个外部可证的 binding-DONE(上面判据)。
- 详 `feedback_workflow_lock_goal_until_done` + `reference_platform_history_architecture_review_20260622`(最大未闭缝=producer 没收口到注册自主 agent)。

## 各框 turf(不越界)
- **platform-soul**:平台 infra / 结算 / dispatch / 部署 / SWE eval / benchmark verify / 标准 QC。
- **soul-verify**:canonical verify(verify_pathA_one)/ 难度门 / verdict-gate。
- **V5**:producer(产候选/轨迹)/ daemon 大脑 / external_reward 入账 / RSI。
- **compass**:记忆/recall/PoI/drift/governance / benchmark env+eval / liveness 探针 / feishu 读写。

---
*维护:闭环目标/动作/判据有变 → 改本文件 canonical(nautilus-core)+ 同步各 repo 根。变更同时记 memory + 广播。*
