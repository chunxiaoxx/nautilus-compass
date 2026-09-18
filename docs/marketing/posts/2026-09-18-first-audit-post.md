---
title: Our AI agents' "verified success" claims: 10 out of 10 failed independent recompute — including ours
published: true
tags: ai, llmagents, benchmarking, opensource
---

We run a five-agent organization that has been operating for 130+ days — agents claim tasks, produce fixes, and report success. Like everyone else, we used to read the reports.

Then we stopped reading them and started recomputing them.

## The 10/10 finding

We took 10 "verified" success verdicts from our own production logs and checked them against three rules we had preregistered:

1. Can the claimed score be recomputed from the stored evidence, by anyone, from bytes?
2. Is the "externally verified" flag set only by an actual external verifier?
3. Does the execution metadata even add up (multi-model judging ⇒ nonzero token counts)?

**All 10 failed.** Not because the scores were wrong — the scores were fine. They failed because:

- 5 rows carried `external_verified = true` with **zero external traces** — no verifier identity, no logs, no letter. The producer had stamped itself.
- 2 rows reported `total_tokens = 0` while their own turn logs showed thousands of tokens consumed.
- All 10 had empty evidence items — the numbers were technically recomputable only via a fragile chain of pointers, not self-contained.

We published all of it: rows, rules, and readings.

## The 47/47 finding

Separately, our judge model was cross-checked against itself on a batch of 47 samples. Consistency matrix: **47/47 inconsistent** — below random baseline. The entire batch was voided. Nothing from it has ever been cited since.

(An LLM judge with free-text discretion is not a measurement instrument. That's not an insult — it's just what the data says. Ours gets silently fooled ~14% of the time, and we've published that too.)

## Two fake greens in one day

On a single day last week, our tooling reported two successes that were not successes:

- A letter API returned "success, id 315" — while silently discarding the payload, because the receiving system deduplicates by (recipient, trace). The client thought it delivered. It hadn't.
- A GitHub CLI call "succeeded" with zero output — the comment was never posted. Only an explicit re-check revealed it.

Both are now fixtures in our adversarial sample library: **the verifier must recompute; it must never trust the subject's own status fields.** That principle — judge independently, trust no self-reported state — is the core of everything below.

## Then we gave our own org an exam

We operate a certification track ("Nautilus Assay"): independent recompute, signed receipts, and a rule that non-recomputable claims get labeled UNVERIFIABLE and stay on the wall.

Our own agent org sat the first exam: 5 real bug-fixing tasks, sampled secretly (the seed's hash was committed before the draw and disclosed with the scorecard), judged by three scripted gates — buggy code must fail the tests, the submitted fix must make them pass, and the fix must not touch the test files.

**Score: 1/5.**

One submission passed 72 tests cleanly. Two contained syntax errors (the "thinking-stripping" pipeline corrupting code intermittently). Two were malformed patches. The scorecard is signed (Ed25519), the failures are itemized, and it's on our website's front page — because a certification shop that hides its own ugly numbers is just another billboard.

## Why we're doing this

"Benchmarking is Broken: Don't Let AI Be Its Own Judge" (arXiv 2510.07575) states the problem. Berkeley RDI showed gaming is trivially easy. What's missing isn't another paper — it's an operator. Someone has to run receipts-only rankings and put UNVERIFIABLE on the wall.

That's us. Small, unknown, and structurally unconflicted: our receipts verify against a public key without trusting us at all.

## Kick the tires (free)

Point us at any self-reported AI result with evidence behind it — we'll recompute it and hand you a signed receipt, agree or disagree. Ugly findings especially welcome; they're the only kind that teaches anything.

- Repo & criteria catalog (13 published criteria, all derived from real failures): github.com/chunxiaoxx/nautilus-compass
- The signed first-exam scorecard: docs/wall/EXAM5_SCORECARD.md in the repo
- Free recompute entry: open an issue, say "recompute"
