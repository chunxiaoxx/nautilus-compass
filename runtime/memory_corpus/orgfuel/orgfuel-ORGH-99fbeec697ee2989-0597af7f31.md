---
name: orgfuel-ORGH-99fbeec697ee2989-0597af7f31
description: "commit f8b491557f38 2026-06-06 feat(fde): feishu Bitable → e"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-99fbeec697ee2989
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit f8b491557f38 2026-06-06
feat(fde): feishu Bitable → expert-review settle wrapper (#43)
bitable_record_to_review maps a feishu Bitable record (fields:{列名:值}) to a
review dict (分项分 from the score columns). main() reads reviews from a feishu
Bitable (--feishu --app-token --table-id · via vtf feishu_client G3) or a local
JSON (--input), then settles → poi_credit. 7 tests green (incl. bitable mapping +
e2e). NO LLM. Ready: experts fill the Bitable → one command settles PoI.

Co-authored-by: nautilus-platform-saas-dialog <saas-dialog@nautilus.social>
