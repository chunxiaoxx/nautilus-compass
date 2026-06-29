# 🎯 LOOP STATE · 单一真相源(SSOT)· 所有对话框 session-start 必读

> **这一份是当前闭环状态的唯一权威。** goal 命令 / FRESH_SESSION_PROMPT / 各框记忆与此冲突时,**以此为准**。
> 🔴 **变更协议(治精神分裂·anchor #4)**:任一框改了"当前闭环目标 / 下一动作 / 卡在" → **先改这四行,再开工**。不先改这里 = 各框拿过期框架 = 精神分裂(本 session 的病根)。
> canonical 在 `nautilus-core/LOOP_STATE_SSOT.md` · 副本同步各 repo 根(同 FDE_BUSINESS_CHARTER 机制)。

---

## 📍 当前活状态(四行·last-updated 2026-06-29)

| 字段 | 值 |
|---|---|
| **当前闭环目标** | **证或杀蒸馏(维①)**=北极星 forcing function。V5 产→compass verify→soul LOO→verdict。**一条线·其余 parking(守教训1反搭建≠闭环)** |
| **下一动作** | ① V5 产够 n≥12 候选就停(别无限产 GLM·反 D)→ 交 compass ② compass 官方 harness verify 出 A 类数 ③ soul canonical 复核+归一化+借 GPU 跑 distill_loo --kind swe→verdict |
| **负责框** | V5(①)/ compass(②verify+借GPU)/ soul(③复核+LOO)· FDE 仅同步切飞书多维表格进 SSOT |
| **卡在** | (a) V5 候选产完未 verify(当前 12+ 候选·produce_glm 15:00 还在产) ① compass verify 待启动 |

## 🛡️ 守教训护栏(防 5 坑·6/29 用户拍"蒸馏一条线+守教训")
1. **n≥12 才跑 LOO**(verdict-gate commit 210e0fd24 拦 n<12·防 whipsaw 教训2)
2. **易 django PROVEN → 须非易料复证**(排 over-fit 假迁移·教训3)
3. **confound 先核再下结论**(教训3·本 session 两次找错 FDE 路径=戒)
4. **SSOT 钉死+广播四框**(治精神分裂·教训4)
5. **ship 了必验活**(教训5·FDE cloud runners/compass 探针都得验)

## 🅿️ Parking Lot(冻结·蒸馏 verdict 出前不碰)
- 维②经济环(credit 口径/结算腿 liveness)· compass MCP 耦合(Phase 1-4)· 平台 mint_mcp_token · FDE 招募/RBAC/4 skill 发版 · content-engine 命名合约 · 维① KILL 资产保留(未来上 H800/换真难料重启)
- **FDE 切飞书多维表格**:执行路径已变(飞书→多维表格→「ECC-三类业务生产管理」base 14 表)·非 cloud systemd runners。FDE 下次同步进 SSOT 细节。

## ✅ binding-DONE 判据(外部可证·任一框可查·治目标无限膨胀)
闭环 = 下面三条**全 grounded 成立**:
1. `agent_survival.total_income` 因真外部验证产出(soul-canonical / held-out)增长
2. Kairos 脱离 critical(balance ≥ min 20·当前 8 被冻)
3. PoI 账本恢复增长(compass `probe_ledger_growth` 从 DORMANT → GREEN)

**判据成立前不算闭·不开新战线。** 不是"我觉得行了",是这三条 SQL/探针返回真值。

## 🅿️ Parking Lot(冻结·闭上面环之前不碰)
- ~~维①蒸馏 KILLED~~ → **6/29 推翻 KILL·正确 unblock**(用 n≥12+非易料重跑·非 n=2 whipsaw)。
- **SWE 批产到 n≈12**:进行中·V5 turf·优先非易 django 避 over-fit confound。
- FDE 三类业务线 / content-engine 命名合约 / 其它 → parking。

## 📌 6/29 推翻 KILL 的诚实条件(防 whipsaw)
- **不是** n=2 LOO(统计无意义·verdict-gate BLOCK n<12·撞 over-fit confound)。
- **是** V5 续产到 n≥12(同族 django 或换真难非易燃料)→ soul verify → 借 compass GPU(GPU 服务器一直开着·非阻塞)→ distill_loo --kind swe → 对比 ALE 0.0833。
- 若易 django PROVEN → 须用非易料复证(排 over-fit 假迁移)·否则不算破墙。

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
