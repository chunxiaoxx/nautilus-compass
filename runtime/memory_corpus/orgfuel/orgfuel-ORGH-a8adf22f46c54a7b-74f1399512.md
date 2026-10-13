---
name: orgfuel-ORGH-a8adf22f46c54a7b-74f1399512
description: "commit f5bd8b42570b 2026-09-22 fix(recompute): 三份 session.js"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-a8adf22f46c54a7b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit f5bd8b42570b 2026-09-22
fix(recompute): 三份 session.jsonl 被 .gitignore *.jsonl 静默拦截——强制入库
非实现者复算(全 GREEN)抓到的实现者假绿:此前声称工件完备,
但日志本体从未入 git,克隆者无法验签。git add -f 补齐三域日志,
判据 2 字面达标。教训:声称入库前必须 git ls-files 验证,
通配 gitignore 会静默吞工件。

Co-Authored-By: Claude <noreply@anthropic.com>
