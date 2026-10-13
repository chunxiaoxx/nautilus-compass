---
name: orgfuel-ORGH-b4f4da2132c327a5-fe1026ecca
description: "commit aae3ea003d12 2026-06-23 feat(drift): no-progress loop"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-b4f4da2132c327a5
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit aae3ea003d12 2026-06-23
feat(drift): no-progress loop detector (Phase2 Task2.1 · B3)
本 session 亲踩 15 次'idle gated'空转 → 把 feedback_loop_self_check passive memory 变 active 机制。
近 window 轮输出归一化后全等且无新 tool 调用 → stuck + surface hint'该停/问用户'。
纯字符串算术·永不抛·同构 metamemory'无可靠 evidence'。5 tests green。
激活步(注): 需 Stop hook 把近期输出写 state 文件供 detector 读(history 源)·后续 wire。
