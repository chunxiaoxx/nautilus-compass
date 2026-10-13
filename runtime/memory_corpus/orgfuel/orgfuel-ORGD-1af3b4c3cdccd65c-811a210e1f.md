---
name: orgfuel-ORGD-1af3b4c3cdccd65c-811a210e1f
description: "[## 3. 判据(预注册,四条,与栖达 G0 同构)] | # | 判据 | 阈值(初拟) | 栖达 G0 对应 | "
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-1af3b4c3cdccd65c
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 3. 判据(预注册,四条,与栖达 G0 同构)] | # | 判据 | 阈值(初拟) | 栖达 G0 对应 |
| --- | --- | --- | --- |
| 1 | **意图接续率**:session N 定下的 plan/anchor,在 session N+k 无提示被主动续推的比例 | ≥50% | 判据 1(记忆可感知率) |
| 2 | **自发引用**:agent 主动引用既往决策(非用户提醒)的 turn 占比 | ≥30% | 判据 3(自发提及) |
| 3 | **方向一致性**:跨 session drift_check 对齐分方差低于阈值;漂移须"被记忆照亮"(主动转向,compass 判分器读转向理由),非遗忘(被动漂移) | **compass 评审定标(9/28):连续 3 轮 drift_check 无红灯,且每次红灯转向理由可被判分器复述(可读性二值判)**;方差口径在 drift 历史基线建立后补锚 | drift 监控现役 |
| 4 | **T+7 恢复**:7 天无接触后重新激活,能恢复上下文并继续的比例 | ≥25%(对照:v5 25 天静默=0 分基线实测) | 判据 4(day7 回访) |
