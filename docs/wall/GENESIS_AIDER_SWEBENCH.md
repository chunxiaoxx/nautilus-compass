# Genesis Receipt #1 · Aider SWE-bench Lite · 2026-09-19

**Subject**: Aider-AI (Aider + GPT-4o & Claude 3 Opus) · SWE Bench Lite
**Claim under test**: "Aider scored **26.3%** on the SWE Bench Lite benchmark"
(aider-swe-bench README, citing swe-bench/experiments PR #7)
**Verdict**: **agree** — independently recomputed **79/300 = 26.3%**, exact match.

## Evidence (all public bytes)

| Artifact | Source | Check |
|---|---|---|
| Predictions | `Aider-AI/aider-swe-bench` → `predictions/multi-models--gpt-4o--openrouter-anthropic-claude-3-opus/all_preds.jsonl` | 300 entries, 300 unique `instance_id`, 290 non-empty `model_patch` ✓ |
| Official results | `swe-bench/experiments` → `evaluation/lite/20240523_aider/results/results.json` | `resolved` bucket = 79 instances ✓ |
| Cross-check | resolved ∩ predictions | 79/79 ⊆ prediction set; 0 orphans ✓ |

Recompute: `|resolved ∩ pred_ids| / |pred_ids| = 79/300 = 0.2633` → **26.3%** ✓

## Boundary (honest scope)

This receipt verifies **arithmetic consistency of the published artifacts** (the
claim is derivable from public evidence, exactly as stated). It does NOT re-run
the benchmark harness itself (docker-based evaluation, s3-hosted logs). Chain:
claim → predictions file → official results file → ratio. Every step recomputed
from bytes; no trust in either repo's summary text was required.

## Why this subject first

Aider's benchmark repo is what public evidence hygiene should look like — raw
predictions, transcripts, and harness all published. Verification of honest
work is a gift, not an attack. Signed with `assay-verify` SDK v0.1.0 (its
first third-party use).

---
Protocol: Assay Protocol v0 · Verifier: 伊洛科技有限公司 (Nautilus Assay, ref impl)
Liability: docs/wall/ASSAY_LIABILITY.md (challenge window 90d, overturn = same-prominence OVERTURNED)
