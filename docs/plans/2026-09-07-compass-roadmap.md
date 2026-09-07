# compass 发展规划 v2(2026-09-07 理论日定稿 · 四维度系统版)

> trace: compass-roadmap-20260907-v2 · 取代同日 v1(git 历史可溯)。
> 依据:方向锚(CLAUDE 2026-09-02)+ 理论日全部产出(七算子审计/判据库框架/Aegis 过秤/
> 仲裁栈图纸/几何快仲裁)+ flywheel 三函实证。
> 下游详细件:[仲裁栈图纸](2026-09-07-arbitration-stack-design.md) ·
> [VerifyPack 立项](2026-09-07-verifypack-v02.md) ·
> [头脑风暴正本](2026-09-07-verifypack-mvp-brainstorm.md) ·
> [position paper v2 素材](../marketing/position_paper_v2_materials.md)。
> 与 GOAL_SSOT 关系:GOAL 管目标执法,本文管方向设计;冲突 GOOL 优先。
> 标注:fact_status ∈ {measured, inferred, heard}。

## 0. 一句话与总览矩阵

**Aegis arbitrates what agents do; compass arbitrates what agents remember —
and what their data is worth**(measured:Aegis $20/mo;inferred:记忆/数据仲裁空位)。

| 维度 | 现在(9/7) | Phase 1(9 月) | Phase 2(Q4) | Phase 3(2026H1) |
|---|---|---|---|---|
| **①算子端** | 写●/读◐/选●/合并◐/忘◐/组合○/评估◐ | 写入门(fact_status)+查重合并+沿链(#48) | 合并=冲突消解仲裁·忘=共识衰减·几何快仲裁 | 组合=推导入链·provenance 召回 |
| **②理论架构** | 仲裁栈五层+L0.5 蓝图 | 判据语言形式化启动 | 概率终局性理论·「忘=共识」形式化·paper3 素材 | paper3 元理论(双速异构验证定理)·2027 双假设裁决 |
| **③工具链** | daemon/MCP/PyPI 3.1.2/评测 harness/四探针 | VerifyPack CLI(#47)+RSI 环 runner | 回执哈希链·conformal 校准器·判据库管理 | 声誉账本·多验证方注册 |
| **④应用生态** | 自家四框+workbuddy | flywheel batch001 跑通 | 首个数据结算场景采信 | **外部第一采信(分水岭)**→验证方网络 |

## 1. 算子端:七算子到全●的路线

现状过秤(v1 审计):写● 读◐ 选● 合并◐ 忘◐ 组合○ 评估◐。

| 算子 | 终态定义 | 路径 |
|---|---|---|
| 写 | 写即声明:fact_status+claims 入包 | #48(9/15) |
| 读 | provenance 召回:可验回执的记忆优先 | Phase 3 |
| 选 | 双速门控:几何 TLB(99%)+复算终审(1%) | L0.5 Phase 2 |
| 合并 | 冲突消解仲裁:验证历史×新鲜度×fact_status 排序 | Phase 2 |
| 忘 | 共识函数:decay=被复算支撑度(记忆 PoS) | Phase 2(schema 已有 decay_rate,measured) |
| 组合 | 推导入链,产物可审计;实体底座=符号图候选 | Phase 3 |
| 评估 | 判分卫生学=概率世界共识协议 | 论文级(paper2 提交中) |

## 2. 理论架构:四件待形式化 + 一个裁决

- L1 判据语言(可执行可复算+口径+置信带)→ Phase 1 启动文档化;
- 概率判定终局性(几次复算收敛/冲突回执)→ Phase 2 前定(图纸 §5);
- 「忘=共识函数」形式化(置信场)→ Phase 2;
- paper3 元理论:双速异构验证定理(同构快→盲区,异构慢→正确,互补为必然)→ Phase 3,
  素材已集(本日讨论+几何仲裁推演);
- 2027-12-31 双假设裁决(分层晋升 vs 蒸馏即记忆,判据已预注册于素材池 §8)。

## 3. 工具链:仲裁栈每层配一个工具

| 栈层 | 工具 | 状态 |
|---|---|---|
| L0 原语 | VerifyPack CLI(build/verify/receipt/check) | #47 |
| L0.5 几何 TLB | drift(在产)+conformal 校准器 | 校准器 Phase 2 |
| L1 判据 | 判据库管理(CRUD/版本/复算历史 ledger) | Phase 2 |
| L2 验证方 | RSI 环 runner(预注册→回归→复算→合入) | #48 首跑 |
| L3 回执链 | 哈希链服务 | Phase 2 |
| L4 结算声誉 | 声誉账本(接 B 理论 ledger) | Phase 3 |
| 基建 | daemon watchdog(9/7 三死教训)·旧入口退役 | 9/15 |

## 4. 应用生态:从四框到网络

- **数据方**(flywheel):batch001=首个真实包;200 条批次+掌形三元组定标(Q4);
- **训练消费方**(V5):verified 标签进数据选择(头脑风暴 Q6);
- **平台**(nautilus-core):验证任务类型+多验证方基建(Q3/Q5);
- **coding agents 终端用户**:9/8 发布起,开源信任资产飞轮(成绩/判分卫生/负结果公开);
- 里程碑:自家四框(now,measured)→ 首个外部采信(**分水岭**,可测=外部团队跑
  verify/check 并采信回执)→ 多验证方网络(2027)。
- **反脆弱红线**:判据库持续接外部锚;自家人验证自家人≠外部信任;不做动作门/代币化/
  完全去中心化;对外叙事只说 PKI 式信任最小化。

## 5. 统一时间轴(与 GOAL_SSOT 并轨)

| 时点 | 事件 |
|---|---|
| 9/8 21:00 | 主发布(信任资产广播开始) |
| 9/9-9/10 | #46 复算 · 头脑风暴回收(9/10 22:00) |
| 9/10 | position paper v2(dev.to+博客) |
| 9/15 | #48 RSI 首环(三件套+退役+watchdog) |
| 9 月内 | #47 VerifyPack v0.2(batch001 端到端) |
| Q4 | Phase 2 全线(判据语言/回执链/合并忘共识化/数据结算/T1 造题/中文圈②层) |
| 2026H1 | Phase 3(外部验证方/声誉/组合/系统论文 10 月线) |
| 2027-12-31 | 双假设裁决(理论预测力审判) |
