# Dogfood bridge · cross-dialog shared compass · L4 design

> Audience: both compass-dialog (this Claude Code session) and
> platform-dialog (the parallel Claude Code session running on a
> separate context). Goal: take dogfood from L3 (V7 agent uses compass)
> to L4 (the human is no longer the message bus between two Claude
> sessions).
>
> Status: 2026-05-10 · design doc · plan A is shippable this month, plan
> B requires Claude Code MCP runtime support for incoming-notification
> handlers.

---

## §1 · The problem we are actually solving

Today 90% of the user's time is relaying messages between this
compass-dialog and the parallel platform-dialog. Both are Claude Code
sessions on the same machine, running in parallel windows. The user is
the human carrier of context between them.

This is the literal definition of "infra-without-consumer" applied to
the *cross-dialog layer*. We shipped:
- MCP protocol (#32 v1.0)
- A2A peer protocol (#47 v1.0)
- Cloud compass MCP endpoint (#84 P1-3)
- Token-scoped RBAC (#49)
- TLS A2A (#53 + #55)

…and we still write things in compass-dialog, the user copy-pastes to
platform-dialog, platform-dialog responds, user copy-pastes back. The
protocols are in place. The plumbing is not.

L4 fixes this in two stages: plan A (shippable now, async/persistent)
and plan B (real-time, requires Claude Code runtime support).

---

## §2 · Plan A · shared compass instance (this month · no Claude Code patch needed)

Both Claude Code sessions ingest into the **same cloud compass MCP
endpoint** with distinct agent_type tags. Either session can recall
what the other did.

### §2.1 · Setup (compass-side · this dialog ships)

1. **Token mint** (compass VM root): `python -m compass.tokens.mint
   --agent-id claude-code-compass-dialog --scopes
   tools.read,tools.write` → `cmp_compass_dialog_<32hex>`. Same for
   `claude-code-platform-dialog`. Both stored in `/etc/compass/tokens.env`.

2. **Both Claude Code sessions configure** `~/.claude/.mcp.json` to
   point `nautilus-compass` at the **cloud** TCP endpoint (not local
   stdio):

   ```jsonc
   {
     "mcpServers": {
       "nautilus-compass": {
         "transport": "tcp",
         "host": "compass-mcp.nautilus.social",
         "port": 9877,
         "token": "<distinct token per dialog>",
         "env": {
           "COMPASS_AGENT_TYPE": "claude-code-compass-dialog"
            // or "claude-code-platform-dialog" on the other session
         }
       }
     }
   }
   ```

3. **Each session's `ingest_obs` writes are tagged automatically** with
   `agent_type=claude-code-compass-dialog` (or platform variant) via the
   env above. No prompt change needed in either session.

### §2.2 · How either dialog reads the other (this dialog can do today)

When this compass-dialog wants to see what platform-dialog did:

```
compass.recall(
  query="<topic>",
  project="C--Users-chunx-Projects-nautilus-core",  // platform's project
  top_k=10
)
```

Filter results by `agent_type` in the frontmatter. Or use
`compass.session_search` with a `query` that matches platform-side
patterns (e.g. "V5 cycle outcome 2026-05-10").

When platform-dialog wants to see what this dialog did, symmetric:

```
compass.recall(
  query="<topic>",
  project="C--Users-chunx",  // compass's project
  top_k=10
)
```

### §2.3 · The async-but-persistent property

Plan A is *not* real-time. Messages do not push from one dialog to the
other. But:

- Anything either dialog writes is persistent in compass memory.
- Either dialog can recall the other's writes on next turn.
- The user no longer needs to copy-paste · they need to nudge the
  receiving dialog to `recall` after the sender writes.
- That nudge is one short message ("see what compass-dialog wrote
  about X"), not the full content. Reduces relay work by ~70%.

### §2.4 · Concrete L4-A flow · azender1 outreach example

1. Compass-dialog drafts reply to azender1 (this turn, already done).
2. Compass-dialog calls `compass.ingest_obs` with:
   ```
   name: azender1 dev.to reply v1
   body: <full draft>
   thread_id: thread_devto_azender1_safeagent
   thread_role: outbound
   agent_type: claude-code-compass-dialog
   ```
3. User pings platform-dialog: "compass-dialog wrote a draft for
   azender1, recall thread `thread_devto_azender1_safeagent`."
4. Platform-dialog calls `compass.thread_recall(thread_id=...)`,
   reads the draft, decides whether to post it via its own send tool.
5. After posting, platform-dialog calls `compass.ingest_obs` with:
   ```
   name: azender1 dev.to reply sent
   body: <url + timestamp + observed reactions>
   thread_id: thread_devto_azender1_safeagent
   thread_role: outbound
   agent_type: claude-code-platform-dialog
   ```
6. Days later when azender1 replies, platform-dialog's inbound monitor
   catches it, ingests with `thread_role: inbound`.
7. Compass-dialog calls `thread_recall` next time it wants to write a
   follow-up · gets the full 4-message thread chronologically.

The user's job in this flow: ~3 short nudges instead of ~3 full
message relays. Lossless context, low effort.

### §2.5 · What this does not solve

- **Real-time interrupts**: if compass-dialog wants platform-dialog to
  stop and address something *now*, plan A doesn't help. Plan B does.
- **Long-running multi-turn negotiations between the two dialogs**:
  plan A is one-shot per recall. If compass-dialog and platform-dialog
  want to design a feature together over 6 messages, the user still
  relays. Plan B fixes this.
- **Off-host dialogs**: if a future third Claude Code session runs on a
  different machine, plan A still works if all share the same cloud
  compass. Plan B needs network listeners.

---

## §3 · Plan B · A2A peer protocol wired into Claude Code (medium-term · needs runtime support)

The A2A protocol shipped in v1.0 (Task #32 / #47 / #55) supports
peer-to-peer messaging between compass instances. To make this usable
from inside a Claude Code session, we need three things that don't
exist yet:

### §3.1 · Required Claude Code runtime extensions

1. **Incoming-notification handler**. When peer A sends an A2A message
   to peer B's compass MCP, B needs to surface that as a system
   reminder or user-message-like injection in the Claude Code session.
   Today MCP `notifications/message` (Task #59) is one-way server→client
   for logging. We need peer-to-client routing.

2. **Stable peer URLs for Claude Code sessions**. Today each Claude Code
   session is a transient process. For A2A to address a peer, each
   session needs a stable peer endpoint (or registration with a
   discovery service).

3. **Async send tool surface**. Compass-dialog calling
   `a2a.send(peer="platform-dialog", message=...)` should not block on
   reply. The reply (if any) arrives as a separate notification on the
   sender side.

### §3.2 · Sketch of the flow (when runtime support lands)

```
compass-dialog (session A)              platform-dialog (session B)
───────────────────────────             ────────────────────────────
| user msg: "ship Y"            |
| → compass-dialog drafts Y     |
| → a2a.send(peer="platform",   |       (B's compass MCP server
|            msg="please review |        receives the message)
|                 Y for me")    |       (B's Claude Code injects as
|                               |        system-reminder: "incoming
|                               |         A2A from compass-dialog")
|                               |       (B reads the message, drafts
|                               |        a review reply)
|                               |       → a2a.send(peer="compass",
|                               |                  msg="review: LGTM
|                               |                       except line 12")
| (A's compass MCP server       |
|  receives the reply)          |
| (A's Claude Code injects as   |
|  system-reminder: "incoming   |
|  A2A from platform-dialog")   |
| → compass-dialog reads, fixes |
|   line 12, ships              |
```

The user is not in this loop. They started it, they see both ends
write to their session, but the handoff happens via A2A. This is the
literal recursive demonstration that compass paper 1 §4 describes.

### §3.3 · Why we're not shipping plan B now

- Claude Code MCP runtime today doesn't surface peer-pushed messages
  as system reminders. Without that, the receiving session never sees
  the incoming A2A.
- Even if we added a polling mechanism (Claude Code calls
  `a2a.poll_inbox` on each turn), the latency would be one turn at
  best. That's better than user-relay (which is multiple turns) but
  not real-time.
- Anthropic's MCP roadmap may add server-initiated client
  notifications in a future protocol version. Until then, plan B is a
  design doc and an A2A protocol implementation we keep current.

### §3.4 · Polling fallback (between plan A and plan B)

A middle path: each Claude Code session, on every turn, calls
`a2a.poll_inbox(since=<last poll ts>)` as the first tool call. If there
are pending messages, they're injected into the session as
system-reminders for the model to address.

This is implementable today on the compass MCP server side · we add a
`tool_a2a_poll_inbox` that reads from
`~/.claude/projects/_a2a_inbox/<peer_id>.jsonl`. The send side writes
to that file. Each session polls on turn start.

**Trade-off**: adds one tool call per turn (~50ms latency) but works
without Claude Code runtime changes. Polling cadence = turn cadence,
not real-time, but typically <1 min latency in active sessions.

Defer to v1.2. v1.1 ships plan A.

---

## §4 · Decision matrix · which plan to ship when

| Plan | Ships | Latency | Effort | Claude Code patch needed |
|---|---|---|---|---|
| A (shared compass) | v1.1 · this month | async (poll-on-recall) | low · 4 hours total | none |
| Polling A2A inbox | v1.2 · next month | ~1 min (turn-cadence) | medium · MCP tool + inbox file format | minor (add tool to session config) |
| B (server-push A2A) | TBD · waits on MCP runtime | real-time | high · needs Claude Code patch | yes |

Recommendation: ship A this month. Watch user pain · if 1-min polling
latency is still too slow, ship A2A polling in v1.2. Only build server-push
A2A when MCP runtime supports it (do not invent custom wire if Anthropic
will standardize this).

---

## §5 · L4 · evidence standard

Plan A reaches L4 when:

```
SELECT
  date_trunc('day', ts) AS day,
  agent_type,
  COUNT(*) FILTER (WHERE action='recall' AND query ILIKE '%peer-dialog%') AS cross_recall
FROM compass.verification_log
WHERE ts > now() - interval '7 days'
  AND agent_type IN ('claude-code-compass-dialog','claude-code-platform-dialog')
GROUP BY day, agent_type
ORDER BY day DESC;
```

…returns ≥3 cross-recall events per day for both dialogs across at
least 5 of the last 7 days. That means: the user is no longer
copy-pasting · each dialog is recalling the other's work directly.

User satisfaction proxy: the user's daily message count to either
dialog goes down by ≥40% week-over-week without project velocity
declining. Measured by `wc -l` on Claude Code transcripts.

---

## §6 · Two open coordination questions

1. **Token rotation**: cloud compass tokens (90 day rotation) cross
   both Claude Code sessions. When OSS dialog rotates, platform dialog
   must update its `.mcp.json` config. Should compass implement a
   /tokens/refresh endpoint so dialogs auto-rotate? Or is a calendar
   reminder enough at this scale?

2. **Project isolation**: today compass-dialog writes to
   `~/.claude/projects/C--Users-chunx/memory/` and platform-dialog
   writes to `C--Users-chunx-Projects-nautilus-core/memory/`. Should
   we add a third shared project (e.g.
   `C--Users-chunx-Shared-Compass-Dialog-Coord`) for cross-dialog
   messages only? Or keep them in each dialog's own project and rely
   on agent_type filtering?

Both questions defer to the first week of plan-A usage data. Run flat,
observe, iterate.

---

## §7 · Change log

- 2026-05-10 · OSS dialog seeds this design doc as part of dogfood L4
  scaffolding. Plan A is shippable this month: 4 hours total
  effort (token mint + 2 `.mcp.json` config edits). Plan B requires
  Claude Code MCP runtime extension that does not yet exist. Polling
  fallback (plan A.5) is the realistic v1.2 ship.
