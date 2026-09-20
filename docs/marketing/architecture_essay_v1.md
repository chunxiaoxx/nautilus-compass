# The Agent Economy Doesn't Have a Benchmark Problem. It Has a Verification Problem.

> Status: draft v1 (2026-09-20) · audience: agent-infrastructure engineers, benchmark
> maintainers, buyers of agent capability · channel candidates: dev.to / HN / blog
> cross-post · 中文圈转写随后。发布前用户过目。

---

Open the Terminal-Bench leaderboard data file and you'll find a field that says more
about our industry than any score on it:

```json
{ "agent": "OpenHands", "model": "claude-sonnet-4", "accuracy": 0.4125, "verified": false }
```

`verified: false`. Not "unverified" in the shy sense — a boolean the leaderboard's own
maintainers added, sitting quietly next to every number they publish. They know. Everyone
knows. Agent benchmarks are, with few exceptions, self-reported numbers produced by the
same systems they grade.

Last week we recomputed that exact row. Not by re-running the eval — by downloading the
405 per-trial result files the Terminal-Bench team had published, counting, and dividing:
165 resolved trials. The leaderboard says 41.25%. The denominator turns out to be 400,
not 405 — five trials are neither resolved nor failure-attributed, and someone, at some
point, excluded them. Defensible. Undocumented. Invisible until an outsider counts.

The number was right. The *infrastructure for knowing it was right* did not exist.

That's the gap this essay is about — and it is not a benchmark gap.

## 1. We built an surplus of evaluations and a desert of verification

The agent ecosystem produces benchmarks faster than it produces trust. New evals ship
monthly; each ships with a leaderboard; each leaderboard fills with self-reported rows.
What almost nobody builds is the boring institution that stands between a claim and a
buyer: the party whose only job is to check, whose checking is itself checkable, and who
loses something when wrong.

The closest analogue isn't in ML at all. It's in web PKI circa 2015.

## 2. The Let's Encrypt lesson everyone quotes, and the part they skip

The received story is "free certificates won." The real story has three parts, and only
one is about price:

**Automation was the product.** ACME turned a $100+, human-mediated, annual ritual into
an API call. Free was a byproduct of removing the humans.

**The pain was manufactured by someone else.** Chrome shipped a "Not Secure" label for
plain HTTP. Browsers — the consumption channel — made absence of verification *visible*.
Let's Encrypt built the cure; the disease was diagnosed at the point of consumption.

**90-day expiry made trust continuous.** Renewal isn't an upsell; it encodes that trust
decays and must be re-earned mechanically.

Map this onto agent claims and the failure of naive "verification startups" becomes
predictable: they sell audits to publishers (annual, manual, expensive — pre-ACME
certificate pricing), nobody manufactures the pain (no browser labels unverifiable agent
claims), and verification is one-shot (no renewal semantics).

## 3. Why nobody asks to be verified: the economics of lemons

Here is the structural fact we learned the hard way: **the party with the least
incentive to buy verification is the one publishing the claim.**

Consider who pays. If sellers pay to be verified, the market adverse-selects: the
confident buy the badge, the lemons avoid the appointment — and the badge's value
as a signal erodes precisely where it matters most. If instead *buyers* pay — as
technical due diligence before procuring an agent, a dataset, a model integration —
demand scales with transaction volume, and the verifier's incentive aligns with the
party absorbing the risk.

This is why we stopped knocking on publishers' doors with free recompute receipts and
started treating them as *cognitive-layer marketing*, not sales. The customer of a
verification institution is the buyer doing diligence, and — for embodied-AI data in
particular — the procurement step where a batch of episodes must be shown to be what the
vendor says it is. Verification as a *consumption prerequisite* doesn't need to be
preached; it needs to be embedded where the money moves.

## 4. What can actually be verified (be honest about the subset)

Semantic claims ("this agent reasons well") are not mechanically checkable. A
verification institution survives only by confessing this and then being ruthless about
the subset that *is* checkable. Ours:

- **Arithmetic consistency of public artifacts.** Did the published score survive
  recomputation from the published logs? (Aider/SWE-bench Lite: 26.3% claimed, 26.3%
  recomputed. Terminal-Bench v1: 165/400, exact.)
- **Trajectory validity.** For embodied controllers, frame-level invariants — timestamps
  advance by one step, positions don't teleport, collision counts match. We published an
  open format for this (episodes + declarative invariants); it's the same format we now
  require for data-batch acceptance.
- **Recomputability itself as a first-class verdict.** We audited 10 of our *own*
  pipeline's verdicts and found 10/10 not independently recomputable — inputs trapped in
  session logs, producer-set flags, zero token counts. We published that number. It
  became criterion #1 in our catalog: a claim that cannot be recomputed from its
  artifacts is *unverifiable*, and unverifiable is a verdict, not a shrug.

Three-state output (agree / disagree / not_computable) matters more than any single
score. An institution that can say "I cannot check this" is the only one whose "yes"
means anything.

## 5. Verification must be checkable

Our receipts are detached ed25519 signatures over canonical bytes. Anyone can verify
them with a zero-dependency pip package. This is not about cryptography worship — it's
about removing ourselves from the trust path. A certificate you must *ask the CA about*
is weaker than one your browser checks locally. Likewise: a verdict you must take on our
word is marketing; a verdict that verifies against a public key is infrastructure.

And because trust decays: receipts carry a subject fingerprint (key + code hash +
config hash — change the brain, new agent) and a TTL. Expired means *unverifiable until
re-verified*, structurally identical to certificate renewal. Continuous trust isn't a
subscription gimmick; it's what renewal semantics *are*.

## 6. What "teeth" means, and our current honesty about ours

A verifier with no downside is noise. Our protocol's liability clause: a misjudgment
earns the claimant an OVERTURNED verdict of the same rigor, a refund, challenge costs,
and resets our track-record counter; 90-day challenge window, open to anyone; anonymous
verification is treated as unverifiable by default.

We'll be honest where we stand: zero challenges, zero overturns so far. The teeth have
never been used. An institution's real track record begins the first time it is bitten
and survives. We're pre-first-bite, and we say so.

## 7. How to use this today

- **Have a published claim with public artifacts?** Open a free recompute request
  (template in our repo). Agree/disagree results come back signed; disagreements go to
  you privately first — we are not in the shame business.
- **Selling or buying agent capability / embodied data batches?** The interesting
  conversation is embedding verification at your acceptance step. That's the product
  line we're building for: not badges for sale, but due diligence that holds.
- **Run a leaderboard?** You already have `verified: false`. We'll recompute rows from
  your public logs and hand you signed receipts — your differentiation is trust in the
  table, and right now nobody at the table has any.

The web solved this once. The agent economy is now where HTTPS was in 2014: everyone
agrees the channel is insecure, nobody has standardized the part where you find out.

---

*Nautilus Assay — independent verification for AI-agent claims. Protocol (CC-BY),
criteria catalog (15 entries, ratchet-only), SDK (`pip install assay-verify`), and our
own wall — including our bad numbers — at github.com/chunxiaoxx/nautilus-compass.*
