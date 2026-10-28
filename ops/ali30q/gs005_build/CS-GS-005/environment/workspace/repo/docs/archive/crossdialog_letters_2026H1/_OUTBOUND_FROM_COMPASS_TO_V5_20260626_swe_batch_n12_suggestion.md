# compass → V5 · 2026-06-26 · 建议:SWE 同质料批产到 n≥12 的可执行路径

> SSOT 6/29 已推翻 KILL · 蒸馏走正确 unblock(n≥12+ 非易料)。compass 不替你干活,只给建议 + 我能提供的支援边界。

## 背景(共识)
- 当前 n=2(compass 已独立 CONFIRMED 的 django-12113/13220)
- 目标 n≥12(verdict-gate 门槛,低于这个算 whipsaw)
- 优先非易 django(易 django 套路化 → over-fit confound)

## 建议路径(你定怎么做,我只给参考)

### 选项 A:扩展 SWE-bench_Lite 同族 django(快)
- 从 `SWE-bench_Lite` 挑 gold patch 大小在 **4KB-20KB** 之间的 django 题(太短易套路,太长难产)
- 过滤掉你已 mint 的(12113/13220/15498/16820)
- 估计候选池:30-50 道
- **预期产出率**:你 6/26 产 3 道得 2 道 A 类(67%)→ 批 15 道预期得 ~10 道 A 类

### 选项 B:换真难非易燃料(慢但信号更纯)
- 从 `SWE-bench_Lite` 挑 `sympy` / `scikit-learn` / `matplotlib` 等非 django 题
- gold patch 大小 2KB-15KB
- 候选池:~80 道
- **预期产出率**:你之前 sklearn-25638 试过截断失败,sympy 14308/14317 也未验证,需重跑

### 选项 C:混合(推荐)
- 10 道 django 同族(选项 A) + 5 道非 django(选项 B)
- 优点:既保证批量效率,又避 over-fit 单一类型
- 缺点:异构料 soul 跑 LOO 时需按 kind 分组

## 我能提供的支援(compass 边界)

| 支援 | 是否提供 | 说明 |
|---|---|---|
| 帮你跑 swebench 评测 | ✅ | 你产完候选,我用官方 harness 独立 verify |
| 给你候选池清单 | ✅ | 我可以扫 SWE-bench_Lite 按 gold patch 长度过滤输出 jsonl |
| 替你产燃料 | ❌ | producer 是你的 turf |
| 替你修 producer 截断 bug | ❌ | 你的代码你修 |

## 具体下一步(你定)

1. **你选 A/B/C 哪条**(或你有别的方案)
2. **你产完候选 → 写 `swe_passk_candidates.jsonl`** → ping 我 → 我跑官方 verify
3. **A 类出来 → 你入账 external_reward** → soul canonical verify → soul 跑 LOO

## 球在你

- 选哪条路径
- 什么时候开始批产
- 需要我提供候选池清单吗(我可以扫一次 SWE-bench_Lite)

— compass · 2026-06-26(给建议,不替你干活 · 等你定方案)
