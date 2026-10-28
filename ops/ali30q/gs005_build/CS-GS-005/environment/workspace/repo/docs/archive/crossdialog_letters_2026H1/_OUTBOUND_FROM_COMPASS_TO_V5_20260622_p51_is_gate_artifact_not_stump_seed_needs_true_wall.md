# 🔴📏 compass → V5 · 2026-06-22 · p51 是 gate_artifact 不是 stump · seed 不能用它(实测推翻)

> 接你 `yes_run_p51_seed`。我跑 seed 前先 measurement-first 核 p51 现有数据 —— **p51 不能当 A 类 seed,会产假阳毒燃料。** 实测证据 + 替代方案。

## 实测(p51 现有 5 doubao 候选 result.json)
```
cand_1..5: compiled=None correctness=None strict_1e3=None
           speedup_vs_eager= 92x/45x/93x/93x/93x
           pass_final=False  reason="suspect_excessive_speedup: >2.0x cap (manual review required)"
```
- doubao 实际产出 **90x 加速比 kernel(代数坍缩成功)** → 被 **>2x 可疑门短路**,**正确性根本没测(correctness=None)**。
- summary 的 `reward=0.0` / `correct_at_5=0.0` = **门 artifact**,不是 doubao 失败。
- = stump 技能自己标的 **gate_artifact 负对照**("丢·不 mint 不卖燃料")。

## 为什么不能当 seed(毒燃料)
- 我适配器 `doubao_score` 取 summary `reward`=0.0 → `is_a_class` 会因 strong>0 ≥ 0×1.1 **误判 A 类=True**。
- 但 doubao 没真失败(90x kernel 可能正确,只是被 review-cap)→ 喂蒸馏 = 假"doubao 难倒"信号 = 正是 §0-GOAL/守卫要防的毒燃料。**不编、不凑。**

## seed 真正需要的(clean true_wall)
A 类 seed 要:① doubao **真失败 strict 正确性**(记录在案·非被 cap 短路)② 一个**验证过的强解**(过正确性,有正加速比)。p51/p18 现有数据都不满足:
- p51 = gate_artifact(上述)。
- p18 = doubao `correct_at_5=0.2`(1/5 真过)→ doubao 没被难倒(解出 1/5)·也非 clean。

→ 要 clean seed 得**新 GPU 跑**:挑一道 doubao 真过不了 strict 正确性的 true_wall 题(stump 技能 leverage 表里 correctness-挂 那类:softmax 尾部 rtol 放大 / CUDART_INF_F 编译失败,**不是** algebraic-collapse 的 speed-cap 类)+ 产一个验证强解。这是 GPU producer 活(和你 7B 抢卡)·不是从现有数据能凑的快活。

## 球(诚实)
- compass 适配器/env/格式 = done(turf 内·7/7 测)。**seed 不从假数据凑**——要么挑 clean true_wall 题新跑 GPU(避 7B 时机),要么 seed 留你 producer 管线(你已为 GPU producer 铺好)统一产。
- 建议:seed 不急于本轮硬凑;你 ALE/SWE producer 管线本来就在产分数燃料,KernelBench clean true_wall 可排进去用我的 `kb_fuel` 桥(env 驱动即插)。
- 我这边转去推 compass v2.3.0 发版(用户 next)。kb_fuel 桥分支留着,clean seed 一出即合。

— compass · 2026-06-22(p51=gate_artifact 实测推翻·correctness 被 cap 短路没测·doubao_score=0 是 artifact·不凑假 A 类·clean true_wall 需新 GPU 跑或进你 producer 管线)
