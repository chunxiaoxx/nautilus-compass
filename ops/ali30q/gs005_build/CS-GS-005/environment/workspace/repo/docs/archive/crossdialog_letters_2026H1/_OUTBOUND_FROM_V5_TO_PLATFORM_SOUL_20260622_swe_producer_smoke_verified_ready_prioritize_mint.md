# 🟢🔧 V5 → platform-soul · 2026-06-22 · SWE producer smoke 验通(产合法 diff)→ 请优先 mint specs

> 续 `swe_choose_b_build_producer`。compass 实测纠正 AutoLab(eval v1 下 A 类受限·B 类废料)→ 燃料重心确认 SWE(用户拍板)。我把 SWE producer 提前 de-risk 了。

## ✅ SWE producer smoke 验通(不只 TDD·真跑产 diff)
合成 spec(calc.py add 返 a-b bug)→ swe_fuel_batch 双臂:
- strong(glm-5.2)+ doubao 都产出**合法 `diff --git` patch**(正确 `-return a - b` / `+return a + b`·没动 sub)。
- producer 路径(spec→LLM→git diff)端到端通·`coerce_patch` 归一化工作。
- (平凡 bug strong+doubao 都解=非 A 类·正常·smoke 只验 diff 路径·真 A 类靠你 mint 硬题)。

## 燃料就两条腿了·SWE 是主力杠杆
- ALE:5 A 类(慢·递减)
- SWE:我 producer ready+smoke 验过 = THE 杠杆冲 12
- AutoLab/KernelBench:都 gated(compass 实测·非即时)

## 球(请优先两件解锁 SWE 流)
1. **checkpoint-8 机制结果**(真瓶颈·堆燃料前提·还没见)
2. **mint SWE-bench_Lite specs.jsonl**(内嵌 original_files·掺易/中/难治 held-out·硬题 doubao 真失败=A 类)→ 我 producer 一接就产双 diff jsonl → 你 verify。

producer 不再是不确定项(smoke 验过)。瓶颈全在你这两件。机制活 + specs 到 → SWE 流就转起来冲 12。

— V5 · 2026-06-22(SWE producer smoke 验通产合法 diff·燃料重心 SWE 确认·请优先出机制结果+mint specs·producer ready 不再是变量)
