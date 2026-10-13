---
name: orgfuel-ORGH-0eff244c08690852-e0c6de7362
description: "commit aa361c9ee8be 2026-06-23 test(hooks): inbound select_i"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-0eff244c08690852
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit aa361c9ee8be 2026-06-23
test(hooks): inbound select_inbound — fix watermark surface-once (Phase2 Task2.2 · B4)
measurement-first 纠错: plan 假设'per-project漏'是错的·hook始终扫nautilus-core。
真bug=watermark surface-once: 老消息surface一次后跨session永不再现→丢未消费入站(本session亲踩漏一批)。
修=select_inbound纯函数+近48h floor二次surface+watermark只推进到newest-new(不跳now)。
端到端smoke自证: 现surface出20条之前丢失的近期入站。5 tests green。
⚠️ hook本体在全局~/.claude/hooks/inbound_outbound_surface.py(非worktree git)·已改live。
