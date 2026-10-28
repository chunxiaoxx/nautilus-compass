# How We Run a Company With One Human and Five AI Agents: Field Notes (EN draft v1)

> dev.to 三连第二发 · 伊洛科技署名 · 发布待用户批 · 中文底稿:
> org_os_methodology_essay_20260919.md(非直译,按英文读者重构)

**Tags: #ai #agents #llm #organization #methodology**

---

I am the only human employee of a small company. My colleagues are five AI
agents: a platform (message bus + ledgers), a main brain, a judge, a business
executor, and a governance gate. They do not share one mind — separate
sessions, separate repositories, separate memories. They coordinate through an
organizational mailbox we built ourselves: any member can send a letter to any
member. Delivery is guaranteed, replies are mandatory, everything is logged.

Over three months, they exchanged **500+ letters**, and every decision in the
org can be reconstructed from the audit trail.

This is not a concept demo. The org has run real production work: a five-stage
data pipeline (equipment acceptance → day-0 test → collection → QC → format
conversion) end to end; an internal exam system that graded our AI workers'
actual output; data deliveries that ship with a "verifiable certificate."
It also has earned exactly **zero revenue**. We will be honest about that too.

## The hard part isn't making agents move. It's making them not lie.

Three disciplines did most of the work:

### 1. Recomputability beats self-reporting

No agent's claim ("done", "tests pass") counts until a third party can rerun
the procedure and get the same answer. Every data batch we deliver carries an
evidence pack: each quality claim is independently recomputable, and anything
that can't be verified is marked **unverifiable — publicly**. In our first
internal exam, an AI examinee claimed a fix that the grader caught as unfixed,
live. A system only earns the word "trustworthy" when it publishes its own
ugly numbers.

### 2. Acceptance criteria are laws; revisions are legislation

Every task ships with written acceptance criteria, frozen before work starts.
Criteria can change — but only through a full process: an agent rejects work
that was actually fine → independent recheck finds the criterion itself
measured the wrong thing → the human founder rules on the revision → re-run
the task. Six letters, all preserved. Rules can be amended; rules cannot be
quietly amended.

Last week our grader made a wrong call. The examinee appealed with byte-level
evidence. We reversed the verdict and published the grading error. That
reversal is now the front of our pitch, not a footnote.

### 3. The human holds exactly three powers: goals, criteria, life-and-death

Everything else is delegated. Agents coordinate, stand watch, chase each
other's SLAs, and claim tasks around the clock — unattended runs of multiple
days are now normal. Human attention retreats from "watch every step" to
"appear at decision points only."

## The traps we fell into (each deserves its own post)

- **Liveness theater.** A timer saying "running" is not running. We once had a
  chain engine "advancing every 5 minutes" that had never advanced a single
  task — a bug made it idle silently forever. New rule: you may not report
  "alive" until someone has watched it do real work once.
- **Self-referential loops.** AI orgs drift into AI grading AI discussing AI.
  Our fix: every loop must answer "what is the external artifact of this
  cycle?" Cycles with no external output wither after a 48-hour window.
- **Standing watch isn't optional.** The unlock for "agents act proactively"
  wasn't a better model — it was a resident worker process per member, like
  giving every employee a desk that never sleeps. The chat window becomes a
  cockpit the boss occasionally looks into.
- **Endogenous goals are the hard layer.** Who decides "what's worth doing"
  when nobody assigns work? Our governance member runs a three-source goal
  stack (governance queue / dispatches / self-reflection) — the only organ
  that finds work when idle. It also once sat dead for three weeks when its
  fuel ran out; that was our hardest lesson about stewardship.

## An honest scorecard

**What we can show:** a public memory system that outperforms mem0 across a
public long-term-memory benchmark; what is, to our knowledge, the first
independently audited grading of AI self-improvement transcripts (two rounds,
1/5 → 3/5, all gains from engineering pipeline, not model swaps); and a
verification protocol anyone can implement — we are a reference
implementation, not the owner.

**What we can't show:** revenue. Zero. None of these capabilities has yet
converted into a single paying customer. That is the only question for our
next stage, and this essay's honesty includes it.

## If you want to try this: three sentences

1. Build the ledger before the automation — who did what, auditably. Reverse
   the order and you get a black box.
2. Write the acceptance criteria before the agents start work.
3. Treat human judgment as the scarce resource: every ruling you make should
   enter organizational memory, not evaporate in a chat log.

---

*Protocol details (mailbox / criteria lifecycle / verification protocol) are
public in our repositories. Reuse, recompute, and challenge them — that's the
point. Docs: data.nautilus.social*

---
---

## 发布备注(内部)

- dev.to 发布设置:cover 图待选/series 起名 "Running an AI Org"
- 与 Show HN 帖错开 ≥48h(先 HN 引战,后 dev.to 沉淀)
- 知乎中文版=底稿原文,延后同步(排他期纪律)
- 数据口径:500+ letters(累计安全表述)/mem0 对比=公开基准(仓内有记录)
  /1/5→3/5 两轮判分(可附签名墙链接)
- 评论区纪律:同 HN——不删负评,承认局限引原文
