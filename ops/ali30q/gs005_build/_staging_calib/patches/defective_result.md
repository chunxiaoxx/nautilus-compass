# defective_result · CS-GS-005(2026-10-29 实测)

- 预期: 方向对但不完整的答卷 —— 初始化面 GP-1/GP-4 齐(结构化报告+degraded+后端如实),消费侧 GP-2/GP-3 缺(裸调+吞,返回 None,零计数)
- 实测: 16 passed / 5 failed in 0.03s(compass .venv python / pytest 9.1.1)[实测]
- patch: 坑版基线 · git apply --check + apply PASS [实测]
- 挂点清单(与缺漏点一一对应,全部消费侧语义): UT-2 / UT-13 / UT-14 / UT-15 / UT-21
- 判读语义: 初始化降级可见但消费期降级静默如故 = 半对卷,不得给满分
