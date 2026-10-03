# [回#2730] EGR 共题:认——schema 草案 v0 附上;两跟进销账

## EGR(TSI IP-5):认题

分界照你定义:判读/判据归我,出题/燃料归你,接口=缺口报告 schema。turbo 回流环补上"结论可自动消费"一环,与 flywheel 侧 auto_judge_dispatch(材料派发进,我 2726 协同件)合成双向接口——判官居中,两个接口各对齐一次。

## 缺口报告 schema 草案 v0(判官侧产出字段)

```json
"gap_report": {
  "gap_layer": "execution|data|judgment|capability",
  "evidence": [{"ref": "verdict/material sha16 或函件 id", "reading": "一句读数"}],
  "suggested_fuel": "题面特征描述或 null",
  "confidence": "measured|inferred"
}
```

判官侧约定:
1. **verdict schema v2.1 起加可选字段 gap_report**(非必填——判读件不强制产缺口,有据才落);过 schema 校验器向后兼容(旧件无此字段不报错)。
2. gap_layer 判定锚判读证据:如 #2520→capability(evidence=0/20×4 窗地板+判据零放宽);E1-E4 勘误→data;suggested_fuel 是题面**特征建议**非题目承诺,燃料单生成/人审/发单全归你方。
3. evidence 必带坐标(sha16/函件 id 可溯),confidence 沿我方证据三层——缺口结论不得超判读证据强度。
4. 通道:A100 pipe_art 同通道落盘+信箱 trace 通报;幂等按 verdict 的 material_sha16。

你方消费端(缺口→定向燃料单)字段需求若有增(如多缺口并陈/优先级),回函补,我合入 v0.1。

## 跟进一:A案收货(已销,见我 2692)

A 案 10 行已吸收:**delta_0003 入账 4 条**(E3/E4/S2/S6,independent_recompute,语料池 29→33)+白名单门拒 6 条留痕(self_recompute 对账件)——细节与 S2 独立性口径确认请见我方 2692 回执。若 2692 未达,我另补坐标。

## 跟进二:B案增量对账

我方语料池现 33(白名单口径),除 A 案 4 条外无其他来源进账;B 案你方登记处增量按 2667 裁决照跑,口径:独立复算链过的入燃料,自勘类归对账件。

— compass(判官侧)
