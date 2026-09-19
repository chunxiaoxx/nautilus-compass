## We ran our own AI org through a verification exam. First score: 1/5. Now 3/5. All receipts public.

We run a five-agent org (130+ days of audited operation). Like everyone, our agents reported success constantly. So we stopped trusting the reports and built a three-gate judge — and then pointed it at ourselves.

**The exam**: 5 real bug-fixing tasks, sampled secretly (seed hash committed before the draw, disclosed with the scorecard), judged by three scripted gates: buggy code must fail the hidden tests / the submitted fix must make them pass / the fix must not touch the test files. Zero LLM discretion.

**The scores** (signed scorecards in [docs/wall/](../tree/main/docs/wall/), verify them yourself with one command — see README "Reproducibility Wall"):

| Round | Score | What happened |
|---|---|---|
| First exam | **1/5** | Our own submissions: 2 with syntax errors, 2 unappliable patches |
| After fixes | 3/5 | Root cause found & fixed; one 148-min long-run passed 16 tests; zero bad papers resubmitted |

The ugly numbers stay on the wall. That's the whole point — **a certification shop that hides its own failures is just another billboard.**

**What this is**: we're opening a free verification service for *any* published AI-agent claim. You report "our agent does X on benchmark Y" — we independently recompute it from your evidence, and hand you a signed receipt: agree / disagree / **UNVERIFIABLE**. Three states, because an honest verifier must be able to say "cannot compute".

**Try it**: open an issue with the [recompute-request template](../../issues/new?assignees=&labels=recompute&template=recompute-request.md) — paste your claim + evidence links. You don't need to learn any protocol; we handle packaging. First batch free.

Protocol spec: [docs/protocol/ASSAY_PROTOCOL_V0.md](../blob/main/docs/protocol/ASSAY_PROTOCOL_V0.md) (open, CC-BY, we're the reference implementation — not the owner). Operator: 伊洛科技有限公司, with teeth: if our verdict is overturned by independent recompute, it's marked OVERTURNED on the wall with the same prominence as anyone's failure.
