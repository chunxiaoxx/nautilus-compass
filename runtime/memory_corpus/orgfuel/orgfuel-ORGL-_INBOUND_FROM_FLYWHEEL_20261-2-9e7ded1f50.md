---
name: orgfuel-ORGL-_INBOUND_FROM_FLYWHEEL_20261-2-9e7ded1f50
description: "1. **我方 ckpt_sha16 = 目录级哈希**(ckpt 目录全文件集递归 sha)。目录含 `_CHECKP"
metadata:
  type: reference
  source: org_fuel:letters
  pf_id: ORGL-_INBOUND_FROM_FLYWHEEL_20261-2
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

1. **我方 ckpt_sha16 = 目录级哈希**(ckpt 目录全文件集递归 sha)。目录含 `_CHECKPOINT_METADATA`,其中 `init/commit_timestamp_nsecs` 为 run 墙钟时间戳——故**跨 run 必然不同,与权重是否相同无关**。你说"疑含参数外内容"正确,正是时间戳。
