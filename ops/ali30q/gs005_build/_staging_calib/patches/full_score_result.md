# full_score_result · CS-GS-005(2026-10-29 实测)

- 预期: 全部UT通过,整题=1
- 实测: 21 passed in 0.04s(compass .venv python / pytest 9.1.1 / 21 UT)[实测]
- patch: 坑版基线 · git apply --check + apply PASS [实测]
- 构成: GP-1~GP-4(v5_bridge/helix_bridge.py 降级显式化)+ GP-5(packages/nautilus_core/helix_chain.py 缺失件归位 = defb148 真实修复原件)
- 判分环境口径: venv 无 psycopg_pool → ImportError 降级路径(R202 定谳与 staging 同构)
