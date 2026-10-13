---
name: orgfuel-ORGQ-R196-bea40b12ea
description: "### R196 · 2026-10-05 20:0x-20:2x(值守轮:B 臂收官卡死手动兜底+双臂 preds 定"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R196
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R196 · 2026-10-05 20:0x-20:2x(值守轮:B 臂收官卡死手动兜底+双臂 preds 定版+B 评测排队)
- **时间修正**:probe 19:32 打脸 R195 的"20:00 探点已执行"——那是提前探;**本轮 20:00 后正点补探 [实测]:staging/f076-f100 仍未到**,10/6 上午再探,仍缺才 U 态顺延通报(承诺口径)
- **B 臂收官卡死 [实测]**:task_29 trajectory 落盘后 30min+ 无 result.json(无 git 子进程,卡 agent.run 收尾层);处置=**手动兜底**:worktrees/l3r1b_29 手动 git diff 采集=**零改动(0 字节 patch,与 runner 将采口径一致)**→补 result.json(status=manual_collect_after_runner_stall 如实标)→精确 PID 杀僵死 runner(27016/22728);**判分链零等**
- **双臂 preds 定版 [实测]**:A 30 题 patch 非空 28(notes 0);B 30 题 patch 非空 **21**(notes 2:django-11490 runner_error+task_29 stall 兜底);instance_id 对齐 30/30
- **B 评测排队 [实测]**:sftp preds_arm_b.json+wait_and_run_b.sh(等 A 评测进程退出自动起 b,**串行防镜像超容** 86G);排队进程存活;A 臂评测 rest 批 13/15 ran successfully 0 failed(150s/题,~5min 完批,后接 django 批 14 题)
- M1:+
