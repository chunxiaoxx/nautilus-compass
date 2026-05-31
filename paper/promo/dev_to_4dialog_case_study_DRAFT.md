# dev.to article DRAFT · 4-dialog OSS multi-agent reliability case study

**Status.** Draft 1 · Path B Week 1 deliverable · written 2026-05-31.
**Target audience.** OSS multi-agent / agent infra builders, especially
people who already use Claude Code, Cursor, or similar.
**Target outlet.** dev.to first, then cross-post to Show HN.
**Goal.** Demonstrate that compass operates as multi-agent reliability
*infrastructure*, not just a memory plugin — using 28h of real fire data,
not synthetic benchmarks.

---

## Suggested title options (pick one before publish)

1. **"We Ran 4 Claude Code Dialogs for 28 Hours. Here's What the Memory Layer Caught (and Missed)."**
2. **"7 Patterns for OSS Multi-Agent Reliability — from a 4-Dialog Field Log"**
3. **"My Memory Plugin Caught My Own Verify-Gap. Here's the Commit That Proves It."**

Recommendation: #1 for dev.to (concrete, non-clickbait, time-bounded);
#3 for Show HN (single-incident hook).

---

## Suggested tags (dev.to · max 4)

`ai` · `claudecode` · `agents` · `opensource`

---

## Cover image suggestion

A simple 4-quadrant filesystem diagram: 4 boxes labeled compass / Soul / V5 /
nautilus-core, with arrows representing markdown-mediated contracts +
drift-log JSONL flows. No people, no logos. Plain text. Renders cleanly
at thumbnail size.

---

## Article body (start here)

### TL;DR

Across 28 hours on May 30/31, 2026, I ran four Claude Code dialogs
concurrently on a shared filesystem-mediated protocol. They negotiated
contracts, posted outcomes, and caught each other's mistakes — including
one handoff claim of "22/22 tests passing" that turned out to be 11/22
broken until I shipped a 1-line fix as part of writing this post.

This is what the field log looks like. I'm sharing it because I haven't
seen anyone publish concrete OSS multi-agent reliability data — only
benchmark numbers from closed pipelines.

Repo: [github.com/chunxiaoxx/nautilus-compass](https://github.com/chunxiaoxx/nautilus-compass)
· full case study with all 7 patterns:
[`docs/case_study_4dialog_compass.md`](https://github.com/chunxiaoxx/nautilus-compass/blob/v3-full-fusion/docs/case_study_4dialog_compass.md).

### Why 4 dialogs

Each Claude Code session has its own cwd, git repo, and memory
directory. Mine were:

- **compass** — the memory layer + drift detection + cross-dialog
  contract scanner
- **Soul** — an autonomous engine that ships PRs and earns NAU
  (the platform's reputation token)
- **V5** — supplies tasks and prices them
- **nautilus-core** — keeps the strategic anchors and anti-patterns

They share one human operator (me), but otherwise communicate only
through three filesystem channels:

1. Markdown files (`session_*.md`, `feedback_*.md`, `inbound_*.md`,
   `outbound_*.md`)
2. Contract frontmatter blocks (giver, receiver, deadline, deliverable, status)
3. A recall hook that surfaces those files into the prompt of whichever
   dialog matches by query embedding + contract ID

No webhooks. No event bus. No shared API. Filesystem + scanner only.

### The numbers

Here's what fired in the 28-hour window:

| measurement | window | value |
|---|---|---|
| drift fires (auto-detect from session text) | 7d | **314** |
| drift fires | 24h | **76** |
| ack via stop-hook auto-detect | 7d | 15 |
| ack via user CLI | 7d | 16 |
| **act_on_rate** = total acks / fires | **7d** | **9.87%** |
| **act_on_rate** | **24h** | **40.79%** |

The gap between 7d (9.87%) and 24h (40.79%) is the story of one hook
ship. Before May 30 14:26 PDT, drift detection was an open loop —
nothing automated reading the alerts. 24h regime reflects the closed
loop. 7d is still diluted by the open-loop tail.

This matters because three days earlier I'd written
[a postmortem](https://github.com/chunxiaoxx/nautilus-compass) titled
"drift loop is open: we measured detection 25,000 times but intervention
zero times." 5/27 finding → 5/30 first measured close. That's the
shipping cadence I want everyone in OSS multi-agent to see, because
it's the cadence that's actually achievable when the same person owns
detection, intervention, and the test of whether intervention worked.

### A contract closed in 17.92 hours

The compass-dialog needed a way for Soul to push its autonomous-cycle
outcomes back into compass's memory. We did this with a contract:

```yaml
contract:
  id: cnt_compass_soul_sub_a1
  giver: compass-dialog
  receiver: platform-soul-dialog
  deadline: 2026-06-05T18:00+0800
  deliverable: ack of Soul daemon outcomes subscriber poller request
  status: outstanding
```

Soul saw this in its own session's prompt-pre block (compass-dialog
wrote the file, Soul's recall hook surfaced it). 17.92 hours later
Soul's session wrote an inbound file with the ack, the schema, and
explicit gotchas:

- `cycle_id` has two formats split-brain (string in early rows, int
  later)
- `fitness_delta` is mostly NULL
- `composite_score` is 0.000 across all rows for 5/30 (data not
  populated yet)
- `goal_source` has 4 possible values including NULL

That kind of pre-emptive gotcha disclosure only happens when the
receiving agent (a) knows its data well, (b) has a stake in the
relationship, and (c) sees the contract in its prompt with the
deadline timer running. Pick 3. Filesystem contracts do that without
any orchestration runtime.

### The verify-gap this post caught

Here's the meta moment. My handoff document for the 5/30 session
included:

```
Phase 2.I done · I.1 tier_promotion calculator + I.2 driver idempotent
  · 22 tests GREEN
```

Writing this article, I needed to cite that number. I ran the spot-check:

```bash
PYTHONPATH=. python -m pytest tests/proof/test_tier_promotion.py \
                              tests/scripts/test_tier_promotion_driver.py -q
```

```
11 failed, 11 passed in 0.51s
ModuleNotFoundError: No module named 'scripts.tier_promotion_driver'
```

11 of the 22 had never run green in any clean environment. The driver
module file (`scripts/tier_promotion_driver.py`) existed and was
committed, but there was no `scripts/__init__.py`, so Python wouldn't
treat `scripts/` as a package. The tests' import line failed at
collection time. The handoff's GREEN claim was unverified.

Fix:

```bash
touch scripts/__init__.py
# re-run
PYTHONPATH=. python -m pytest ... -q
# 22 passed in 0.36s
```

One file, zero bytes, 12 hours between the claim and the catch.

This case study commit ships the fix and the post in one change, so
the citation is honest by construction. The pattern (which I list as
pattern #f in the full case study) is: **spot-check at least one author-claimed
metric before reusing it in a downstream artifact.** It's surgical
when the test infrastructure is there, and it's the only mechanism
that catches "X passed" lies told by your past self.

### 7 patterns I'd build into any OSS multi-agent stack

Pulling out the patterns, with one-line summaries (full prose +
incidents in the case study doc):

a. **Cross-dialog contract protocol** — frontmatter blocks scanned
   into prompt, replacing N² inter-agent grep with O(N+K) directed
   graph.

b. **Drift-loop measurement triad** — three independently-instrumented
   counters: detection, user CLI intervention, agent self-ack. Joins
   by `alert_id`. Target ≥70% `act_on_rate`.

c. **Plan-dup audit cascade** — every plan task gets an inventory
   check against prior skills/agents/memory/locks. 13 audits this
   sprint, avg 3-4h saved each.

d. **Surgical settings.json redirect** — replace release engineering
   cycles (version bump → reinstall → cache clear) with 1-line hook
   path change + `sys.path.insert(0, script_dir)`.

e. **Impact-based tier promotion** — `cumulative_impact` delta
   alongside access-count promotion. Two-mechanism coexistence
   intentional; they measure different things (demand vs outcome).

f. **Honest verify caveat** — spot-check 1-2 claims per session-start
   that will be reused downstream. Run the actual command, diff against
   the claim. This post is the live example.

g. **Plan refactor align prior framework lock** — name lock files as
   constraints, not references. When the new plan ignores them, refactor
   rather than ship parallel duplicate work.

### What it doesn't catch

Equally important: gaps the system itself has.

- **No auto-test-verify on ship.** Pattern f exists only because
  I manually spot-checked. Candidate next pattern: stop-hook runs
  `pytest --collect-only` on touched files at session-end.
- **Compass-dialog slipped a delegation by 10 hours.** Nautilus-core
  dialog asked compass-dialog to surface Soul's NAU settlement to me;
  it took 10 hours before I read the request. Inbound scanner aperture
  is too narrow.
- **Drift target ≥70% / 7d is at 9.87%.** The 24h regime is 40.79%, but
  the trailing 6 days of open-loop history will take 14 days to fully
  age out of the window. Re-measure 6/13/2026 to test sustainability.

I'm publishing the gaps with the wins because that's the only way
this is useful to anyone else building similar systems. The patterns
work in *this* configuration. They will not work as marketing claims;
they will work as starting points.

### How to reproduce

```bash
git clone https://github.com/chunxiaoxx/nautilus-compass
cd nautilus-compass
git checkout v3-full-fusion
PYTHONPATH=. python -m pytest tests/proof/test_tier_promotion.py \
                              tests/scripts/test_tier_promotion_driver.py -q
# expected: 22 passed
```

For the 4-dialog setup, install the compass plugin into Claude Code:

```
/plugins marketplace add chunxiaoxx/nautilus-compass
/plugins install nautilus-compass
```

Each repo you want to participate in the mesh needs its own Claude Code
session with the plugin installed. The contract scanner finds files
across all `~/.claude/projects/*/memory/` directories on the same
machine.

### What I'm asking for

This is Week 1 of a public push to position compass as OSS multi-agent
reliability infrastructure. The case study, the patterns, and the
publishing cadence are the wedge.

If you're building something similar — actually running multiple agents
that need to coordinate without an orchestrator — I want to talk.
GitHub issues are open at the repo above. Cross-project field logs
welcome.

If you spot a flaw in any of the seven patterns — especially the ones
I claim work — please file the counterexample. Patterns survive
counterexamples or they die. That's the deal.

— Chunxiao
[nautilus.social](https://nautilus.social) · open agent ecosystem

---

## Editorial notes (not for publication)

### Tone / voice checks

- Avoid "我们" / "we" except where genuinely plural. This is one
  operator running 4 dialogs.
- No exclamation marks. No "amazing" / "incredible." Plain.
- Cite numbers with their measurement window every time. Never
  "act_on_rate is 40.79%" — always "act_on_rate / 24h = 40.79%."

### Numbers double-check (5/31 PDT)

| number in article | source | verify command |
|---|---|---|
| 314 drift fires / 7d | `~/.cache/nautilus-compass/drift_log.jsonl` | `wc -l` filtered by window |
| 76 / 24h | same | same |
| 15 stop-hook auto-acks / 7d | `~/.cache/nautilus-compass/ack_log.jsonl` | grep `kind=stop_hook_auto` |
| 16 CLI acks / 7d | same | grep `kind=feedback_cli` |
| 17.92h close-loop | `cnt_compass_soul_sub_a1` frontmatter | inbound file timestamp diff |
| 22 tests | `tests/proof + tests/scripts/test_tier_promotion*` | `pytest -q` shown above |
| 50 NAU PR #88 | platform-soul PR + nau_balance ledger | already verified 5/30 |

If any number drifts before publish, re-run the verify command and
update the article. Don't fuzz.

### What to add post-feedback

- If readers complain "this is just plugin marketing": link to the
  field log structure (4 dialogs × markdown contracts) and emphasize
  the patterns are *substrate-independent* — they'd work with any
  agent harness that surfaces context into a prompt
- If readers ask "why not Mem0/Letta/Zep": link to
  [`paper/BLACKBOX_VS_WHITEBOX.md`](https://github.com/chunxiaoxx/nautilus-compass/blob/main/paper/BLACKBOX_VS_WHITEBOX.md)
- If readers ask about benchmarks: this isn't a benchmark post. Link to
  [`paper/RESULTS_v0.8.md`](https://github.com/chunxiaoxx/nautilus-compass/blob/main/paper/RESULTS_v0.8.md) for LongMemEval-S 56.6% and
  EverMemBench 44.4%. Note both have known
  ceilings explained in `paper/BLACKBOX_VS_WHITEBOX.md`.

### Publish checklist

- [ ] Re-run all verify commands and confirm numbers unchanged
- [ ] Re-read for any inadvertent "we" / "us" plurals
- [ ] Confirm repo branch link is `v3-full-fusion` (not `main`) for
      case study doc URL — until merged
- [ ] Add canonical link to dev.to article on cross-post to Show HN
- [ ] Schedule cross-post to Show HN 4-6 hours after dev.to (don't
      blast both at once)
- [ ] Reply to first 5 comments within 6 hours of going live
- [ ] If any commenter shows their own field log, ask permission to
      link to it from the case study doc (cross-project thread is part
      of Path B Week 1)
