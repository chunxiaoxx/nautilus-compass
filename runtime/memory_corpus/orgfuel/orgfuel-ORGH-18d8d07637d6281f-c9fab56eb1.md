---
name: orgfuel-ORGH-18d8d07637d6281f-c9fab56eb1
description: "commit ab19935739bc 2026-08-24 fix(daemon): v3.0.3 per-proje"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-18d8d07637d6281f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit ab19935739bc 2026-08-24
fix(daemon): v3.0.3 per-project 锁串行化 embed/flush——根因=并发 setdefault 竞态(两线程各持 cache dict,后写 flush 用稀疏 pkl 覆盖致条目丢失→347% CPU 反复 re-embed;33 次 tmp 同名 ENOENT)。附唯一 tmp 名
Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
