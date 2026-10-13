---
name: orgfuel-ORGM-bd2e0ac31e98eafc-9fb68aff7a
description: "记忆条目 cloud-daemon-storm-rootfix-20261006.md 2026-10-06 晚 R26"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-bd2e0ac31e98eafc
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 cloud-daemon-storm-rootfix-20261006.md
2026-10-06 晚 R263(commit 4beaf3ca):probe 第六源骤升 +217/轮,py-spy 取证翻案 [[dogfood-and-e1-recheck-20261006]] 里 R256 的"socket 泄漏"诊断——**误诊**。

**真根因(无用功风暴)**:CPU 跑 bge-m3 前向慢(单请求 30s+)× 客户端超时重试风暴 → 32 inflight 槽全被"客户端已 FIN、daemon 还在白算"的僵尸请求占满 → accept 全 overload reject → 排队连接 CLOSE-WAIT 稳态堆积。**判别证据**:worker 线程全闲时 CLOSE-WAIT 28 个(若泄漏应有卡死线程)、单线程烧 99.7% CPU 3.5h、log 3h 无一请求完成。CLOSE-WAIT 堆积≠close 缺失,handler 从未被调度到。

**修复(daemon_v33.py v3.3.3,备份 .bak_20261006_r263)**:A) `_safe_handle` 开工前 `recv(1, MSG_PEEK)`——返回 b''(对端已 FIN)直接 return 跳过计算,finally 照常 close+release sem;B) chunk fusion cosine 数组 guard。验收[实测]:overload 计数 195369 停涨、P9 cache 请求恢复、CLOSE-WAIT 28→16。

**Why**:R256 只看了 CLOSE-WAIT 堆积表象就贴"泄漏"标签;py-spy 现场栈一抓便翻案——线程状态+log 时间线比 socket 计数更接近因果。

**How to appl
