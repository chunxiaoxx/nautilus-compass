---
name: orgfuel-ORGM-f9316bd73453fe29-0b06af910b
description: "记忆条目 t5-recall-throttle-live-20261009.md T5 recall UserPromp"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-f9316bd73453fe29
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 t5-recall-throttle-live-20261009.md
T5 recall UserPromptSubmit 注入节流 2026-10-09 落地（R432 深夜止损后的日间重做，用户令"现在做·带测试"）。

**方案要点（与 R432 失败 WIP 的本质区别）**：节流闸最前置 `main()`，窗口内**零输出直接 `return 0`**（=Claude Code 无注入）——不做 stdout 捕获/重定向，R432 转义地狱（heredoc+repr+真换行三重）的根因整体规避。

**Why:** R432 试图捕获 stdout 判断注入内容，被 recall.py 多点 early return 打爆；不捕获就没有转义问题。

**How to apply:**
- 坐标：plugin 仓 `~/.claude/plugins/nautilus-compass/recall.py`（feat/memory-gate-trio 分支）· 测试 `tests/test_recall_throttle.py`（12 用例）
- 参数：`COMPASS_THROTTLE_MIN`（分钟，默认 10，0=禁用）；状态文件 `~/.cache/compass_hook_throttle/<sid>.json`（TTL 48h 自清）
- **stdin 单读陷阱**：stdin 流读一次即耗尽——main 闸与 `read_user_prompt_from_stdin()` 必须共享 `_read_stdin_json_cached()`，否则闸先读后 main 拿空
- fail-open 纪律：无 session_id/状态损坏/闸异常→一律放行注入，节流器绝不成为注入单点
- 行为变更：同 session 10min 内后续消息只见单
