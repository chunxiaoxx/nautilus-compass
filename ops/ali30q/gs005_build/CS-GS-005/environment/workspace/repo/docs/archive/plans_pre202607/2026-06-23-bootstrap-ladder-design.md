# 设计 · 自举阶梯(Bootstrap Ladder)· 方向 B 第 2 件 · 2026-06-23

> 方向 B = 把"燃料稀缺墙"变飞轮。第 1 件(迭代强解·V5 建)在**单轮内**提升强模型解出率。本件(自举阶梯)在**跨轮**让蒸馏出的模型反哺成 producer,使燃料率**复利**——这是北极星"系统可证变强→产更难题"循环字面意义上转起来。

## 0. 一句话
distilled-v_n(本轮蒸馏出的模型)加入第 n+1 轮的 **producer 池**;它在"领域特化 > 通用强模型"的题上贡献**新解**→ 新 A 类燃料 → 训 distilled-v_{n+1} → 解出更多 → 循环。

## 1. 🔴 viability gate = held-out 泛化(与首证同一个问题)
**自举能不能复利,等价于 distilled 能不能泛化。**
- distilled-v_n 若只**背**了强模型的解(over-fit),它在**新题**上产不出强模型产不出的东西 → 自举加不了新燃料 → **不复利**。
- distilled-v_n 若**泛化**(held-out 上 distilled>base)→ 它能解新 ALE 题 → 在强模型失败的题上可能成功(领域特化)→ 复利。
- **所以:自举阶梯 gated on 正在跑的 LOO held-out 首证。** 首证 PROVEN → 自举可建;首证 KILLED → 自举不会复利,改走(更多料多样性 / 更大模型 / 轨迹蒸馏)。**不在首证出结果前实现自举**(反 facade)。

## 2. 阶梯机制(每一级 rung)
```
轮 n:
  fuel_pool_n (A 类燃料)
    → 训 distilled-v_n (QLoRA·full pool·非 held-out·full 用料)
  producer_pool_{n+1} = { 强模型(V5·N-turn 迭代), distilled-v_n }
    → 对 strong=0 残余题各 producer 尝试
    → 任一 producer 解出 + doubao 仍败 + 真 judge 验证 = 新 A 类
  fuel_pool_{n+1} = fuel_pool_n ∪ 新 A 类
  → 训 distilled-v_{n+1} ...
```
**关键度量(每 rung 必报)**:`new_A_from_distilled` = distilled-v_n 解出**而强模型(含迭代)解不出**的题数。这是自举**净贡献**——若 ≈0,distilled 没加价值,阶梯无意义。

## 3. 反坍缩护栏(防自举退化成自欺)
自举最大风险 = 模型自产自销、信号通胀。铁律:
1. **doubao 仍败**:distilled 的新解必须 doubao 解不出(否则不是 A 类·is_a_bucket 连续分门已有)。
2. **真 judge 验证**:distilled 的解走同版 ale_eval(judge_version 锁同版)打分·**绝不用 distilled 自评**。
3. **多样性**:producer 池 + 燃料池跨基准(ALE+SWE+KernelBench)·防阶梯过拟合单基准 quirk。
4. **净贡献停机**:某轮 `new_A_from_distilled < K`(如 2)→ 阶梯**平台了**→ 诚实停·不空转刷轮次(反 D·anchor #3)。
5. **基线对照**:每轮留出独立 held-out 测 distilled-v_n vs distilled-v_{n-1} vs base——**外部 benchmark 证每级真变强**(北极星每圈外证铁律)·非只看燃料数涨。

## 4. 与现有机制复用(anchor #5·不重造)
- 训练/eval:`distill_qlora.py` / `distill_eval.py` / `distill_loo.py`(已建)。
- 燃料判定:`distill_fuel.is_a_bucket`(连续分·已支持)。
- producer 接口:distilled-v_n 用 `_distill_runtime.generate_solution`(已对齐 prompt)产解·喂 V5 的 ale_eval 判分——**与强模型 producer 同一判题路径**(可比)。
- 迭代:distilled-v_n 也可跑 V5 的 N-turn 迭代(它也能 turn2>turn1)。

## 5. 实现次序(gated·分阶段)
- **阶段 0(现在·gated on 首证)**:LOO held-out 首证出结果。PROVEN 才进阶段 1。
- **阶段 1(MVP·1 级 rung)**:首证 PROVEN 后,full-pool 训 distilled-v1 → 对 strong=0 残余题跑 distilled-v1 produce(复用 generate_solution + ale_eval)→ 数 `new_A_from_distilled`。**1 级证明净贡献>0** = 自举可行性证。
- **阶段 2(多级 + 自动化)**:净贡献>0 才把阶梯做成循环(`distill_bootstrap.py` driver:train→produce→judge→pool→repeat·带停机护栏)。**不在阶段 1 证明前建 driver**(反提前抽象)。
- **阶段 3(接 agent 自治)**:distilled-v_n 注册成真 agent(agent_first_register·北极星 §0-ARCH)·producer 池=注册 agent 群·survival/capability 挂上——内飞轮(模型变强)接外飞轮(agent 自治)。这是两套基底真耦合(平台史最大未闭缝)。

## 6. 诚实判据(防自欺)
- 自举**成立** = 存在 rung 使 `new_A_from_distilled > 0` 且 distilled-v_n 在独立 held-out 上 > base。
- 自举**证伪** = 任何 rung distilled 都加不了新解 / held-out 不涨 → distilled 只会背不会创 → 老实退回"靠强模型 + 多基准扩料"·不硬撑阶梯叙事。
- 元教训(北极星):**别把"燃料数涨"当"系统变强"**——必须外部 benchmark 每级证。数字涨而 benchmark 不涨 = facade。

## 7. 球
- **soul**:首证 PROVEN → 实现阶段 1(distilled-v1 produce strong=0 残余 + 数净贡献)。
- **V5**:N-turn 迭代救 26 道 strong=0(扩 fuel_pool + 是阶梯轮 1 的强模型 producer)。
- **compass**:KernelBench A 类(多样性护栏 #3)。

关联 [[project_north_star_one_loop_distillation_forcing_function_20260622]] · [[session_20260623_overfit_PROVEN_mechanism_alive_direction_B_LOO]]
