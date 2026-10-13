---
name: orgfuel-ORGD-38a84127bfb9c2fd-b6e6dbd5c8
description: "[# _call_tool 的 deny 检查旁加同款(防知名字直调):] - 兼容性:ops/内部 token(tok"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-38a84127bfb9c2fd
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[# _call_tool 的 deny 检查旁加同款(防知名字直调):] - 兼容性:ops/内部 token(tokens.json,admin scope)可见全部 17 个,内部调度零影响;自助/公开 token 只见 8 个用户工具
- 效果:外部 tools/list 17→8;governance_×5/submit_platform_task/proof_of_impact/add_worker/long_task/ingest_platform_task_result 退出公网面
- 部署:scp+restart,probes.py 复跑 + tools/list 计数断言
- 待用户拍板后执行(对外可见行为变更)
