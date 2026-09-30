Hi TypeSafe team,

We're an independent verification lab (Assay). Yesterday we published a public analysis of the performance claims on your homepage ("193.6x Faster, 444.6x Cheaper (proof)") — writing to give you the full right of reply, plus a concrete offer.

What we found (all from your public pages, no behind-the-scenes access):

1. The "(proof)" label is styled text, not a link — no methodology page, no benchmark doc anywhere we could find (and /pricing 404s).
2. Your own on-page demo computes to 171x cheaper and 75x faster — real numbers, but they don't match the 444.6x / 193.6x headline on the same page.
3. To be fair: your "$42 per billion input tokens, 238x cheaper than Claude" claim IS internally consistent (42 × 238 ≈ $10/M matches the public list price). We're not claiming the numbers are false — we're saying they aren't independently checkable today.

The public analysis is here: https://x.com/chunxiaoxx/status/2105296550117458093

Two things we'd genuinely welcome:

1. **Your response.** If there's a methodology doc or comparison set that reconciles headline vs. demo numbers, we'll update our analysis and say so publicly, with the same visibility.
2. **A free independent recompute.** You share the eval config + comparator set (frozen once shared); we rerun it and publish pre-registered criteria, full artifacts, per-claim pass/fail, and every failure sample verbatim. Co-attributed report; you keep errata rights via a 90-day challenge window. It costs you nothing except the config file.

We do this because the whole category — memory layers, decision models, agent infra — currently runs on self-reported numbers, and someone has to sit in the verifier's seat. We made the same offer to mem0 (DolphinBench) and MemTensor/MemOS (OmniMemEval) this week.

Either way, thanks for building in public — Jev's latency profile in our own testing (flat 0.44s across query counts) was the most consistent we measured.

— Chunxiao Wang, Assay · independent verification for AI claims
github.com/chunxiaoxx/nautilus-compass
