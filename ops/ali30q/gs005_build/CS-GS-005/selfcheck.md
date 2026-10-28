# CS-GS-005 selfcheck 双向预检留证(2026-10-29)

判分解释器: ~/Projects/nautilus-compass/.venv/bin/python(pytest 可用)
UT: tests/test_gs005_degradation.py(3 条,全 targets_badpattern)

| 态 | 构造 | 实跑结果 | 退出码 |
|---|---|---|---|
| Golden(金标) | repo + solution 覆盖(helix_chain 归位 + 金标 bridge) | 3 passed | 0 |
| NOP(坑版原样) | environment 原样(无 helix_chain.py,坑版 bridge) | 3 failed | 1 |

双向留证成立(照 GS-001 selfcheck Golden=1/NOP=0 口径)。复跑命令见 solution/answer.md。
证据副本: gs005_build/_selfcheck_gs005/{golden,pit}(复核后可清)。
