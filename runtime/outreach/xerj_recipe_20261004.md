Subject: recipe: agent-memory retrieval & evaluation (as promised)

Hi Ivan,

The recipe I owed you — two patterns from our stack that a reference corpus would directly sharpen, written so others can replicate the failure modes, not just the wins. Both come from production scars, all numbers reproducible.

## Recipe 1 — Retrieval over session memory: the corpus IS the agent's own history

Retrieving from a reference corpus and retrieving from an agent's own session memory are different problems, and the difference is invisible in standard benchmarks:

1. **Query = situation, not question.** In agent memory the query is usually the agent's current context (task state, recent errors), phrased as an imperative ("deploy failed again with 401"), not an information need ("how do 401s work?"). Hybrid retrieval (dense + sparse) over BGE-M3 embeddings handled this better than dense-only in our runs; but the bigger effect was **slicing**: chunking session memory by semantic topic instead of by token window changed recall@1 by double digits in Chinese, and *reversed* the ranking of two embedding models vs their MTEB scores. MTEB-ledger performance did not predict in-distribution behavior on our session data.
2. **Corpus gap that would change our answers:** a reference corpus of *real multi-session agent trajectories* (with timestamps, failures kept, verbatim) — not cleaned docs. What "retrieval quality" means when the corpus is the agent's own memory: a hit that surfaces *that you already tried this and it failed* is worth more than a hit that surfaces the manual page. Nobody scores that. If your corpus has raw agent-session data with failure turns intact, we will switch our eval answers because the ground truth changes.
3. **One non-obvious failure mode:** fill_diagonal-style masking bugs (excluding gold pairs from the candidate pool) silently turn a retrieval eval into a constant-zero or constant-pass exercise. We shipped one. Test: if every query scores 0 hits, suspect your mask, not your model.

## Recipe 2 — Evaluation: preregistered criteria, self-report and recompute as separate artifacts

The pattern we keep re-learning, stated once compactly:

1. Freeze criteria **before** running: metric, threshold, stop-loss, and the exact verifiable artifact each claim points to. Criteria may only move *stricter* mid-stream; loosening requires a fresh preregistration.
2. Label every claim `measured` / `inferred` / `unverifiable`. Inferred claims carry an upgrade path. The most useful eval artifact we ever published was a self-report saying "2 of 4 gates FAIL on recompute" — the FAILs, kept visible, are what made the green credible afterwards.
3. **Compute a majority-class baseline before claiming accuracy.** We just watched a 0.87 binary classifier that a 0.78 always-yes baseline nearly matched (n=60, CI overlapping baseline). n<100 needs the CI printed next to every headline number or the number isn't a claim, it's a mood.
4. Paired designs beat unpaired by an order of magnitude of information: same frames, two checkpoints, McNemar. Our unpaired reading overstated an effect ~4x versus the paired one.

If either recipe earns its keep on your corpus, an honest issue saying where the index is thin would be worth more to us than a star. The independent-recompute offer from my last note stands, no push.

— Chunxiao
Assay / nautilus-compass
