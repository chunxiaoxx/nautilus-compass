# Show HN submission ready · 4-dialog OSS multi-agent reliability case study

**Status.** Ready to submit. User-action required (I cannot submit Show HN
without HN account API). Submit 4-6 hours after dev.to article goes live
to avoid cross-post timing conflicts.

**Source article on dev.to.** `paper/promo/dev_to_4dialog_case_study_DRAFT.md`
(needs to go live first · 4-6h before this submit).

**Cross-post canonical link.** Use `canonical=true` on dev.to ·
`Show HN: ...` URL points to dev.to article (not the repo case study doc ·
because dev.to drives discussion + author replies).

---

## Show HN title (pick one)

Hard limit 80 characters on HN. Three candidates:

1. **"Show HN: I Ran 4 Claude Code Dialogs for 28 Hours — Here's the Field Log"** (79 char)
2. **"Show HN: Memory plugin caught its own verify-gap (4-dialog field log)"** (71 char)
3. **"Show HN: 7 OSS multi-agent reliability patterns from a 4-dialog field log"** (76 char)

**Recommendation: #2.** Concrete incident hook ("caught its own verify-gap")
is more Show HN voice than abstract pattern claims. Lands the dogfooding
angle in the title. #1 is solid backup. #3 reads too whitepaper-academic.

---

## URL field

```
https://dev.to/<user>/<slug-from-dev-to-article>
```

User to fill the slug after dev.to publish. Make sure dev.to article has
`canonical_url=true` checked so SEO points to dev.to as primary.

Do NOT submit the case study .md from the repo as the URL. Reasons:

- Repo case study is the persistent source-of-truth artifact
- dev.to article is the *discussion surface* with comments + replies
- HN visitors should land where they can engage, not on a static md page

The repo case study link goes in the dev.to article's "Reproduce" section
and in the first comment on HN (next section).

---

## First comment (mandatory · author-context)

Post immediately after submitting (within 30 seconds of clicking submit).
HN ranks first-comment-from-OP highly for context-setting.

```
Author here. Quick context the article doesn't fully spell out:

The 4 dialogs share one human operator (me), but each runs in its own
Claude Code session with its own cwd, git repo, and ~/.claude/projects/
memory namespace. The cross-dialog communication is filesystem-only ·
markdown files with frontmatter contract blocks · a scanner walks all
memory dirs to surface contracts into the right prompt.

No webhooks. No event bus. No shared API. This means the patterns are
substrate-independent · they'd work with any agent harness that surfaces
context into a prompt and writes session transcripts to disk.

The verify-gap (handoff claimed "22/22 tests passing" but 11/22 were
broken due to a missing scripts/__init__.py) was caught by my own
spot-check before citing the number in the article. The fix ships in
the same commit as the article. That's the "honest verify caveat"
pattern (#f in the article) live · the alternative is article + claim +
silent broken state, which is what compass is designed to prevent.

Repo: https://github.com/chunxiaoxx/nautilus-compass
Case study source-of-truth: docs/case_study_4dialog_compass.md
The commit shipping article + fix: f0d5b31

Happy to answer questions about the contract scanner mechanics,
how cross-dialog state stays consistent without an orchestrator, or
specific incidents from the field log. Skeptical questions especially
welcome · patterns survive counterexamples or they die.
```

Length: ~1280 characters. Below the 4000-char HN comment limit, above
the "too short to be useful" threshold.

---

## Timing strategy

| step | when | who | why |
|---|---|---|---|
| dev.to article publish | T0 | user | primary discussion surface · canonical |
| dev.to first 5 replies | T0+0-6h | user | establish thread activity for HN bot |
| Show HN submit | T0+4 to T0+6h | user | not T0 to avoid double-blast feel |
| First comment | T0+4-6h+30s | user | immediately after Show HN URL submit |
| First HN reply window | T+6 to T+12h after Show HN | user | most front-page upvotes within first 4h |
| Cross-project thread (GitHub issue) | T+24h after Show HN | user | only if HN landed front page · else skip |

Do NOT submit Show HN before dev.to has at least 1-2 hours of organic
engagement. HN's algorithm penalizes content that looks like coordinated
cross-post manipulation. 4-6h is the safe window.

---

## What NOT to do

- **Don't ask for upvotes.** HN guidelines explicit. Auto-flag risk.
- **Don't post the same comment multiple times if not visible.** Wait
  10-15 min · then refresh · then post once.
- **Don't argue with downvoters.** Reply factually to substantive
  critique. Ignore vibes-only "this is just marketing" without engaging
  further than one reply.
- **Don't link to compass.nautilus.social hosted gateway in the first
  comment.** HN bias against hosted-service-with-OSS-wrapper framing.
  Lead with repo + case study .md · paid gateway is footer-level.
- **Don't link to the paper2 EverMemBench 44.4% number unless directly
  asked.** This is not a benchmark post. Don't reframe to "compass beats
  Mem0 at LongMemEval" — that's not what the post is about and it picks
  unnecessary fights with white-box memory teams whose comparisons are
  contextual (see paper/BLACKBOX_VS_WHITEBOX.md).

---

## Reply templates for predictable comments

### "This is just plugin marketing."

> Fair to ask. The marketing framing would be "compass beats X at
> benchmark Y." This isn't that — it's a field log of what actually fired
> in 28h of real work, including the gaps the system has and the
> verify-gap the system itself missed. Patterns are documented with
> source code + commit references. If specific data points look like
> marketing rather than evidence, I'll dig into them with you.

### "Why not just use Mem0/Letta/Zep?"

> Different tradeoff. Those projects optimize for benchmark recall on
> closed haystacks (LongMemEval-S leaderboards). compass optimizes for
> drift detection + cross-dialog reliability in long-running real
> sessions. We trade 30 points on LongMemEval-S vs white-box leaders in
> exchange for full-local-deployment + drift-aware behavior. Full
> argument in paper/BLACKBOX_VS_WHITEBOX.md. Use whichever fits your
> actual problem.

### "How is this different from CrewAI/AutoGen multi-agent?"

> Those are orchestration frameworks · one runtime coordinates many
> agent calls. This is a 4-dialog setup where each "dialog" is a fully
> independent Claude Code session (different cwd, different repo,
> different memory namespace) · they coordinate only through filesystem
> writes (markdown + contract frontmatter). No orchestrator. Pattern (a)
> in the article documents the contract protocol that replaces N²
> inter-agent grep with O(N+K) directed scanner. The relevant comparison
> is "agent mesh without orchestration runtime," not "multi-agent
> framework."

### "Where's the benchmark?"

> Not this post. Benchmark numbers are in paper/RESULTS_v0.8.md
> (LongMemEval-S 56.6%) and paper/sections/paper2_06_5_evermembench.tex
> (EverMemBench 44.4-47.3%). Known ceilings + tradeoffs explained in
> paper/BLACKBOX_VS_WHITEBOX.md. The current post deliberately reports
> *operational* data (drift fires, contract close-loop, plan-dup audits)
> rather than benchmark recall, because OSS multi-agent reliability is
> not a benchmark category that exists yet · the post is partly an
> argument that it should.

### "What stops two dialogs from writing conflicting state?"

> Each dialog writes only to its own memory namespace. The contract
> scanner reads all namespaces but is one-writer-per-file. No two
> dialogs share a file as a write target. Conflict detection happens at
> the contract level (one contract has one giver and one receiver ·
> consume by either is unambiguous because filename + frontmatter ·
> id is unique). This works because the operator is one human across
> dialogs · for an n-human + n-dialog setup you'd need a write fence
> (out of scope · the field log is single-operator).

### "How does the drift detector know what to alert on?"

> 25 user anchor sentences + 35 anti-pattern sentences are BGE-m3
> embedded once. Every prompt's last assistant message gets embedded
> and scored as alignment − deviation (cosine sim against anchor set
> vs anti-pattern set). Score < -0.04 OR any anti-pattern hit ≥ 0.538
> triggers R1 (strict self-stop). The numbers are not pulled from the
> air · they come from drift_AUC=0.83 on a held-out set of pre-labeled
> sessions. Detail in recall.py + the drift section of the case study.
> The 9.87% act_on_rate gap to ≥70% target is the open finding · not
> hidden.

---

## Cross-project thread (T+24h conditional)

If Show HN lands front page or top-20 sustained for 6+ hours, post a
GitHub issue on a related project ([anthropics/claude-code · Cline ·
agentmemory] · pick one) titled:

> Cross-project field log: 4-dialog OSS multi-agent reliability patterns

Body links back to the case study + 1-paragraph TLDR + question:
"Are these patterns visible in your project's logs too? Would value a
cross-project field log thread to make OSS multi-agent reliability a
measurable thing."

This is Path B Week 1's cross-project ask. Do NOT post if HN didn't
land · cross-project asks tied to flop'd Show HN look opportunistic.

---

## Path B Week 1 progress accounting (5/31 06:25 PDT)

| Path B Week 1 deliverable | status |
|---|---|
| LICENSE clean | already done (MIT · README footer) |
| README rewrite (or hook for case study) | done (Case study section · +23 lines) |
| CLI v0 (nautilus-compass installable + functional) | already done (PyPI v1.7.x) · CLI command broken in current PATH · noted as separate fix |
| dev.to article | draft ready (paper/promo/dev_to_4dialog_case_study_DRAFT.md) · awaiting user publish |
| Show HN | submission text ready (this file) · awaiting user submit T+4-6h |
| GitHub issue cross-project thread | T+24h conditional on HN landing |

Path B Week 1 ~80% complete · 3 user-side actions remaining (dev.to
publish · Show HN submit · cross-project thread conditional).

---

## Final pre-submit checklist (re-run before clicking submit)

- [ ] dev.to article live (URL retrievable)
- [ ] dev.to canonical_url=true set
- [ ] At least 1-2 hours since dev.to publish
- [ ] No drift in numbers between dev.to article and current verification:
  - [ ] `wc -l ~/.cache/nautilus-compass/drift_log.jsonl` matches article's 314 / 7d
  - [ ] `grep '"kind": "stop_hook_auto"' ~/.cache/.../ack_log.jsonl | wc -l` matches 15 / 7d
  - [ ] tier promotion `PYTHONPATH=. pytest tests/proof + tests/scripts -q` is 22 passed
- [ ] First comment text copy-pasted into HN clipboard (paste within 30s of submit)
- [ ] HN account is in good standing (no recent flags)
- [ ] Time of submit is in 8am-12pm PT window (max HN audience overlap)
