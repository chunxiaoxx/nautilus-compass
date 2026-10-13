---
name: orgfuel-ORGQ-R181-846fba59c1
description: "### R181 · 2026-10-05 14:4x-15:0x(用户拍板执行轮:L3 正榜开跑) - **拍板**:"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R181
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R181 · 2026-10-05 14:4x-15:0x(用户拍板执行轮:L3 正榜开跑)
- **拍板**:max_steps 双臂同步放宽到 50,正榜开跑
- **判据演进落档**:L3 预注册档配置差裁定第 3 条改 50(演进程序:开跑前+记档+开跑后不得再动);A 臂参数化走 v5 仓 `f1921b66`(`--max-steps` 默认 25 保持 4e14a898 行为,harness 本体零改动);B 臂 b_runner_r1.py(step_limit=50+wall 3600s 披露项)
- **题源重抽**:heldout30 分布偏(astropy19+django11)→Verified 500 实测分布(12 repo)分层最大余数法抽 30,seed=20261005;配额 django14/sympy5/sphinx3/matplotlib2/sklearn2/astropy·xarray·pylint·pytest 各1/seaborn·flask·requests 0(全库≤8 题,如实披露);pyarrow 显式类型+回读验证(smoke 坑不复犯);产物 _r181_board30/{board30.parquet,tasks.json,board30_meta.json}
- **双臂开跑**(14:55 并行后台,单进程校验过,B 臂"双进程"=venv launcher 父子非双开):A 臂 tag=l3r1a(held_out=true),B 臂 worktree 前缀 l3r1b,输出 _r181_board30/{arm_a_run.log,arm_b_run.log,board_b/}
- **知会函 5725**→platform(max_steps50 演进+题源重抽+n=30 起步+护栏放宽披露)

