---
name: orgfuel-ORGH-110415de0ae0db90-180bfab887
description: "commit f396c186e5c7 2026-06-21 fix(ale-eval): default judge_"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-110415de0ae0db90
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit f396c186e5c7 2026-06-21
fix(ale-eval): default judge_version=202510 (live bug: public_eval defaults 202301→ImageNotFound)
live 标定发现:public_eval 不传 judge_version 默认 202301·去 pull ale-bench:cpp23-202301
(只建了 202510)→ ImageNotFound。修=DEFAULT_JUDGE_VERSION=202510 显式传。
live 验证:ahc001 trivial→0.0 两次确定·rejected 路径(无输出→0)成立。9 TDD 绿(+judge_version guard).
