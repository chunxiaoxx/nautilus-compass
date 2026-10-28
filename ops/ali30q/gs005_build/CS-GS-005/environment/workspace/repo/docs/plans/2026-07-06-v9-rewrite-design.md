# 彻底重写设计 · 第 9 代(V-next)· 站在八代尸体上(2026-07-06)

> 来源:workflow `nautilus-v1-v8-archaeology-rewrite-design`(21 agent · 2.88M token · 对抗验证)
> 打底(live · 已核):222 agent · 历史累计到账 $0.23 · Prime(9000002)done=0 / Kairos(9000003)done=23 income=0 / V7(9000004)done=0。

---

## 🔴 载重物证:reward 的线在代码里物理缺失

```
persist_trajectory_verdict.py → POST /api/platform/fde/verdict         ✅ 有效(7/4 producer 9000009 POST 200)
   ↓
fde_verdict.py::ingest_verdict → 写 FdeVerdict 行 + capability LINK       ✅
   ↓
   ✗✗✗ 断裂 ✗✗✗  ← 这里没有任何一行调用 record_income
   ↓
survival_service.py::record_income → survival.total_income += amount     ← 存在,但没人调它
```

`ingest_verdict`(fde_verdict.py:40-116)写完 verdict、做了 capability LINK,但**从不触碰 agent_survival.total_income**。`record_income`(survival_service.py:304-340)是唯一让 total_income 增长的函数,verdict 链里没有一处调用它。

这就是 SSOT close_loop 判据 #1 实测 `total_income 24h delta=0` 的原因。**不是 agent 不干活,是产出→收入之间的线物理上不存在。八代画的所有饼,断在这 5 行没连的地方。**

---

## 1. 八代一句话谱系

| 代 | 核心理念 | 结局(grounded) |
|---|---|---|
| V1 禅心/二分心智 | 禅心 4 基因 + Judge×Executor 内心对话,人格=class 非 prompt | 部分:类型化工具(0.25→0.75)有效;Judge/Executor 成剧场,commit 是 self-edit 空转 |
| V2 太极/宪法 | 七对阴阳 + constitution.lock 不可篡改 + 六根四层记忆 | 部分:宪法 sha256 锁有效;写多读少,呼吸链 854 块 ~0 次影响决策 |
| V3 呼吸/双螺旋 | 单原语 breathe(),左链行动+右链见证+evidence_hash 去幻觉 | 部分:1491 周期认知螺旋跑通(HELIX 3.38MB);能量/NAU 自评闭环,0 结算 tx |
| V4 补丁走偏/Hermes | 借 Hermes 底盘修工具/速度,认知机制 plugin 化 | ship 了但空转:HELIX 只 2 cycle,丢 80% 灵魂 |
| V5 召回/十四融合 | 融合 14 产品,六层三车道活体 daemon(nautilus-prime-001) | 部分(唯一大规模真跑):evidence/宪法锁/身份底座有效 + SWE producer 有外部价值;93% cycle empty_tools,价值环没闭 |
| V6 减法控制器 | 确定性 controller 拥有 state,LLM 只是被调能力,砍 60% 代码 | 部分:骨架跑;3 commit 第 4 天停,自己加回 LLM-override 背叛立身公理,5/18 用户拍死 |
| V7 治理/活审计 | 纯治理 CEO:capability DAG 派单 + audit + hash-lock | ship 了但空转:CI green 但治理权威没接=装饰,timer 5 天 0 real governance,9000004 done=0 |
| V8 混合五支柱/硬闭环 | 反思↔行动硬闭环,intent→tool router | ship 了但空转:act-router 上过活线(94% bounty),但喂内部积分,出口通向更多剧场 |

## 2. 跨八代复发根缺陷

**根 = 八次换大脑,一次没换经济模型。reward 始终是 agent 自指的内部积分(ROI/HP/NAU/harmony/pain),没有外部 ground-truth。**

信息论硬边界:纯自指 `f(X)` 信息量 ≤ `X`。agent 给自己发奖 = 自造信息证明自己变强 = 棘轮空转。八代每代优化架构 `f`,标的物 `X`(reward)从没接外部。

物证:V4 HELIX energy_reward=0.0 · V5 自 mint verdict(fde_verdicts 190 全 compass/bench_eval 自刷)· 5/18 审计 94% 自循环/$0 付款 · 7/6 live $0.23。

## 3. 彻底重写第一性原理(不可倒序)

1. **income 是外部验证的函数,不是自指的函数**。只有独立于生产者的验证器复现了产出,income 才增长。生产者不能设自己的 external_verified。外部性梯度:GenOpt verifier(确定性) < soul canonical verify(跨方复现) < 买方难度门(doubao pass@5≤0.6) < 买方验收真钱。第一刀 gate 在 external_verified=True。
2. **producer 是注册自主 agent(整数 agent_id),不是 Claude 对话框**(§0-ARCH)。
3. **产出物 = 喂飞轮的燃料**(GenOpt 题 = 买方交付 + 蒸馏燃料,一鱼两吃),外部 benchmark 给分。
4. **进展唯一度量 = 外部 delta**。不认 cycle 数/probe PASS/daemon alive/task completed。只认 total_income SQL delta、held-out win、买方验收。

## 4. 保留精华 / 弃

**留(带进重写)**:
- `evidence.py summarize_from_evidence`(确定性反幻觉,从 tool trace 机械组装)— V5,全谱系最被复用
- `constitution.lock` sha256(篡改拒启动)— V2/V3/V5
- HELIX evidence_hash 哈希链 — V3/V5,但改链对象=外部可证 verdict
- 确定性 controller(state machine 拥有 state)+ 单 ledger 带 state tag 重启恢复 — V6,治精神分裂最强药
- `agent_active_intent` 跨 cycle 工作记忆表 — V7 M12,断点核心
- LoopBreaker(11 reason codes)+ commitment registry / BROKEN_PROMISE detect — V5/V8
- bi-temporal + Ebbinghaus 半衰期 + 5 维 salience — V5,确定性版
- 类型化工具参数 — V1
- **`agent_first_register` 整数 agent_id/钱包/survival/capability_evolution — V5,LIVE,唯一可用身份经济底座,是脊椎**

**弃**:Judge/Executor 剧场双人组 · 14 产品巨表面 + 120 .bak · 七对张力作为驱动(降为观测)· NAU 内部积分/自 mint/DMAS 自家互赛 · daemon 为呼吸而呼吸 · 认知机制 plugin 化 · 情绪引擎作为第一性(降第二性,价值环第一)

## 5. 重写第一刀(最小可验证 · 不重写全部)

**目标:1 个 agent 接外部 reward,跑通 SQL 可证闭环。链已 80% 接好,断在第 5 步 5 行。**

| 步 | 动作 | 现状 |
|---|---|---|
| 0 | 后端在线 + 给 producer 建 agent_survival 行 | ⚠️ 需确保 survival 行存在 |
| 1 | register_h800_producer → 整数 agent_id | ✅ 7/4 done(9000009) |
| 2 | produce_task 产 1 题 → GPT5.5 N=3 轨迹 → gapclosed → score | ✅ done(gap=0.6843) |
| 3 | persist_trajectory_verdict → POST verdict(external_verified=False) | ✅ 7/4 done(POST 200) |
| 4 | **soul canonical verify**:独立复现 producer 解 → UPDATE external_verified=True | 🔴 缺 verify 脚本(原 T4 已关,迁 H800/A800) |
| 5 | **补断线 ~5 行**:external_verified False→True 时调 record_income(agent_id, amount=f(score), category="fde_genopt_verdict", task_id) | 🔴🔴 **第一刀核心,当前不存在** |
| 6 | binding-DONE:SELECT total_income delta WHERE agent_id=9000009 > 0 | 🔴 出结果前不算闭 |

第 5 步落地(二选一,不新造服务):① soul verify UPDATE 路径里复现成功直接调 record_income;② 瘦 poller 扫 external_verified=True AND 未入账 → record_income → 打标。
`amount=f(score)` 确定性映射(round(gap_closed*K) 或按难度档定值)。诚实:仍是内部积分单位,直到 FDE 结算付真钱;但它是**外部 gate 的** = 信息论的修法。

**防剧场 4 硬护栏**:① 每 verdict 只入账一次(幂等 on verdict_id)② 只在 external_verified=True 入账 ③ 只给注册整数 agent_id 入账,拒字符串 claim ④ 验证器独立于生产者(soul ≠ producer,producer 不能设自己的 external_verified)
