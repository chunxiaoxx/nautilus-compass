---
name: orgfuel-ORGG-abfb52138c3db2f5-6818833cb9
description: "判读档判例 CASEBOOK_V1 · 卷首 · 判分纪律（适用全部判例） ## 卷首 · 判分纪律（适用全部判例）  "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-abfb52138c3db2f5
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 CASEBOOK_V1 · 卷首 · 判分纪律（适用全部判例）
## 卷首 · 判分纪律（适用全部判例）

1. **证据三层标注**（正本 `docs/metering/JUDGING_EVIDENCE_TIERS_20261003.md`）：每条结论性陈述标注 `[实测]`（材料直读/可复算）、`[推断]`（带 upgrade_path）、`[不可验]` 之一。推断不得冒充实测。
2. **判据零放宽**：判读按预注册判据执行，判不动就报"判不动"，不以任何代理顶替冻结语义，不因结果挑判据。
3. **负结果照报**：PARTIAL / U 态 / 否证一律如实出件。判读叙事跟数字走。
4. **非实现者复算**：判读方与材料实现方分离；自报读数须独立复算后才可引用（本机构对己方判读件同样过 schema 校验+复算）。
5. **独立复验入口**：每判例附材料 sha16 锚定与复算命令；外部读者按坐标可独立复验任意判例。
