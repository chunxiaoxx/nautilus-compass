## Title
Offering a free independent recompute run for OmniMemEval public results (verification lab, no strings)

## Body

Hi MemTensor team — first, genuine congratulations on OmniMemEval. Multi-session, multi-source, dynamic memory is a hard thing to evaluate honestly, and having a benchmark that stresses cross-session consolidation (rather than single-session retrieval) fills a real gap. We've been using it as a reference point in our own evaluation work.

**Why we're writing**

We run a small independent verification lab (Assay). Our whole job is one thing: making benchmark numbers *reproducible* — pre-registered criteria, full request/artifact archiving, third-party recompute, and a public errata process (append-only, 90-day challenge window). We recently published the protocol details after applying it to our own judge outputs, and it caught real issues in our own pipeline (three classes of self-reported-score failures, all documented).

One thing we've noticed across the memory-layer ecosystem: the numbers that get quoted most (including "35.24% token savings" in the README here) are self-reported by the systems being measured. That's not a criticism — it's the industry default, and honestly disclosed. But it leaves an empty seat: nobody is independently recomputing anyone's numbers.

**What we're offering**

A free, no-strings independent recompute run of OmniMemEval public results:

- You (optionally) share the evaluation criteria + run configuration; we treat them as frozen once shared
- We rerun the evaluation independently and publish: pre-registered criteria, full artifacts, pass/fail per claim, and every failure sample verbatim
- Report is co-attributable (your benchmark + our recompute), and you get the full errata rights via the challenge window
- If a claim doesn't reproduce, we publish that too — that's the deal, it's what makes the verification worth anything

We apply the same bar to ourselves: our own judge corpus (1,454 labeled verdict samples) was independently recomputed with documented methodology, and our first baseline classifier's 66.2% floor is published as-is next to its failure modes.

**Why we think it's worth your time**

Your benchmark is becoming a reference point (rightly). The first system whose numbers carry an independent, reproducible recompute receipt gets to define what "verified" means in this category. We'd rather that be OmniMemEval than a marketing department somewhere.

Happy to share the full protocol spec + a sample recompute report first, if useful. And if the answer is "not now" — no problem at all, the offer stands.

— Assay (independent verification for AI claims; three-state verdict protocol, reproducible receipts)
