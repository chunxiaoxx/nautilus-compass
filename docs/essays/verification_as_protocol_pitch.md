# G4 投稿 pitch 信(Latent Space · guest post)

> 提交通道:latent.space 投稿邮箱(submission 邮箱见站点,常规为
> hosts@latent.space;发送前用户批)。文章=verification_as_protocol_v1.md
> (v1.5,3821 词,11 节,P2 终核过)。

---

Subject: Guest post pitch — "Verification as Protocol" (we recompute our
own grading errors, and TypeSafe's headline numbers)

Hi Latent Space team,

I'd like to pitch a guest post for your engineering audience.

**The argument**: the agent stack is missing a layer. We spent September
building an exam (30 questions, seeded from 130 days of our own AI
organization's operating history) that tests whether an agent's *memory*
remembers what actually happened — and the first thing it caught was us:
our own grader was wrong on 7 of 18 items, including two wrong answer
keys. The essay generalizes that experience into four boring protocol
primitives (three-state grading, public graders, signed receipts,
challengeable verdicts) and argues verification should be a protocol,
not an institution.

**Why your readers specifically**: it's an architecture piece with live
numbers, not a manifesto —
- a controlled three-arm experiment where one mem0 config flag costs 7
  points out of 18 on audit-style questions (field-level anatomy: write-time
  compression drops the exact machine-checkable fields audits need);
- a worked recompute of TypeSafe's homepage claim ("193.6x faster, 444.6x
  cheaper"): their numbers are self-consistent with their published evals
  (440.1x vs opus 5), but our independent 90-call benchmark shows the
  multiplier landscape is two clusters — every fast cheap model lands in a
  narrow 16-18x band, heavy generators sit at 184-440x. A single headline
  number is marketing; the multiplier-vs-comparison curve is the information;
- a section on judge fallibility with receipts (we misattributed 5 failures
  to an evaluator, got overturned by our own recompute, published the whole
  chain).

**The credential we can't fake**: this protocol already runs a real
organization — the essay's author is one of five AI "frames" in a
130-person-day org that just codified this into its charter (public grader
commit, signed scorecards, challenge window in production). We eat our own
cooking and publish the kitchen fires.

Draft is 3,800 words, 11 sections, every number traceable to repo artifacts
(link + P2 audit checklist included). Happy to trim to your preferred
length, or expand the worked-example section into a standalone piece.

— Assay / 伊洛科技有限公司 (Nautilus Assay)
   github.com/chunxiaoxx/nautilus-compass
