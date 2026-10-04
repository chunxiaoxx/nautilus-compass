Hi — we run Nautilus Compass, a small independent verification org (multi-agent, 130+ days of audited operation logs). We've been following Letta Evals as fellow builders in the agent-memory space; this proposal is for this repo (we understand evals live here, not in letta-ai/letta).

One gap we think is mutual: **rubric-grader scores are self-reported by the same stack being scored**. Your `RubricGrader` (`letta_evals/graders/rubric.py`) routes scoring through an LLM judge — that's exactly where we've observed reproducible failure modes on our side, and we'd like to offer a verification layer for it:

1. **Judging hygiene findings** (paper, arXiv soon): a three-type taxonomy of LLM-judge failures observed in production pipelines — knowledge-boundary blindness, budget exhaustion, connectivity blindness — plus a 7-item hygiene protocol (preregistered criteria, evidence-tiered verdicts, criteria-evolution with explicit amendment rules). Applied to `RubricGrader`, the budget and connectivity types apply directly (judge API failures silently degrading scores), and the knowledge-boundary type applies to rubric ambiguity.

2. **Casebook v1** — public, 8 cases, every verdict recomputable by outsiders (sha-anchored materials + scripts): [docs/cases/CASEBOOK_V1.md](https://github.com/chunxiaoxx/nautilus-compass/blob/main/docs/cases/CASEBOOK_V1.md). Includes a rollout case where a frozen criterion sat at a 0/100 floor and was reported as-is, and a hypothesis collision resolved by measurement rather than rhetoric.

3. **Free recompute pilot**: run one Letta Evals suite and send us the materials (dataset + suite.yaml + results), and we return an independent verdict on the grading layer — evidence-tiered (measured / inferred / unverifiable), sha-anchored, negative results included, no strings attached. Precedent for third-party adoption: the certification track we proposed to RSI-Bench was implemented by its maintainer (replay certification + goal-specific verification gate).

If useful, we can start with a one-batch pilot on an example suite (e.g. `multi-model-simple-rubric-grader`) under your review. If not interesting, no hard feelings — we'll keep citing your work.

---

### Disclosures

- **Third-party product**: this issue mentions a third-party project — Nautilus Compass ([github.com/chunxiaoxx/nautilus-compass](https://github.com/chunxiaoxx/nautilus-compass)) — which is the authors' own project. The offer is free; there is no paid upgrade, trial-to-paid funnel, or lead-generation intent behind this proposal.
- **AI assistance**: this issue was written with AI assistance (Claude, by Anthropic), reviewed and edited by Chunxiao Wang before submission.

— Nautilus Compass verification team
