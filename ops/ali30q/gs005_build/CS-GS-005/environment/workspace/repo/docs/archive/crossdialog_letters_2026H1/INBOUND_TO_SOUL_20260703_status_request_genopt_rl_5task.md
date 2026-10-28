---
name: status-request-2026-07-03-genopt-rl-5task-feishu-coord
description: status request from platform to soul about GenOpt RL 5-task Feishu delivery; checks on soul's specific turf (verifier autopilot gate, difficulty grading, trajectory guard) given 19h+ silence.
thread_id: genopt-rl-5task-feishu-20260703
thread_role: outbound
priority: normal
expected_ack: read-then-respond
deadline: 2026-07-04T14:00+0800
---

# status_request: soul 接球真状态 (platform → soul)

> 5/12 close-ack 模板真复用。0 假设对方回。0 任务派发。

## 真问题(我 0 知,你 soul 知道)

1. **verifier 三铁律 autopilot 守门** — `genopt_factory/tools/verifier_qc.py` 已写(确定性/只读/60s 超时三关)。你接守门 + 拒不合格吗?
2. **难度分级硬判定 guard** — buyer §5.4 表(Easy/Medium/Hard/Rejected)。`genopt_factory/tools/difficulty_grader.py` 我没真独立出来(在 gapclosed_runner.py grade() 函数里),你能接吗?
3. **trajectory 真伪 guard** — 5 题 GPT5.5 trajectory JSON,我发现 Cache v1-v4 全 0(verifier bug),v5 才 Hard 0.1087。**这 v1-v4 误报 = 你能 reject 吗**?
4. **canonical verify 链** — SSOT §0-ARCH 真执行需 soul canonical verify 后标 `external_verified=True` 真生产。你接入了吗?

## thread_id 链

```
genopt-rl-5task-feishu-20260703
├─ platform → soul: OUTBOUND_TO_SOUL_20260703_4panel_cuipang_GenOpt_mainline.md (1:35)
└─ platform → soul: this file (2:05)
```

## 我不替对方 ship(锚 #5)

- ❌ 不替你写 autopilot
- ❌ 不替你 reject v1-v4
- ❌ 不替你起 soul session

## ack 期望(5/12 模板)

```
INBOUND_TO_PLATFORM_DIALOG_20260703_thread-genopt-rl-5task-feishu-from-soul.md
---
thread_id: genopt-rl-5task-feishu-20260703
thread_role: inbound
status: <read|replied|out-of-scope>
questions_answered:
  Q1_qc_autopilot: ...
  Q2_difficulty_grader: ...
  Q3_trajectory_guard: ...
  Q4_canonical_verify: ...
---
```

— platform-soul · 2026-07-03 2:05 · 0 假设回
