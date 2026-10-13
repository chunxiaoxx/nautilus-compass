---
name: orgfuel-ORGD-a6b254807944b085-c961aac2ed
description: "[### Task 2: 语料 seed/pull 脚本(CPU 服 ↔ T4)] - `push_corpus(loc"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-a6b254807944b085
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[### Task 2: 语料 seed/pull 脚本(CPU 服 ↔ T4)] - `push_corpus(local_memory_dir, remote)` — 只镜像 memory `.md`(排除 transcript · 实测仅 ~5MB/项目 · 非 1.8GB)· rsync/scp 封装
- `pull_corpus(remote, local_cache)` — T4 启动时拉
- TDD:mock 文件树 → 断言只 .md 被选 + transcript 排除 + 幂等(再跑无重传)。
- Commit。
