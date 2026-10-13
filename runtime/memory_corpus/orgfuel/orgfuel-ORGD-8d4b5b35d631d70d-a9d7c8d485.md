---
name: orgfuel-ORGD-8d4b5b35d631d70d-a9d7c8d485
description: "[### Task 6: 端到端验证] | Hook | 真跑结果 | 期望 | |---|---|---| | com"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-8d4b5b35d631d70d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[### Task 6: 端到端验证] | Hook | 真跑结果 | 期望 |
|---|---|---|
| compass_session_start.py (cwd=compass) | exit=0 + 6 alert | ✅ |
| compass_session_start.py (cwd=v5) | exit=1 + FAIL | ✅ |
| compass_post_tool.py (写 compass) | exit=0 | ✅ |
| compass_post_tool.py (写 v5) | exit=1 | ✅ |
| compass_post_tool.py (冒充 OUTBOUND) | exit=1 | ✅ |
| path_b_session_audit.py (session memory check) | 输出含 OK/WARN | ✅ |
