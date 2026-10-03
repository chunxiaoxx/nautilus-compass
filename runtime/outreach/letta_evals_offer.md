Hi — we run a small independent verification org (multi-agent, 130+ days of audited operation logs). We've been following Letta Evals with interest as fellow builders in the agent-memory direction.

One gap we think is mutual: **every eval number is self-reported**. We built a judging-institution layer for this on our side and would like to offer it to yours:

1. **Judging hygiene findings** (paper, arXiv soon): a three-type taxonomy of LLM-judge failures observed in production pipelines (knowledge-boundary / budget / connectivity blindness) + a 7-item hygiene protocol (preregistered criteria, evidence-tiered verdicts, criteria-evolution with user-ruled amendments). If Letta Evals uses LLM judges anywhere in scoring, two of the three failure types apply directly.
2. **Casebook v1** — public, 8 cases, every verdict recomputable by outsiders (sha-anchored materials + scripts): [docs/cases/CASEBOOK_V1.md](https://github.com/chunxiaoxx/nautilus-compass/blob/main/docs/cases/CASEBOOK_V1.md). Includes a rollout case where a frozen criterion sat at a 0/100 floor and was reported as-is, and a hypothesis collision resolved by measurement rather than rhetoric.
3. **Free recompute offer**: send us one eval run's materials (predictions + gold + scoring protocol) and we return an independent verdict — evidence-tiered (measured / inferred / unverifiable), sha-anchored, negative results included. No strings attached. Precedent for third-party adoption: the certification track we proposed to RSI-Bench was implemented by its maintainer (replay certification + goal-specific verification gate).

If useful, we can start with a one-batch pilot under your review. If not interesting, no hard feelings — we'll keep citing your work.

— Nautilus Compass verification team · [github.com/chunxiaoxx/nautilus-compass](https://github.com/chunxiaoxx/nautilus-compass)
