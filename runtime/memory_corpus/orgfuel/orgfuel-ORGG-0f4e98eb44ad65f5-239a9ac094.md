---
name: orgfuel-ORGG-0f4e98eb44ad65f5-239a9ac094
description: "判读档判例 PRECOR_JUDGE_ROBUST_20261006 · 实验 C:软维度双跑一致性(ER 门 v2 数"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-0f4e98eb44ad65f5
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 PRECOR_JUDGE_ROBUST_20261006 · 实验 C:软维度双跑一致性(ER 门 v2 数值依据)
## 实验 C:软维度双跑一致性(ER 门 v2 数值依据)

- **设计**:同题重复判 k=5 × 解码 {greedy, T=0.3} = 两轨;逐题测软维度(置信/严重度等连续档)与主维度(label)的自一致率。
- **读数**:①主维度自一致率(预期 greedy≈100%)②软维度相邻档一致率(|Δ|≤1 档占比)与逐档一致率 ③轨间对比。
- **判门(冻结)**:不设通过门——本实验目的=**实测出软维度复现率上限**,ER 门 v2 的软维度单列门数值=实测 greedy 自一致率 −2pp(封顶 97%),由判据修订序(预注册 v2)另行冻结;本实验只产数不定门。
- **产出**:ER v2 提案数值依据+caliber-bench(元基准)首批自评用例。
