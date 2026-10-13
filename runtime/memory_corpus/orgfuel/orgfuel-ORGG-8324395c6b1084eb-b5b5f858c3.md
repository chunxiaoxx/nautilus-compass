---
name: orgfuel-ORGG-8324395c6b1084eb-b5b5f858c3
description: "判读档判例 2026-06-22-compass-convergence-slices · 切片 C · recall "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-8324395c6b1084eb
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-22-compass-convergence-slices · 切片 C · recall 清污(删 dummy.md·一步·安全)
## 切片 C · recall 清污(删 dummy.md·一步·安全)

- 实测:`~/.claude/projects/default/memory/dummy.md`(12 字节 "test memory"·2026-05-01 冒烟遗留)是 `default` 项目唯一文件→任何 project=default 的 v14 recall 必 rank-1(候选池只它一个),score 0.72 霸榜。
- 文件在 T4 daemon 侧(经 cloud 跳板)。
- Step 1 — 确认:`ssh cloud "ssh -i ~/.ssh/id_ed25519_qb ubuntu@43.166.8.20 'cat ~/.claude/projects/default/memory/dummy.md; ls ~/.claude/projects/default/memory/'"`(T4 跳板·fail2ban 清后)。
- Step 2 — 删:`rm ~/.claude/projects/default/memory/dummy.md`(或删整个 default/memory/·确认无他文件后)。inotify 标脏自动重索引。
- Step 3 — 验证:`curl -s "http://127.0.0.1:8770/v1/v14/recall?q=memory+capsule&scope=user&top_k=3"`·期望 dummy.md 不再 rank-1。

---
