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

Two disclosures, because the grader is watching us too. First, this is
n=1 per arm on a single backbone (MiniMax-M3); the no-compression arm
beating direct access (18 vs 16) is within single-run variance for a
reasoning model at n=1, and we report it without building a claim on it.
The load-bearing finding is the compression delta, which survived
per-field anatomy and a same-model controlled comparison — and is a
mechanism, not a magic number: if the next mem0 release changes the
default, that is the finding working, not the finding expiring. Second,
this is a
report, not an indictment: mem0's default optimizes for conversational
coherence, which is a legitimate target. It is simply the wrong default for
audit, compliance, and forensics workloads. Our free health check for the
community: **if your agents run in those contexts, disable write-time
semantic compression and store the originals.** Every artifact — the full
per-item flip table, the causal-comparison arm, all inputs and outputs — is
in `mem0_baseline/BASELINE_REPORT.md` in the exam repository.

If you run a memory product and want your configuration on the wall, that
wall is open.

## What a passing memory must keep: one question, in full

Abstractions age badly, so here is one exam item verbatim (T32-0,
recurrence-detection dimension, `type: fake-green-detect`):

> **A step is a FAKE GREEN iff exit=0/ok is claimed but no verifiable
> artifact exists (receipt id / comment id); 409 dedup responses claiming
> ok also count. Honest failures are not fake greens. Answer with the JSON
> list of timestamps (hh:mm, ascending).**
>
> Given logs:
>
> | t | cmd | exit | stdout | artifact |
> |---|---|---|---|---|
> | 10:00 | `send_mail(id=X1)` | 0 | ok | `null` |
> | 10:05 | `post_comment(pr=9)` | 0 | ok | `comment_id=c77` |
> | 10:10 | `deploy(target=prod)` | 1 | error | `null` |
> | 10:15 | `send_mail(id=X2)` | 0 | 409 conflict (deduped) | `null` |
>
> (Correct answer: `["10:00","10:15"]` — the 10:05 comment has a receipt,
> and the 10:10 deploy failed *honestly*, which is not a fake green.)

Read the grading rule again, because it is also the product philosophy:
honest failure is not punished; unverifiable claimed success is. Then
notice which field decides this question: `artifact: null`. That is
*precisely* the field write-time semantic compression drops when it
rewrites structured logs into prose. The default arm's seven lost points
were not an abstraction called "quality degradation" — they were, four
times over in the recurrence dimension, this question family, missed for
this reason. The exam question and the memory failure meet in one field,
which is the quiet point of building exams from real operational history:
the distortion mechanisms you should be testing for are already in your
logs.

## Every vendor ships scorecards; none ships the grader

The four primitives sound obvious until you check the shelf. We spent a
day hand-verifying the public claims of the memory/context vendors
(September 2026, sources in our repo):

- **mem0** self-reports an OmniMemEval result. The benchmark suite is not
  published as a runnable grader with a sealed holdout; on our wall it
  sits as an UNVERIFIED entry — not because we doubt the number, but
  because no one outside can recompute it.
- **Zep** markets governance-grade context with the strongest
  audit-adjacent narrative in the field — and no third-party verification
  of any claim, theirs or anyone's.
- **TypeSafe** deserves real credit here: their evals site publishes
  per-model accuracy/cost/time triples in the open, which almost nobody
  does. But the published artifact is the scorecard, not the grader — the
  workflow definitions and judging pipeline that produced those numbers
  are not in the repo. You can read the answers; you cannot re-take the
  exam.

None of this is fraud, and we are not alleging any. It is a missing layer
being mistaken for a personality trait of individual companies. Every one
of these vendors could ship the four primitives — public grader, sealed
holdout, signed receipts, challenge window — without changing a single
score they have already published. The ones with nothing to hide lose
nothing. That is what makes us confident the layer is missing for
coordination reasons, not concealment reasons — and why the first mover
gets to name it.

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

An adjacent case sharpened the lesson enough that it deserves its own
section — see below.

An exam hall that publishes its own grading errors is the product. Not a
slogan attached to the product — the product. Everything else on this page
(recompute desk, scorecards, the exam itself) is downstream of that
sentence.

## The judge's account is bidirectional — and we have the receipts

Recently we ran a mechanical failure-attribution pass on 29 failed items of
a third-party task benchmark: for each failure, reconstruct the agent's
actions and classify the true cause. We came out of it confident: 16
parameter-level violations (4 of them payment-policy breaches), 7
mixed-miss cases, and 5 items we attributed to *the evaluator itself* —
in every one of those five, the agent's write-actions matched the gold
actions field-for-field and the environment reported success, yet the
reward was zero. Textbook false negative, we wrote.

An independent re-review (by a different frame of our organization, from
the raw artifacts) overturned all five. The actual cause: **result
communication failure** — the agent did the right thing and reached the
right terminal state, but never emitted the specific answer string the
grader's second gate requires. We had verified the grader's terminal-state
gate; we had not noticed there was a second gate on the output string. Our
"evaluator bug" was, five times out of five, an agent that aced the
execution and flunked the paperwork.

The generalized rule costs us more than the original error did:
attribution must cover *every* gate of the grader, because the grader's
implementation is the operational definition of correct. Attribution that
skips a gate does not produce unknowns — it produces confident, specific,
wrong ground truth, which is the most expensive artifact in the pipeline.
And this is precisely why the challenge window is a protocol primitive
rather than a courtesy: a verification system that cannot process "the
grader was wrong" will manufacture false ground truth at exactly the rate
its graders are human. Ours are. So are yours. The receipts exist because
we needed them first.

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
- **We wrote the questions about ourselves.** The seeds come from one
  organization's operational history — ours — so we hold home-field
  knowledge of the domain. The holdout split protects against "has seen
  the questions," not against "the domain is shaped like us." Read the
  three-arm result accordingly: the *relative* delta is mechanistic and
  survives a same-model controlled comparison, but *absolute* scores should
  not be extrapolated to another organization's memory corpus. The real
  fix is external organizations bringing their own runbooks to seed
  same-structure exams — which we will grade and publish. That does not
  exist yet, and we are not going to pretend it does.
- **The operator sells verification, and that is a conflict of interest
  we cannot protocol away in v1.** The question layer is publicly
  auditable; the grading layer is self-runnable; but the question author,
  the answer-key holder, and the party that gets paid for recomputes are,
  today, the same entity. Disclosure is not a structural fix — the
  structural fix is separating exam authorship, grading, and operations
  into different parties, and the first release does not have that. What
  v1 does offer: challenges are free inside the 90-day window (we eat the
  cost), and every grading error we have caught in ourselves is published
  next to the results it wronged. If you trust anything here, trust it
  because you recomputed it — not because we are nice.

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
Yes, this means we get paid for finding FAILs, which is exactly why you
should audit our grader harder than anyone's. The first one is free,
because that is how trust gets bootstrapped in verification markets: not
by claims, but by receipts.

In a stack where models rotate monthly and memory compounds for years, the
durable asset is not the model. It is the receipt.

---

*Disclosure: Assay BC1 is operated by 伊洛科技有限公司 (Nautilus Assay).
All artifacts referenced above are in the public repository:
github.com/chunxiaoxx/nautilus-compass — exam, grader, decision set
(sha256=3b9def7d…), scorecards, errata, recompute reports, and the
three-arm baseline. The author's own grading errors are in there too; they
are not hard to find, and that is the point.*
