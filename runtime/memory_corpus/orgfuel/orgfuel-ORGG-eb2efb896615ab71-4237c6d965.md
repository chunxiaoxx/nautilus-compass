---
name: orgfuel-ORGG-eb2efb896615ab71-4237c6d965
description: "判读档判例 2026-06-19-stump-gate-design · 背景 / 为什么 ## 背景 / 为什么 用户"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-eb2efb896615ab71
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-19-stump-gate-design · 背景 / 为什么
## 背景 / 为什么
用户问题:**如何持续产出难倒 doubao 的真实经验教训题目?** 6/19 实测两道已建经验题(doubao-seed-2.0-pro·N=5):
- d1(version-key-join·**gotcha 型**):pass@5 = **1.00** → 完全难不倒(清晰 spec 把"该考虑版本维度"说破,强模型照做即过)。
- c2(CJK 编码 round-trip·**IO/correctness 型**):pass@5 = **0.60** → 压线难倒(2/5 候选 byte-exact round-trip 全损)。

**判别器假设(N=2·未证)**:难度住"一句 spec 能说清的事"(gotcha→难不倒)vs"模型须在多用例都执行对的 fiddly 正确性"(IO/编码/数值/并发→难倒)。同 KernelBench(写又快又对 kernel 本质难)。
