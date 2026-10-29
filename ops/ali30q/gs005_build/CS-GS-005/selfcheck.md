# CS-GS-005 selfcheck 双向预检留证(2026-10-29 · R202 扩条后)

判分解释器: ~/Projects/nautilus-compass/.venv/bin/python(pytest 可用·无 psycopg_pool=坏 DSN 场景走 ImportError 降级)
UT: tests/test_gs005_degradation.py(21 条:targets_badpattern 17 + focus 独立锚 4)
staging 布局 = 容器同构(X/tests + X/workspace/repo,照 task.toml artifacts destination)

| 态 | 构造 | 实跑结果 | 退出码 |
|---|---|---|---|
| Golden(金标) | repo + helix_chain 归位 + 金标 bridge 覆盖 | 21 passed | 0 |
| NOP(坑版原样) | environment 原样(无 helix_chain.py,坑版 bridge) | 21 failed | 1 |

双向留证成立(10/29 R202 轮实测,扩条 3→21 后双向均满幅分叉)。
staging: /tmp/gs005_utexp_pit(轮后可清);复跑命令见缺口档排期与本档表格。
证据副本: gs005_build/_selfcheck_gs005/{golden,pit}(R195 版已清,本轮日志落 selfcheck_*_run.log)。
