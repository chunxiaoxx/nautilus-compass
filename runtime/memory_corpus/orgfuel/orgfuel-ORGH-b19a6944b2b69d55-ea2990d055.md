---
name: orgfuel-ORGH-b19a6944b2b69d55-ea2990d055
description: "commit 7721501609a9 2026-08-28 fix(eval): utterance context "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-b19a6944b2b69d55
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 7721501609a9 2026-08-28
fix(eval): utterance context 注入 session 日期(tr 型 e2e 0/5 根因:context 无日期可算)
诊断:tr 5 题模型明说 no record of the date,检索命中的 session 全对——缺的不是召回是 context 里的日期戳。
修复:build_ssu_context 加 dates 参数,chunk 头 (from Session N, YYYY-MM-DD)。

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
