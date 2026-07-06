# 🎯 LOOP STATE · 单一真相源(SSOT)· 所有对话框 session-start 必读

> **这一份是当前闭环状态的唯一权威。** goal 命令 / FRESH_SESSION_PROMPT / 各框记忆与此冲突时,**以此为准**。
> 🔴 **变更协议(治精神分裂·anchor #4)**:任一框改了"当前闭环目标 / 下一动作 / 卡在" → **先改这四行,再开工**。不先改这里 = 各框拿过期框架 = 精神分裂(本 session 的病根)。
> canonical 在 `nautilus-core/LOOP_STATE_SSOT.md` · 副本同步各 repo 根(同 FDE_BUSINESS_CHARTER 机制)。

---

## 🔴 7/5 收口(用户拍 · 暂停扩张)· 覆盖下方 7/2-7/3 四行 · 2026-07-06 sync from core canonical

用户 7/5 反馈"过往一周工作比较混乱"→ 拍 **D 暂停扩张,清点收口**:
- **不产新 GenOpt 题 · 不碰蒸馏 · 不开新战线**
- 锁 **11 题交付甲方(M1+M2)= 最小可闭环**(11 题全 OR JobShop Easy · ship 5/5 + frontier_eval 9/9 + GPT5.5 valid · 缺 doubao 验证 10 题 + user_access_token)
- 完整规划 = `nautilus-core/docs/plans/2026-07-06-genopt-rl-eng-delivery-convergence.md`
- 混乱根因 = 一周 60+ commit / 0 binding-DONE / 417 散落 outbound
- 🔴 **本框(compass)收口活 = 该 plan 的 Task 1.4:Conductor 扫 inbound 恢复 4 框通信**(compass 被点名"沉默 34h+")· 其余(GenOpt 扩量 / MCP 标准远程迁移)= **收口期 park,不开新战线**
  - MCP 标准远程迁移 Task 0-3 已 done+本地验证(branch `feat/mcp-standard-remote-http` @ plugin repo)· Task 4-6(部署)按 7/5 冻结,收口后再解冻
- **下方 7/2-7/3 四行 = 收口期冻结**(收口完再解冻)

---

## 📍 当前活状态(四行·last-updated 2026-07-03 · 收口期冻结 · 见上方 7/5 收口 · sync from nautilus-core 双主线)

> 🔴 **7/3 同步变更**:本框 6/29 SSOT 单线「证或杀蒸馏」= 子目标 B · 7/2 用户在 core 加双主线 A (GenOpt 1000 题交付)。compass 单线= B 子集不矛盾 · 但下读需知 A 也在转。本框不改"负责框/turf"——compass 仍只管 env + feishu + benchmark harness(详见下方 sync 段)。

| 字段 | 值 |
|---|---|
| **当前闭环目标** | **双主线(用户 7/2 拍)**:(A) 🆕 **GenOpt RL 1000 题交付**(买方新单 · Frontier-Eng generative optimization 范式 · SPEC 同步 `nautilus-core/vtf/BUYER_SPEC_GenOpt_RL_20260702.md`)· (B) 证或杀蒸馏(维①)· **本框对 A 的贡献 = compass 认领 KernelEngineering + ComputerSystems 域生产 + env 审查**;**本框对 B 的贡献不变 = compass verify 路径(等 A800 GPU)· 等 V5 产够 n≥12 → compass 官方 harness verify 出 A 类数 → 交 soul LOO** |
| **下一动作** | ① V5 7/3 JS-SP 已 ship 飞书(recvojPszE0XoJ)→ 本框 7/2 卡点「V5 候选 12+ 等 verify」实际已解封 · 仍等 V5 给 n≥12 · **不再单卡 a 字段**(因为 v5 已 ship,后续 n 增只是节奏)② **本框 7/3 新动作:扫 GenOpt 工厂 4 题模板哪些落到本框 turf(KernelEng + ComputerSys)· 把 Attention/Cache 两题 owner 同步给 v5** ③ soul canonical 复核+借 A800 跑 distill_loo --kind swe→verdict(等 GPU) |
| **负责框** | **本框(compass)**:对 A = KernelEngineering + ComputerSystems 域生产(env + Attention/Cache 模板已就绪)· 对 B = verify 路径(等 A800)· 仍按 FDE_BUSINESS_CHARTER §4 turf 不越界 |
| **卡在** | (a) 等 A800(GPU 部署)→ verify_pathA_one 真跑 n=4 复证 = compass 下一步第一刀(SSOT core 已锁候选 A)· 不撞 GenOpt 工厂(本框 factory 资产 = 4 题模板 + verifier_qc + gapclosed_batch_runner · 与 v5 flywheel 各走各路) |

> 📌 **Sync 来源**:`nautilus-core/LOOP_STATE_SSOT.md` last-updated 2026-07-03 14:00 后 · 5 题真 grounded + 第 6 题 QAOA + 4 框催球 outbound · 详 core SSOT | 本框变更协议:不重写,只增量同步 | 下次变化先改 core canonical 再同步本框 | 完整 sync 历史见 `compass/vtf/_inbound_from_core_sync_20260703.md` | 7/3 14:00 用户已 Edit compass 本档
> 📌 **7/6 sync**:从 core canonical 同步 binding-DONE grounded 实测(见下方「当前实测状态」块)· 纠正 compass 副本过时值 `balance=8 被冻` → `income=0` 口径 · PoI 账本 `DORMANT` → 实测 `+1250 GREEN` · 起因 = qixuw 精神分裂教训(compass 7/4-5 重查 core/v5 7/2-4 已知的 qixuw reasoning_effort 根因,3 天重复劳动 = SSOT 未同步的代价)

## 🛡️ 守教训护栏(防 5 坑·6/29 用户拍"蒸馏一条线+守教训")
1. **n≥12 才跑 LOO**(verdict-gate commit 210e0fd24 拦 n<12·防 whipsaw 教训2)
2. **易 django PROVEN → 须非易料复证**(排 over-fit 假迁移·教训3)
3. **confound 先核再下结论**(教训3·本 session 两次找错 FDE 路径=戒)
4. **SSOT 钉死+广播四框**(治精神分裂·教训4)
5. **ship 了必验活**(教训5·FDE cloud runners/compass 探针都得验)

## 🅿️ Parking Lot(冻结·蒸馏 verdict 出前不碰)
- 维②经济环(credit 口径/结算腿 liveness)· compass MCP 耦合(Phase 1-4)· 平台 mint_mcp_token · FDE 招募/RBAC/4 skill 发版 · content-engine 命名合约 · 维① KILL 资产保留(未来上 H800/换真难料重启)
- **FDE 切飞书多维表格**:执行路径已变(飞书→多维表格→「ECC-三类业务生产管理」base 14 表)·非 cloud systemd runners。FDE 下次同步进 SSOT 细节。

### 🛠️ 破自循环通道(锚点③ 预备·scope 严格)
- **实证**(6/29 grounded DB):fde_verdicts 今日 190 全 `compass/bench_eval` source·task_uid 全 `compass_exp_*_automint_<ts>`·engine_cycle_outcomes 今日 0·`soul_alive=True` 靠自循环刷的剧场。
- **scope**(用户 6/29 拍 B·微破):仅为**蒸馏 verdict 留通道**,不变成通用维②清理(踩教训1)。
  - 加 1 列:`fde_verdicts.external_verified bool`(默认 false·仅 soul canonical verify 标 True)。
  - 改 1 判据:`control_plane.soul_alive` 按 `MAX(external_verified_at)` 新鲜度算(非 cycle stale_hours)。
  - 内循环(auto-mint / bench_eval)继续跑·只是不再"算活/入账"——**不改 compass 内部逻辑**(V5/compass turf 不动)。
  - 不写新服务/不写新 runner/不写新 webhook——复用现有 soul canonical verify 加 1 行 UPDATE。

## ✅ binding-DONE 判据(外部可证·任一框可查·治目标无限膨胀)
闭环 = 下面三条**全 grounded 成立**:
1. `agent_survival.total_income` 因真外部验证产出(soul-canonical / held-out)增长
2. Kairos 脱离 critical(balance ≥ min 20·当前 8 被冻)
3. PoI 账本恢复增长(compass `probe_ledger_growth` 从 DORMANT → GREEN)

**判据成立前不算闭·不开新战线。** 不是"我觉得行了",是这三条 SQL/探针返回真值。

### 📊 当前实测状态(sync from core canonical · 实测 2026-06-29 23:30 · compass 7/6 同步,非本框重测)
> 🔴 grounded 纠正 compass 副本两处过时值(治精神分裂):
> 1. ❌ `total_income` 24h delta = **0**(213 rows · 无外部验证驱动的收入增长)— 判据 #1 **未成立 = 当前唯一缺口**
> 2. ⚠️ Kairos = `alive / GROWING / income=0` — **"balance=8 被冻"是过时推断**(core 6/29 实测纠正:schema 无 balance 字段,当前不 critical),判据 #2 口径改看 income
> 3. ✅ `platform_nau_ledger` 24h delta = **+1250**(71 行新增 · last_entry 6/29 23:30)— 账本活跃增长,判据 #3 **实际已 GREEN**(非 DORMANT)
> 📌 净:3 条判据里 #3 已成立、#2 口径修正、**#1(外部验证收入)仍是唯一未闭缺口**。下一步不扩题,把已产题走 soul canonical verify → 外部 reward 入账。

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
