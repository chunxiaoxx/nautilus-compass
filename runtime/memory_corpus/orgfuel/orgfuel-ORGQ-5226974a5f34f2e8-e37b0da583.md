---
name: orgfuel-ORGQ-5226974a5f34f2e8-e37b0da583
description: "轮次记录 R435 · 2026-10-09 晚二(用户令·T5 recall 节流重做✅[实测三连]——TDD 12绿"
metadata:
  type: reference
  source: org_fuel:queue
  pf_id: ORGQ-5226974a5f34f2e8
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

轮次记录 R435 · 2026-10-09 晚二(用户令·T5 recall 节流重做✅[实测三连]——TDD 12绿+生产 hook 链三态验证+失效 WIP stash 清账)
### R435 · 2026-10-09 晚二(用户令·T5 recall 节流重做✅[实测三连]——TDD 12绿+生产 hook 链三态验证+失效 WIP stash 清账)
- **主件=T5 recall 注入节流(R432 重做方案落地)**:节流闸最前置 main()——窗口内**零输出直接 return**(不捕获/不重定向 stdout,R432 转义地狱根因规避);session_id(.stdin JSON)为键,默认 10min 窗,`COMPASS_THROTTLE_MIN` 可调(0=关);fail-open(无 session_id/状态损坏/闸异常→一律放行注入,节流器绝不成为注入单点);状态文件 `~/.cache/compass_hook_throttle/<sid>.json`+TTL 48h 顺手清。
- **stdin 单读缓存**:新增 `_read_stdin_json_cached()`,main 闸与 `read_user_prompt_from_stdin()` 共享同一次 read(stdin 流读一次即耗尽,不缓存则闸先读后 main 拿空)。
- **TDD[实测]**:tests/test_recall_throttle.py 12 用例先 RED(12 failed)→实现→**GREEN 12 passed**;全量回归相关 31 passed(收集 12 error=mcp_durable 缺失既有已知,非本次引入)。
- **生产链三连[实测]**:hook.sh 模拟 stdin(session_id=throttle-sm
