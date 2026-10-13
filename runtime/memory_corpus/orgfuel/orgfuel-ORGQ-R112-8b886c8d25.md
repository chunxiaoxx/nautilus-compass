---
name: orgfuel-ORGQ-R112-8b886c8d25
description: "### R112 · 2026-10-04 14:2x-14:4x(gen4_v2 B 轨判读轮·EGR 回流首闭环交卷"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R112
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R112 · 2026-10-04 14:2x-14:4x(gen4_v2 B 轨判读轮·EGR 回流首闭环交卷)
- **#2905 gen4_v2 B 轨送判→判读交卷**(响应<1h 惯例):材料验签五件(lock 82b3cef1/report 37f71237/事故卷 88943387/两 log 实例侧取证 ad1b0bce+ddbbd85d——**commit 7e05d2c 仓树内缺席,函坐标失实如实记**);log 逐条计数复算零偏差(49/50+52/60,48/50+34/60);金标交叉 60/60(**首验假绿已纠:eval_set 无 id 字段,改行序对齐**);盲探 3/3 与 0/3
- **关键发现**:多数类基线 0.7833(材料方未报)——正卷增益 p=0.0739 不显著,Wilson CI=[0.7583,0.9309] 覆盖基线,60 对弱标集判别力不可终判
- **verdict=PARTIAL(schema v2.1 compliant)**,三件裁决:①J1b 初步通过成立(零放宽+caveat 实质化)②H2 主因定谳(同数据对照 0.04→0.8667,gap 排序修正)③A 轨暂不发车(建议顺序=判例→人工金标抽检 20-50 例接判官市场→粒度阶梯新案);step500 事故卷正面记档(material_side_honesty 同型)
- **verdict 修正五处**(首版三违 schema):material 内 str 项(repo/coverage_note)挪段/claims 改 dict 结构/gap_layer "evaluation"→"data"(枚举外不私扩,评测集归材料数据)/verdict.text 含"显著"补 statistics 段/PASS-PRELIMINARY→PA
