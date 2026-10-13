---
name: orgfuel-ORGG-421a68aeb84df78a-b698fe78c3
description: "判读档判例 2026-09-18-10verdict-recompute · 复算方法(全实测) ## 复算方法(全实测"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-421a68aeb84df78a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-09-18-10verdict-recompute · 复算方法(全实测)
## 复算方法(全实测)

- DB:fde_verdicts 全行(含 items/artifacts/external_verified)、verification_logs、
  audit_log、org_mailbox,SELECT only。
- 独立重跑:cloud 仓 git worktree(detach 到指定 commit,跑毕全部 remove+prune,
  工作树零污染),.venv py3.10/pytest 9.0.3:
  - 7 条 pass 行 → ref fix commit 跑档内 test_id;
  - 3 条 skip 行 → buggy commit 跑档内 test_id(单测+整文件);
  - 另对 7 条 pass 行的 buggy commit 跑同名 test_id 做红灯对照(结果=测试函数缺失,
    rc=4,见探针自证 3)。
- 档-行一致性:DB artifacts 的 turns/total_tokens 与档内逐字段比对,10/10 镜像吻合。
