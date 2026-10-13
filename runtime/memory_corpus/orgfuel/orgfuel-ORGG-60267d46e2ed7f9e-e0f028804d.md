---
name: orgfuel-ORGG-60267d46e2ed7f9e-e0f028804d
description: "判读档判例 NACRE_NATIVIZATION_ROADMAP_V0_20261007 · 二、原生 RSI 自进化:"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-60267d46e2ed7f9e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 NACRE_NATIVIZATION_ROADMAP_V0_20261007 · 二、原生 RSI 自进化:"双模型互锁"(反自指的工程化)
## 二、原生 RSI 自进化:"双模型互锁"(反自指的工程化)

- **创新机制**:自训自进化的最大风险=自指漂移(自己教自己越教越偏)。我们的护栏差异化:**NACRE-exec(被训方)与 NACRE-judge(裁判方)分离互锁**——exec 的每次自进化批次,必须过 judge 按冻结判例锚(frozen anchor)的验证;judge 自身只允许从外部勘误(判例集)更新,不允许从 exec 的输出更新。
- **为什么是我们**:互锁需要两侧都是可信部件(judge 可复算+判例 registry 防篡改);单模型自进化(MemRL 类)没有这种结构性护栏。
- **实验设计(E-NACRE-2)**:v5 蒸馏小模型(exec)用涡轮增压自训两轮;每轮后由 judge 判读同一 held-out 集——judge 判定与 ground truth 的一致率不降 = 互锁有效;exec 的任务成功率提升 = 自进化有效。两门同过才算。
