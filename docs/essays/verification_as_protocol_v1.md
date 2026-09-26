# Verification as Protocol: the missing layer of the agent stack

> G4 draft v1 · 2026-09-27 · working title (candidate 1 of 3 from outline) ·
> every number traceable to repo artifacts: BC1_LAUNCH.md ·
> SELFTEST_SCORECARD_V2.md · RECOMPUTE_SELFTEST.md ·
> mem0_baseline/BASELINE_REPORT.md · decision_set sha256=3b9def7d…
> Next: adversarial self-review (3 genuine objections), then P2 final
> number check before any submission. Do not relax numbers in review —
> tighten only.

We built a 30-question exam that tests one narrow thing: whether an AI
organization can correctly remember 130 days of its own operating history.
Before publishing it, we sat our own stack down and took it ourselves.
First attempt: 11 out of 18. Then we audited all seven failures, and every
single one was the grader's fault, not the examinee's. Two questions had
wrong answer keys — the examinee was right, and our ground truth was wrong.

Hold that for a moment, because it is the thesis of this essay. The industry
is wiring agents into production — memory layers, eval harnesses, leaderboard
culture — on the assumption that the interesting failure modes live in the
models. Our exam results point somewhere else. The most dangerous failures
now live in the verification layer, the layer whose entire job is to catch
failures. A wrong answer teaches your system one wrong fact. A wrong grader
teaches your system that wrong answers work — and you will never see it,
because the grader is the thing you trusted to show you.

This essay makes one argument: in an agent stack, verification should be a
protocol, not an institution. Below: the evidence that pushed us there
(including our own grading errors, published in full), the four primitives
we landed on, and an honest list of what 30 questions cannot prove.

## Self-reported numbers now expire faster than models

The working assumption of the current stack is that models are the moving
part and everything around them is infrastructure. That assumption made
sense when a model shipped once a year. It has quietly inverted. Models now
rotate monthly; self-hosted setups swap backbones mid-project; the "same
product" runs on different brains depending on the day and the contract.
A benchmark number attached to a model identity is a claim about a moving
target. Its shelf life is measured in weeks, not quarters.

What survives model churn is not any particular number. It is the *ability
to recompute the number*. A self-reported score and a recomputable score
look identical on a leaderboard and behave completely differently six months
later: the first is a screenshot, the second is a live claim with a debt
that comes due the moment anyone reruns it.

This is not a new economic observation — inspection regimes exist wherever
products are too complex for buyers to evaluate directly. What is new is the
reflex answer most teams reach for. When someone points out that graders can
be wrong, the standard response is "then we need a bigger referee": an
independent lab, a standards body, a certification institution. We think
that answer is backwards, and our own audit trail — kept, published, and
linked throughout this essay — is the clearest way to show why.

## Organizational memory is the compounding asset nobody stress-tests

Long-running agents compound their value somewhere other than weights: in
memory. Decision timelines, incident ledgers, cross-service state, who
promised what to whom. An agent that runs for 130 days is not valuable
because it is 130 days smarter; it is valuable because it holds 130 days of
ground truth that no fresh model instance has. That memory is the
organization's compounding asset.

The industry measures memory systems where measurement is easy: retrieval
quality (does the right chunk come back?) and answer quality (does the
answer sound right?). Almost nobody stress-tests the *write path* — whether
what got remembered is what actually happened. That is a strange blind spot,
because write-path distortion is precisely the failure that compounds. A
retrieval miss costs you one answer. A corrupted write costs you every
future answer that touches it, forever, invisibly.

So we built an exam for exactly that seam. Assay BC1 seeds 30 questions
from one real AI organization's 130-day operating history (ours,
parameterized and de-identified so the questions survive even though the
underlying events are ours). Four dimensions, one theme:

- **Cross-frame state consistency** (7 items): given a timeline, public
  claims, and raw rows, derive the true state and catch the contradictions.
- **Write-gate quality** (8 items): does the memory system reject poisoned
  writes, respect dedup thresholds, and enforce anchor semantics?
- **Recurrence detection** (7 items): can it tell incident #3 from incident
  #1 — count recurrences, recognize false-green resolutions, see drift?
- **Attribution traceability** (8 items): which link in which chain
  actually violated the rule, and what does the anchor pool say about it?

The split is public 18 / sealed holdout 12, and the holdout stays sealed
until the first external examinee shows up — which is also the only
incentive-compatible way for us to say "you haven't seen the questions."

## One configuration flag cost 7 points on identical questions

Before publishing, we ran the public 18 through the exam ourselves in three
configurations. Same backbone model (MiniMax-M3), same questions, same
grader. Only the memory path changed:

| Arm | Score |
|---|---|
| Direct access to source materials | **16/18** |
| Through mem0 2.2.0, default configuration (write → retrieve → answer) | **11/18** |
| Through mem0 2.2.0, write-time compression disabled (only variable changed) | **18/18** |

A write-time semantic-compression feature — one flag, default on — costs 7
points out of 18 on audit-style questions. The anatomy is unambiguous, and
it is field-level rather than vibe-level. The default path compresses
structured operational logs into narrative sentences at write time. The
fields that get dropped are exactly the machine-checkable ones: an
`artifact: null` marker that encodes "no receipt exists," dedup thresholds,
anchor references. Audit questions ask about precisely those fields, because
that is what audits do. The compressed memory can still *tell a story* about
the incident; it just cannot *prove* anything about it.

The collapse concentrated where you would predict: recurrence detection fell
from 4/4 to 1/4. Once incidents are stored as prose, incident #3 and
incident #1 blur into "that recurring problem with the deploy job," and
counting — the thing recurrence detection is — becomes impossible.

Two disclosures, because the grader is watching us too. First, the
no-compression arm beating direct access (18 vs 16) is within single-run
variance for a reasoning model at n=1; we report it and do not build a claim
on it. The load-bearing finding is the compression delta, which survived
per-field anatomy and a same-model controlled comparison. Second, this is a
report, not an indictment: mem0's default optimizes for conversational
coherence, which is a legitimate target. It is simply the wrong default for
audit, compliance, and forensics workloads. Our free health check for the
community: **if your agents run in those contexts, disable write-time
semantic compression and store the originals.** Every artifact — the full
per-item flip table, the causal-comparison arm, all inputs and outputs — is
in `mem0_baseline/BASELINE_REPORT.md` in the exam repository.

If you run a memory product and want your configuration on the wall, that
wall is open.

## Verification should be a protocol, not an institution

So: graders get questions wrong, memory write-paths corrupt quietly, and
model churn devalues static claims. The reflex answer is a bigger referee.
Here is the problem with referees: when the referee errs — and ours erred
twice in the first two weeks of a single exam — an institution has to
*renegotiate its authority*. Watch how that goes in practice. Either it
defends the error (and burns the authority), or it quietly fixes it (and
burns the audit trail, because nobody publishes their own errata
voluntarily). Certification works by snapshots; every snapshot is a new
negotiation.

A protocol works differently. It does not ask you to trust anyone; it asks
you to spend compute. Clone the repository, run the grader on the published
answers, check the signature. When the protocol's operator errs, the error
is a public artifact next to the correction, and the authority was never in
the operator to begin with. Trust moves from the institution to the
protocol — which, as a side effect, is also what limits the operator's
space for misconduct. You cannot quietly inflate what anyone can recompute.

Assay BC1 runs on four primitives. Each is boring alone; that is the point.

1. **Three-state grading.** Every item returns PASS, FAIL, or U
   (unverifiable — missing data, unparsable submission, non-recomputable
   answer). U never counts as a pass. There is no "partially correct," and
   there is no charity, because gray zones are where self-serving scores
   live. Every item's criteria explicitly references a public catalog entry
   (`criteria@catalog-v0`) — the grader implements published rules, it does
   not exercise taste.

2. **The grader is public.** `verify_bc1.py` is a file in the repository.
   Examinees can run it on their own submission before handing it in, and —
   more importantly — audit its implementation. If you believe the grader
   is wrong, you do not have to take it up with us; you can read the
   grader. (The exam's decision set is content-addressed:
   `sha256=3b9def7d…`, so "which version graded me" is never ambiguous.)

3. **Signed receipts.** Every scorecard is signed with ed25519; the public
   key is published. Results cannot be silently edited after the fact —
   only errata'd, with the erratum filed next to the original, both
   visible. This sounds like table stakes. Our signing incident (next
   section) is the argument for why it needs to be protocol rather than
   practice.

4. **Challengeable verdicts.** Any examinee can formally challenge a result
   with their submission artifacts inside a 90-day window. The judging
   account is bidirectional: judges err too, and a verification system that
   cannot process "the grader was wrong" is not a verification system — it
   is a false-ground-truth factory. We know, because that is precisely how
   our own first release failed.

## We failed our own exam first — and published the failures

The full chain, in order, every link public:

1. **v1 self-test: 11/18.** Our own pipeline sat the exam and failed seven
   items.
2. **Per-item audit.** All seven FAILs were attributed to question-side
   defects: two wrong answer keys (the examinee was right; our ground truth
   was wrong), three ambiguous wordings, two undefined boundaries. Zero
   were the examinee's fault.
3. **Non-implementer recompute.** A separate session, given only the
   artifacts and the published criteria, independently re-derived the whole
   scorecard. Result: GREEN — every claim supported. And it caught what we
   had missed: two items where the scorecard's raw scores (69/62) did not
   match our reported scores (71/67). A transcription error, in the
   scorecard of an exam about organizational memory fidelity. Errata filed,
   kept, not deleted.
4. **The signing incident.** Our first "signed" scorecard had been signed
   with a mis-generated key — the public key file was mistakenly used as a
   seed, and our self-verification walked down the same wrong path and
   passed. The recompute caught that too. Re-signed with a dedicated key;
   the incident record stays.
5. **v2 retest: 18/18.** Five item defects fixed, all seven formerly-failed
   items pass, zero new failures. That last part matters more than the
   score: it is the reverse-proof that the v1 attribution was correct. If
   the defects had really been the examinee's, fixing the questions would
   not have flipped exactly those items and nothing else.

An adjacent case sharpened the lesson. In an unrelated audit, we
mechanically attributed 29 failures of a task benchmark; an independent
re-review overturned five of our attributions. Our method had checked one
of the grader's two judging gates and missed the other. The grader's
implementation *defines* what "correct" operationally means, so attribution
that does not cover every gate of the grader is attribution that invents
its own ground truth. Judges err; protocols make those errors expensive to
hide and cheap to process.

An exam hall that publishes its own grading errors is the product. Not a
slogan attached to the product — the product. Everything else on this page
(recompute desk, scorecards, the exam itself) is downstream of that
sentence.

## What 30 questions cannot prove

Honest limits, stated before anyone else states them for us:

- **30 items is proof of process, not statistical power.** The first
  release contains only machine-gradable item types; the long-horizon
  dimensions (multi-day consistency, drift under load) are a separate
  volume, not smuggled into this one.
- **Scores are comparable only within this item set.** BC1 is an
  organizational-memory verification prototype, not a general agent
  benchmark. Do not put it on a leaderboard next to coding benchmarks and
  pretend they measure the same construct.
- **The independence paradox is real, and our answer to it has a price.**
  Who verifies the verifier? Our answer is not "a bigger institution" — it
  is the protocol plus recomputable artifacts. The price: the same
  machinery that clears us can indict us, and the operator cannot make a
  claim the artifacts do not support. We consider that a feature. It is
  also a constraint on our growth story, and we are telling you that up
  front rather than in a footnote.
- **The three-arm experiment is n=1 per arm.** Deltas are reported with
  field-level anatomy rather than error bars, because error bars need runs
  we have not spent yet. The compression finding is causal and controlled;
  the 18-vs-16 overshoot is disclosed as within-run variance, not claimed
  as signal.

## Take the exam

The entry path is deliberately boring:

1. **Sign up**: open an `exam-signup` issue in the repository, pick BC1,
   accept the integrity terms (U never counts; guessing scores as FAIL, not
   as clever).
2. **Take it**: you receive the current public 18 — same distribution as
   the self-test set; the holdout 12 stays sealed until the first external
   examinee. Human, agent, or script; however you answer, the submission
   must be recomputable from artifacts.
3. **Get graded**: we run the public grader; you get a signed three-state
   scorecard. Pre-grade yourself with the same script if you like — that is
   allowed, because it is the point.
4. **Challenge if you must**: 90-day window, artifacts required, and yes —
   you might be right against our answer key. It has happened before, to
   the operator's own exam.

And the commercial part, said plainly, because hiding it would be stranger
than not: we run a **recompute desk**. Bring us a self-reported result you
do not fully trust — an agent's, a vendor's, your own system's — and we
independently recompute it from artifacts, under the same four primitives.
The first one is free, because that is how trust gets bootstrapped in
verification markets: not by claims, but by receipts.

In a stack where models rotate monthly and memory compounds for years, the
durable asset is not the model. It is the receipt.

---

*Disclosure: Assay BC1 is operated by 伊洛科技有限公司 (Nautilus Assay).
All artifacts referenced above are in the public repository:
github.com/chunxiaoxx/nautilus-compass — exam, grader, decision set
(sha256=3b9def7d…), scorecards, errata, recompute reports, and the
three-arm baseline. The author's own grading errors are in there too; they
are not hard to find, and that is the point.*
