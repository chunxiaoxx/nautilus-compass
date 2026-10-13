---
name: orgfuel-ORGQ-R280-fca2d4f1e2
description: "### R280 · 2026-10-07 早(loop v2 R4:B/C 正式发车✅) - **PRECOR B/C"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R280
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R280 · 2026-10-07 早(loop v2 R4:B/C 正式发车✅)
- **PRECOR B/C 上 A100 实跑[实测]**:两障碍连破——①modelscope 目录结构(config 在 snapshots/master/,顶层无 config→Unrecognized model)②共享实例实锤(venv_groot 的 _staff_batch100_inset.py 占 16.6G 跑 11h——A100 非独占,1.7B 4.5G 共存无冲突)。进程 3816420 活,bf16-greedy 150/291 acc≈0.86(>模板自验证门 0.80,向生产 0.885 收敛中),GPU 21.1G 共存。预计 1-1.5h 跑完 9 轨(bf16/fp16/int8/int4×greedy+bf16-T0.3),收数=matrix.csv+一致率矩阵(判门 0.99 预注册)。
- 发车路径复盘:上传脚本坑(heredoc 反斜杠/import os 漏/SSH 间歇拒绝)=退避重试+文件化脚本解决;**shared GPU 事实记档**(排期计划须虑及他框任务共存)。
- 下轮:run.log 巡检收数→按 PRECOR 判门出 verdict→回函 v5/platform。
