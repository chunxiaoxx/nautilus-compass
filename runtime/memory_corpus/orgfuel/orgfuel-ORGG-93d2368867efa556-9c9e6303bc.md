---
name: orgfuel-ORGG-93d2368867efa556-9c9e6303bc
description: "判读档判例 2026-06-22-kernelbench-score-fuel-adapter-design · 3. "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-93d2368867efa556
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-22-kernelbench-score-fuel-adapter-design · 3. 方案(turf-clean · 复用不重造 · anchor #5)
## 3. 方案(turf-clean · 复用不重造 · anchor #5)
| 谁 | 干什么 | 复用 |
|---|---|---|
| **compass**(env/eval/格式 turf) | 建 6-key 适配器 `kb_fuel.py` + 跑现有 harness 验强解 | stump 技能工具链 + V5 6-key 契约 + attention 已验强解 |
| **V5**(producer turf) | 在 ALE/SWE 同管线跑 Opus 强解 + doubao 难度,经 compass harness | 它的 producer + ARK completer + GPU 调度 |

### 组件:`kb_fuel.py`(compass repo · 镜像 `ale_fuel_batch.py` 结构)
- **纯函数 `build_kb_fuel_sample(task_id, problem_statement, strong_result, doubao_result) -> dict`**:发出 6-key(+score_type="maximize")。映射:`strong_score`=强解 harness 加速比·`doubao_score`=doubao best 加速比(失败/不过正确性门=0)·`strong_verified`=强解过正确性+速度门。**逐键匹配 V5 契约**(下游 ingest 零改)。
- **A 类判定**:复用 V5 `is_a_class` 语义(strong_verified ∧ strong
