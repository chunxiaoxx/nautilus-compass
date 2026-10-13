---
name: orgfuel-ORGG-4fdd13b6d5913b0f-7787e8f7a1
description: "判读档判例 2026-05-29-compass-comprehensive-uplift-design · 4. 闭环"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-4fdd13b6d5913b0f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-05-29-compass-comprehensive-uplift-design · 4. 闭环 (Closure · 4 gates 测法)
## 4. 闭环 (Closure · 4 gates 测法)

### 4.1 Gate 1 · Self-dogfooding act-on rate 0 → 30%+

**定义**: compass drift / PoI / metamemory event 触发后 · agent (Claude / V5 / 我) 在下个 turn 真接收并改变行为的事件占比。

**测法**:
- ship `.cache/act_on_log.jsonl` · 每个 drift / PoI / metamemory event 一行
- agent 下回合 acknowledge / FP / TP / ignore 各一个 status
- 2 周窗口 · N(events) ≥ 200 · act-on rate (acknowledge + TP) / N ≥ 30%

**Baseline**: 0% (5/27 session 实测)

### 4.2 Gate 2 · Recursive-improvement metric · compass-on vs compass-off ≥ +10pp

**定义**: N=20 受控 task · 同 model 同 prompt · 唯一变量是 compass active 与否 · 任务质量 delta ≥ 10pp。

**测法**:
- 复用 compass-value-study/run_pilot.py 框架 + 加 H 维度 task
- 任务类型 (4 维): 跨 session 一致性 / 提前 catch contradiction
