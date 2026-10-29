# equivalent_result · CS-GS-005(2026-10-29 实测)

- 预期: 功能等价实现(实现路径与金标不同),全部UT通过,整题=1
- 实测: 21 passed in 0.02s(compass .venv python / pytest 9.1.1 / 21 UT)[实测]
- patch: 坑版基线 · git apply --check + apply PASS [实测]
- 与金标路径差异(等价性声明):
  · 降级账 = 事件列表 `_degradation_events` 逐条追加,count/report 由 property 动态派生(count=len(events)、report=最新一条)——金标为独立计数器 + 单报告覆盖
  · 降级登记 = 模块级函数 `register_degradation()`,非宿主私有方法 `_mark_degraded()`
  · 降级 outcome 经工厂函数 `outcome_unsealed()` 构造;后端标记走模块常量 BACKEND_PG/BACKEND_FILE
- 可观测语义四点(GP-1~GP-4)与金标逐一相同: 结构化报告/degraded 标志/降级计数贯穿/后端如实标记
