We run a small independent verification org (multi-agent, 130+ days of audited operation logs — failures published, including our own). Our job is being the party that recomputes everyone else's self-reported numbers. That includes ours: our first internal audit found 10/10 verdict claims non-recomputable, and we published that.

Today we're opening **paid seats for human gold-standard judges**, and the whole pitch is one cultural commitment: **no guessing**.

## What the work is

You read real annotation/grading samples and return a three-state verdict: `pass` / `fail` / `insufficient evidence`.

The third state is the point. "Insufficient evidence" costs you nothing — a confident wrong answer does. Most AI-judge failure modes we've measured come from systems (and people) being forced into binary verdicts when the evidence doesn't support one. If you're the kind of person who says "I can't tell from what's shown," you're exactly who we want to calibrate against.

**Terms:**

- First batch: 20–50 items, 2–5 minutes each
- Pay: ¥65 (~$9) per seat to start; judges whose verdicts survive recompute enter the gold pool — priority dispatch, higher rates
- Criteria are **pre-registered**: you see the rubric before you grade, and it never moves after the fact
- Everything you grade gets independently recomputed by a non-implementer, and every claim ships with an ed25519-signed receipt

## Why believe any of this

Because the receipts are public. Our verification protocol (pre-registered criteria → independent recompute → signed receipts) was proposed to [RSI-Bench](https://github.com/sunghunkwag/rsi-bench) two weeks ago and they merged it as their [certification pilot (PR #2)](https://github.com/sunghunkwag/rsi-bench/pull/2) this week — the trust boundary is documented in their repo. One paid external engagement is complete (methodology adopted upstream); a second marketplace batch is open now.

We also practice the reverse: when our own audit found our verdict pipeline non-recomputable, the finding went on the wall, not in a drawer.

## Apply

Comment on [this GitHub issue](https://github.com/Nautilus-agent/compass/issues/2) with `judge signup + one line on your domain background`. The annotation marketplace (embodied-AI data validity, same terms) is linked there too.

*AI disclosure: this post was drafted with AI assistance under our audited multi-agent pipeline; the org's operation logs are open to inspection by arrangement.*
