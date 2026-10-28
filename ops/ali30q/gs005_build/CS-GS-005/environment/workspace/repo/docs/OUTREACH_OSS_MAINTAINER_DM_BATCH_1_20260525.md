# Outreach · OSS Maintainer DM · Batch 1 · 2026-05-25

> Paste-ready DMs for 3 verified-active OSS multi-agent maintainers
> Each DM personalized with hook from their RECENT (≤7 day) public activity
> Verification timestamp: 2026-05-25 via `gh api users/<handle>/events`
> Re-verify if sending > 48h after this doc · maintainer activity changes fast

## Anti-pattern reminders (do before sending)

- ❌ Don't mass-send identical text · each DM has personalization hook · keep it
- ❌ Don't include cert URL in first DM unless asked · keep it for follow-up
- ❌ Don't pitch sale · these DMs ask "compare notes" only
- ❌ Don't follow up < 5 days · if no reply at 7+ days · 1 follow-up max
- ❌ Don't send all 3 the same hour · spread over 24-48h to avoid batch-spam pattern

---

## DM 1 · Harrison Chase (@hwchase17) · GitHub issue

**Channel**: New issue on `hwchase17/harbor` (his brand new personal repo · 0 stars · he'll see every issue)

**Why this channel**: bypasses the LangChain org noise · personal-repo signal that you've actually looked at his recent work · highest signal-to-noise.

**Verify before sending**: visit https://github.com/hwchase17/harbor · confirm repo still exists + recent commits. If repo gone or archived · pivot to issue on langchain-ai/deepagents instead.

**Title**: `Multi-agent reliability primitives · comparison notes from another agent framework`

**Body**:

```
Hi Harrison — saw you shipped Harbor 5/22 for agent evaluations + RL environments,
and your 5/01 work on langchain-ai/deepagents. We've been working on adjacent
primitives in Nautilus that might be useful comparison data:

- AST-based semantic-preservation check that catches LLM over-rewrites when
  agents are asked to make small precise edits (catches the false-pass class
  where py_compile + import + ruff all pass but the agent rewrote function logic)
- Engine self-bootstrap last session: dispatched our coding engine via its own
  RAID-2 council pipeline to ship its own context-injection feature (~40 LOC ·
  0 manual edits to the file · all spec'd additions verbatim · evidence in repo)

Curious how Harbor is thinking about:
1. Eval-time semantic regression detection vs runtime regression
2. RL reward signals when agent code edits drift from the original spec
3. Whether agent-output observability is more about traces (LangSmith-style) or
   structural diffs (our angle)

Repo: https://github.com/chunxiaoxx/nautilus-core (MIT · still pre-release)
PR with cycle 12-16 work: https://github.com/chunxiaoxx/nautilus-core/pull/46

Happy to compare notes async via this issue · or 15-min call if useful.

— @chunxiaoxx
```

---

## DM 2 · João Moura (@joaomdmoura) · X DM

**Channel**: X (Twitter) DM to @joaomdmoura · twitter handle verified in his GitHub profile · DMs typically open for crewAI founder

**Verify before sending**: visit https://x.com/joaomdmoura · confirm DM is open (visible "Message" button without follow-required)

**DM body** (≤ 280 chars):

```
Hi João — saw your crewAI commits this past week.
Building Nautilus (github.com/chunxiaoxx/nautilus-core):
RAID-2 council + ast semantic check; engine self-bootstrapped
its own context-injection feature in ~40 LOC last session.
15 min compare-notes on multi-agent reliability?
```

---

## DM 3 · Charles Packer (@cpacker) · X DM

**Channel**: X (Twitter) DM to @charlespacker · twitter verified · he's actively shipping letta-code TODAY (2026-05-25) so very online

**Verify before sending**: visit https://x.com/charlespacker · confirm DM open

**DM body** (≤ 280 chars):

```
Hi Charles — saw letta-code shipping fast today.
Adjacent territory at Nautilus (github.com/chunxiaoxx/nautilus-core):
cross-agent memory (Compass V2 · BGE) + engine self-bootstrap that
shipped its own context-injection feature using its own RAID-2 council.
15 min compare-notes?
```

---

## Reply triage protocol (when any of 3 reply)

| Reply pattern | Your response |
|---|---|
| "Interesting · tell me more" | Send: PR #46 link + cycle 15 self-bootstrap diff highlight + offer 15-min Zoom slot |
| "What's different from LangChain/Letta/CrewAI?" | Send concise 3-bullet differentiation (RAID-2 multi-LLM council · ast semantic check · stake-backed cert · NAU economy) |
| "What's your wedge?" | Honest: "currently OSS reliability primitives · pivoting from earlier audit-as-a-service wedge after Q1+Q2 buyer-side fit analysis" + link WEDGE_PIVOT_DECISION_AUDIT |
| "Show me a real customer" | Honest: "0 paid customer yet · self-pilot cert at nautilus.social/cert/audit_1ff498837701ccd9 marked [SELF_TEST_DEMO]" |
| Silence / no reply at 5+ days | 1 follow-up DM: short · "any thoughts?" · then drop · no spam |
| "Not interested" / "Busy" | Reply: "no worries · thanks for the read · happy to revisit any time" · move on |

---

## Tracking table (fill as you send)

| Date sent | Handle | Channel | Hook used | Reply? | Reply summary | Call scheduled? |
|---|---|---|---|---|---|---|
| | @hwchase17 | GitHub issue · hwchase17/harbor | Harbor 5/22 + deepagents 5/01 | | | |
| | @joaomdmoura | X DM | crewAI 5/20 commits | | | |
| | @cpacker | X DM | letta-code 5/25 active | | | |

---

## Honest expected outcome (calibration · do not over-promise to yourself)

| Sent | Reply rate (cold OSS founder · personalized) | Call rate |
|---|---|---|
| 3 | 1 reply (~33%) typical · could be 0 · could be 2 | 0-1 call from 3 sent |
| If you batch 5+ later | 1-2 replies | 1 call |

**OSS founder cold-DM rule of thumb**: ~30-50% reply when personalized + relevant · but 80% of replies are short non-committal acknowledgment · only ~20% of replies convert to actual call. So 3 sent → 1 reply → 0-1 call → 0-1 ongoing dialog. Anything more is gravy.

**Real ROI is not the call** · is the relationship build over months. 1 acknowledged DM today = warmer reach later if you ship something impressive in 1-2 months.

---

## Send sequence (suggested · avoid batch-spam pattern detection)

| Day | Send |
|---|---|
| Today 2026-05-25 evening | DM 3 (Charles Packer · X · he's online today · highest immediate-reply odds) |
| Tomorrow 2026-05-26 morning | DM 1 (Harrison Chase · GitHub issue · public · async-friendly) |
| Tomorrow 2026-05-26 evening | DM 2 (João Moura · X · spaced from DM 3 by 24h+) |

---

## Next batch (after this batch · fresh-session work)

If batch 1 yields ≥1 reply → write batch 2 with 5-7 more candidates:
- @baskaryan (LangChain contributor)
- @bhancockio (CrewAI dev rel)
- @jerryjliu0 (LlamaIndex)
- @sonichi (AutoGen original creator)
- 2-3 more from verified-active list

If batch 1 yields 0 reply at 7 days → don't scale · debug the hook quality / channel fit / messaging first · maybe pivot to dev.to article + Show HN to attract inbound instead of cold outbound.

---

**Author**: platform-dialog · 2026-05-25 · session ~7h+ · R3 acknowledged · sender (you) does actual sending
