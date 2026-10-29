# guessed_result · CS-GS-005(2026-10-29 实测)

- 预期: 方向性错误答卷 —— 病根误诊为「缺重试」(加 3 轮重试循环+attempts 计数),chain_backend 恒标 "pg"(与 GP-4 背道而驰),无结构化报告/degraded/降级计数,无 DSN 场景提前静默返回
- 实测: 21 failed in 0.05s(compass .venv python / pytest 9.1.1)[实测]
- patch: 坑版基线 · git apply --check + apply PASS [实测]
- 备注: UT-1 首断言(日志痕迹>0)可通过("retry exhausted" 日志含 helix 字样),后续结构化断言全挂 —— 猜卷仅有散日志、无任何机器可读降级语义
- 判读语义: 四点题眼(GP-1~GP-4)全数未命中 = 整题 0
