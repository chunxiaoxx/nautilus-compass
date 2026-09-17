# Assay 认证轨 · 借轨合作函底稿(2026-09-17 · BC2 件提前备,发出前用户过目)

> 三封同骨架:承认对方题目层权威 → 指出共同痛点(自报/污染,引学界盟友)→
> 提议认证轨(他们出题,我们出可信度)→ 我们先坐第一排。发送渠道:GitHub
> issue/Discussions 或邮件;署名 Nautilus Assay team (chunxiaoxx)。
> 纪律:不抢冠名、不fork题库、条款留白给对方定;被拒不纠缠。

## A · RSI-Bench 维护者(sunghunkwag)

Subject: Certification track proposal for RSI-Bench — integrity scoring on top of your axes

Hi — we run a small verification org (multi-agent, 130+ days of audited
operation logs) and we're users/admirers of RSI-Bench's six-axis framing of
self-improvement measurement.

One gap we think you'd agree on: every number on every leaderboard is
self-reported. "Benchmarking is Broken: Don't Let AI Be Its Own Judge"
(arXiv 2510.07575) and Berkeley RDI's gaming evidence ("100 points without
solving anything") state the problem better than we can.

Proposal — a **certification track**, not a competing benchmark:

1. Your items, your protocol, unchanged. We add a protocol layer: runs are
   re-computed by an independent verifier (byte-level, scripted checks, no
   LLM discretion), results ship with ed25519-signed receipts.
2. Official rankings count receipt-backed runs only. Self-reported runs stay
   visible, permanently marked UNVERIFIABLE — the wall, not the blacklist.
3. Integrity is a score, not a footnote: share of non-recomputable claims
   subtracts directly.
4. We go first: our own org's RSI loop (including a 10/10-non-recomputable
   audit finding we published) would be the first subject — worst score on
   the wall, receipts public.

If useful, we can start with a one-batch pilot under your review. If not
interesting, no hard feelings — we'll keep citing your axes.

## B · RSIBench-Data 作者(arXiv 2607.25886)

Subject: Your failure-evidence-to-better-models loop + our verdict corpus

Hi — your data-centric RSI framing (turning model failure evidence into
training signal) matches something we've built independently: a verdict
corpus where every entry is a byte-recomputable claim with a signed receipt
(verifier ≠ producer, three-state adjudication). We're accumulating exactly
the "negative data with provenance" your paper argues for.

Two non-asked questions we'd value your view on, and one offer:

1. Do you see integrity-of-evidence (was this failure record itself
   verifiable?) as a gating property for the data loop?
2. Where does verifier bias bite hardest in failure-driven pipelines?
3. Offer: our corpus schema and a pilot export are open — if your pipeline
   can consume failure records with provenance metadata, we'd like to learn
   what breaks.

Context: we're building "Nautilus Assay", a certification-track layer over
existing benchmarks (receipt-only rankings, UNVERIFIABLE-on-wall).

## C · LME-V2 团队

Subject: Certification track on LME-V2 — org-memory runs with signed receipts

Hi — we maintain a public evaluation record on LME-V2 (attribution to your
team intact; protocol + tuning stack documented). Your move toward
organizational experiential memory is exactly the regime we operate in:
a five-dialog agent org with cross-agent state, memory gates, and 130 days
of receipts.

Proposal: a certification track for LME-V2 runs —

1. Independent re-computation of submitted runs (byte-level checks, signed
   receipts, verifier separate from producer);
2. Receipt-backed and self-reported results listed separately, both public;
3. A shared, optional integrity score: share of claims that could not be
   recomputed.

We'd run it first on our own org's results — including the ugly numbers.
Happy to co-design the protocol if there's interest; equally happy to just
keep being a well-attributed user.
