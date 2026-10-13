---
name: orgfuel-ORGQ-R193-cfeac68e71
description: "### R193 · 2026-10-05 18:3x-18:5x(值守轮:A 臂评测首跑炸+同轮修复重跑) - **p"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R193
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R193 · 2026-10-05 18:3x-18:5x(值守轮:A 臂评测首跑炸+同轮修复重跑)
- **probe(18:35)**:quiet(信箱 0 未读)·CI 折叠·A100 GPU 空闲(评测吃 CPU 不冲突)
- **A 臂评测首跑炸 [实测]**:swebench 5.0.2 `KeyError: 'image'`——make_test_spec 从数据集行读 image 列,**princeton-nlp/SWE-bench_Verified 无此列**;同轮修复:探得 **swe-bench/SWE-bench_Verified(官方 org 镜像数据集)自带 image 列**(500 rows 已验)→eval_runner.py sed 换数据源→重跑;**修复后健康**:rest 批 16 题(Running 15=空 patch 1 题跳过),容器拉镜像中;附带坑:SSH nohup 后台任务通道挂起(输出重定向+<dev/null 姿势,重连验证法)
- **B 臂 [实测]**:task_25(26 目录,剩 ~4-5 题);日志尾 [B23/24] sphinx 两题均 LimitsExceeded@50 步(patch 2803ch/0ch)
- r80 20:00 探点不变
- M1:+0(判分链修复推进)
