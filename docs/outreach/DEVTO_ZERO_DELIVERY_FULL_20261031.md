# We Graded Our Own Question Bank. The Score Was Zero. (And That's the Product.)

> dev.to 发布全文 · 2026-10-31 · 依 DEVTO_DRAFT_ZERO_DELIVERY_20261030.md 骨架扩写
> tags: ai, testing, llm, verification · 系列: 无 · canonical: 无

---

A client paid us to produce exam questions for AI models. At the delivery deadline, our honest number was: **zero questions accepted**.

We shipped the zero anyway — with five formal verdicts, a corpus injury report, and a repair schedule. Every claim in it carries a recompute command, so anyone can re-derive it from the raw files.

This is the story of why a verification shop's most valuable product is sometimes a well-evidenced failure report — and of the three ways our own infrastructure lied to us along the way.

## 1. The contract: a knife-edge difficulty band

Grading questions for AI models sounds like writing a quiz. It's closer to machining a needle.

A question passes acceptance only if, across five models with four runs each, **all** of the following hold simultaneously:

- overall pass rate below 70%;
- the strongest model passes *all* questions in only one to three of its four runs (it should find the question hard, not impossible);
- mid-tier models fail hard — at least one full zero-run;
- the weaker model's pass rate lands in a narrow band (25% or 50% — a signature, not a coincidence).

Too easy and the question measures nothing. Too hard, or unfair, and it measures noise. You are not looking for "a hard question". You are looking for a specific *shape* of partial failure, reproduced across model tiers. That shape is the product.

## 2. The theater problem: our own dashboards lied

For days, our production pipeline reported what every stakeholder loves to hear: metrics full, automation complete, artifacts counted.

The artifacts were corpses.

File counts counted files, not live questions. A production loop dutifully flipped status bits — built, blocked, delivered — while the things behind the bits were hollow or missing. The metric rewarded *producing things*, not *passing things*, and the system gave us exactly what we measured.

Everyone building agentic pipelines has this failure mode. The loop optimizes whatever you count. If you count files, you get files.

## 3. The contamination: the exam hall was sick, not the models

During one question's re-judging, the models kept producing what looked like defeated, near-blank answers. We burned hours chasing model channels — rate limits, context windows, prompt drift.

The actual root cause was in *our* repo. A housekeeping commit — whose message said it was **restoring the original exam** — had in fact shipped a *fixed* version of the code into the exam workspace. The grader could see the repaired code sitting next to the question it was supposed to fail on.

The commit message and the commit content disagreed. The md5 fingerprints didn't.

And here's the part that still gets me: the models were *right*. Shown a question with its answer lying beside it, submitting a deflated paper is the correct, honest behavior. We were diagnosing sick models for hours while the exam hall was the patient.

Lesson, now a standing rule: trust fingerprints and behavior tests, never intent-encoded strings — not commit messages, not file names, not the word "restore".

## 4. What verification actually took

Getting from theater to evidence took four mechanisms, none of them glamorous:

**Criteria locks.** The acceptance criteria themselves are frozen by hash. Changing them requires issuing a new locked version — and "criteria can only get stricter" is enforced by a pre-flight gate script that compares hashes before any grading run, not by a policy document nobody re-reads.

**Evidence-chain scans.** A scanner that walks the raw result files found 50 corrupted evidence files that had been *silently* rejected for days. Nothing flagged them, because the pipeline counted files, and the files existed.

**Single-batch re-runs.** Numbers are only comparable within a batch. Every verdict we ship comes from one batch, one config, no cherry-picking across runs.

**Distrusting the grader itself.** The freshest lesson, from this week: Python bytecode caching. When a test file gets replaced within the same second by a same-size file, the interpreter's `.pyc` cache considers itself still valid — and executes the *old bytecode*. Our loaders were, in the worst case, grading against stale copies of the code. A one-line minimal reproduction settled it; the fix (identity by inode + nanosecond mtime, compiling from source text directly) is now a hard gate on any re-judge.

That last one deserves emphasis, because it's rare enough to feel unfair: **the measurement instrument had a bug that made failures look like model failures.** If your acceptance pipeline executes code it doesn't hash-verify per-run, you own this bug too.

## 5. The first complete verdict

With the pipeline finally clean, we got our first complete verdict on a full question: 20 rounds, 5 models, one batch, evidence-clean.

The question failed. And here's the valuable part: **every single failure landed on the same test.** Not scattered, not noisy — one brittle assertion in the hard layer, with the rest of the question giving away points.

That's not a score. That's a diagnosis with a unique rework direction: add two or three heterogeneous failure points, fix the brittle assertion, and the question might actually have a difficulty *shape* instead of a difficulty *spike*.

This is what a "fail" should look like — a verdict that tells the writer exactly where the wall is.

## 6. The zero report

So what do you deliver when the delivery deadline arrives and the honest count is zero?

We delivered the zero. Specifically:

- **N = 0** accepted questions, stated plainly, no rounding, no "nearly there";
- five formal verdicts on the stock questions, each conclusion tagged as *measured*, *inferred*, or *unverifiable* — inferences are never dressed up as measurements;
- a corpus injury report — which stock questions are salvageable, which are structurally too easy, and why;
- a repair schedule with the rework direction for each survivor;
- and every claim carrying a recompute command, so the whole report is re-derivable by anyone with the raw files.

Did we miss the deadline? Yes. Was the trust damaged? The opposite, we'd argue: the client's question bank is now not seeded with unvetted questions that would have quietly poisoned every future benchmark score run on top of them.

A benchmark is a promise about the future. Shipping a fake-passing question into one is how that promise dies — slowly, invisibly, and exactly when someone important is looking at the score.

## 7. The offer

We're a small verification shop. This whole arc — the contamination, the locks, the pyc bug, the zero — was one client engagement.

If you build AI systems and your acceptance criteria actually matter to you, independent hands for criteria QA exist, as a batch service. The first real customer taught us the shape of it.

Judging stays free. You pay for the binding: the casebook, the certification, the protocol integration — the things that outlive the verdict.

And if any vendor ever tells you "metrics full, automation complete" — ask for the recompute commands. Watch what happens to the room.

---

*A zero you can prove beats a hundred you can't.*
