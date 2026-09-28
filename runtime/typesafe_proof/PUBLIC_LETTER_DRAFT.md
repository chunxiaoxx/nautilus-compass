# 致 TypeSafe 的复算背书函(草稿 v1 · 待用户批后外发)

> 外发通道建议:Discord builders-chat(我们 9/27 在此发过 BC1 帖,TypeSafe
> 自家社区)+ 邮件(如有)。姿态:同行复现,不树敌。

---

Subject: An independent recompute of your 193.6x/444.6x claim — findings
and one suggestion

Hi TypeSafe team,

We run a small verification shop (Assay, by 伊洛科技有限公司). As our
first public worked example, we put your homepage claim — "193.6x Faster,
444.6x Cheaper based on workflows for System One tasks (proof)" — through
our standard recompute protocol. Method and full artifacts:
github.com/chunxiaoxx/nautilus-compass (runtime/typesafe_proof/).

**What we found:**

1. **The claims are self-consistent with your own published evals.** From
   the per-model triples on evals.typesafe.ai, 444.6x cheaper matches Jev
   vs opus 5 (we compute 440.1x across the four tasks); 193.6x faster
   tracks vs sonnet 5 (183.8x). No inflation detected — and credit where
   due: publishing raw accuracy/cost/time per model is rarer than it
   should be, and your blog's own caveats ("higher end of real world
   gains", shorter inputs) turned out to be accurate self-assessments.

2. **Our independent re-run (64 timed calls, Jev API vs our local
   suppliers) confirms the architecture, not the headline.** Jev's
   latency is flat at 0.44-0.48s whether we ask one question or three,
   short state or long; our fastest local comparison (MiniMax-M2.7)
   ranged 3.7-8.0s on identical questions — a ratio of 7.9-18.2x, not
   193.6x. All three numbers are true at once; which one a buyer
   experiences depends entirely on what they run today. The advantage is
   structural (constant latency; probabilities emitted directly — 69
   output tokens vs 406) rather than accuracy-driven (Jev matches, not
   beats, the frontier on your own charts — we report that too).

3. **Verdict under our pre-registered three-state rule: PARTIAL** —
   reproducible at order-of-magnitude; magnitude is a function of the
   comparator.

**One suggestion:** label the comparison model next to each multiplier
("444.6x vs opus 5"). Your proof link goes to the blog, which goes to the
evals site — a consumer willing to do the work can get there, but the
homepage number is what sticks. One annotation closes the gap between
defensible and self-explanatory.

We'll publish our recompute either way; we'd rather publish it with your
corrections than without them. Reply here, in the builders-chat channel,
or at the repo.

— Assay / 伊洛科技有限公司 (Nautilus Assay)
   github.com/chunxiaoxx/nautilus-compass
