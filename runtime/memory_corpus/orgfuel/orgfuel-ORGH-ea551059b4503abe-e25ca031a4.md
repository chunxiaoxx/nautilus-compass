---
name: orgfuel-ORGH-ea551059b4503abe-e25ca031a4
description: "commit 26dccb922244 2026-08-23 fix(daemon): pkl 原子写 + 每50 em"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-ea551059b4503abe
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 26dccb922244 2026-08-23
fix(daemon): pkl 原子写 + 每50 embed 周期性落盘——根治云 74MB 损坏 pkl 重嵌入卡死
病根(8/24 云实测):c096d6883da3.pkl 非原子写截断 → warmup 'Ran out of input'
→ 该项目每次重启全量 re-embed → recall 慢 → 消费方重试 → 32 in-flight 满 →
overloaded 活锁。修法:① tmp+os.replace 原子写(3 处)② re-embed 循环内每
COMPASS_PKL_FLUSH_EVERY=50 文件 flush 一次,kill 不再丢进度。

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
