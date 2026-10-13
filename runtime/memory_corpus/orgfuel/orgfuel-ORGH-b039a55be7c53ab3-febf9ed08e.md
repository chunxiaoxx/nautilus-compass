---
name: orgfuel-ORGH-b039a55be7c53ab3-febf9ed08e
description: "commit 72b8624195f5 2026-05-08 docs+CI: A/B/F/G/E batch · ra"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-b039a55be7c53ab3
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 72b8624195f5 2026-05-08
docs+CI: A/B/F/G/E batch · raw eval data · saas template · reproduce guide · star/contrib badges · PyPI OIDC
A · paper/results/em_bge_v3_per_question.jsonl + em_cross_judge_gemini_per_question.jsonl
    Force-add (override *.jsonl gitignore) so the 497-row Run 2 log and
    the 100-row Gemini cross-judge log ship inside the repo. Reviewers
    can now run scripts/bootstrap_em_jsonl.py and reproduce the 47.3%
    [42.9, 51.7] CI without re-spending $25 on the eval LLM API.

B · docs/SAAS_OPERATIONS.md
    Mirror of docs/PLATFORM_HANDSHAKE.md from the SaaS-dialog side.
    Production topology, tier definitions, billing flow, support SLO,
    monitoring SLI, compliance roadmap, marketing funnel. Many [TODO]
    placeholders for the SaaS dialog to fill in; OSS di
