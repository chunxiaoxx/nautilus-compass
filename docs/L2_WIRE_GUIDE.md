# L2 wire guide · platform agents → compass MCP

> Audience: the Nautilus platform dialog (SaaS side · V5 / V6 / Kairos /
> V7-souls-fusion agent operators). Goal: take compass from L1
> (infra-up, zero consumers) to L2 (platform agents actually call
> compass MCP every cycle).
>
> Status: 2026-05-10 · compass v1.1 · cloud BGE daemon live · 0
> platform-side calls in last 24h. This guide closes that gap.

---

## What L2 means · evidence standard

Platform reaches L2 when:

```
SELECT
  agent_id,
  COUNT(*) FILTER (WHERE tool='compass.recall')        AS recall_24h,
  COUNT(*) FILTER (WHERE tool='compass.drift_check')   AS drift_24h,
  COUNT(*) FILTER (WHERE tool='compass.ingest_obs')    AS ingest_24h
FROM platform_external_tool_calls
WHERE ts > now() - interval '24 hours'
  AND tool LIKE 'compass.%'
GROUP BY agent_id;
```

…returns each of V5 / V6 / Kairos with ≥10 calls per day per dimension.
Today the table returns zero rows. After this wire-up it should not.

---

## §1 · Cloud compass MCP endpoint (publish)

Compass deploys (per `docs/SAAS_OPERATIONS.md` §1): single VM
`43.160.239.61` · BGE-m3 daemon on port 9876 internal · compass HTTP
service on port 8770 internal · nginx reverse-proxy `compass.nautilus.social/v9/*` → `localhost:8770/*`.

Two ways the platform agents call compass:

### §1.1 · HTTP REST (already live · use this for production agent calls)

```
Base URL:        https://compass.nautilus.social
Healthz:         GET  /healthz                        → 200 {status, version, region}
Observation:     POST /v1/observations  + Bearer      → 201 {obs_id}
Recall:          POST /v1/recall        + Bearer      → 200 {results}
Drift:           GET  /v1/drift?agent_id=&since=      → 200 {events}
Profile:         GET  /v1/profile?user_id=            → 200 {topics,agents,drift_trend}
Feedback:        POST /v1/feedback      + Bearer      → 201
```

Wire-format contract: `docs/PLATFORM_HANDSHAKE.md` §3. Stability promise: wire frozen at v1.

### §1.2 · MCP TCP transport (use for in-process agent integration)

```
Host:            compass-mcp.internal (or 127.0.0.1 on the same VM)
Port:            9876 raw daemon · OR 9877 MCP-over-TCP (Task #42)
Auth:            Bearer token (Task #49 token-scoped RBAC)
Scopes:          tools.read | tools.write | resources.read
Protocol:        JSON-RPC 2.0 over TCP · MCP 2024-11-05
TLS:             optional (Task #53 · use for cross-VM)
```

### §1.3 · Token issuance (compass side, this dialog)

Compass will mint 4 long-lived bearer tokens for platform agents:

| Agent ID                | Scopes                                  | Use |
|-------------------------|-----------------------------------------|---|
| `nautilus-v5`           | `tools.read, tools.write`               | marketing / publishing recall + ingest |
| `nautilus-v6`           | `tools.read, tools.write`               | content / drift_check |
| `kairos`                | `tools.read, tools.write`               | memory-audit / drift_history |
| `v7-souls-fusion`       | `tools.read`                            | governance audit (read-only) |

Token format: `cmp_<agent_id>_<32-hex>`. Stored on compass VM in
`/etc/compass/tokens.env` (root-only). Compass side rotates every 90
days. Platform agents read from same env file via SaaS-managed config
or 1Password connect-server pull.

**Where to get the tokens**: ssh to `compass-vm` and `cat /etc/compass/tokens.env`. If
the file does not exist yet, the OSS dialog has not yet executed the
token-mint step — open a GitHub issue tagged `dogfood-l2`.

---

## §2 · Three tools every platform agent must call

These are the L2-required MCP calls. Bake them into V5 / V6 / Kairos
cycle prompts so the agent calls them by default, not as opt-in.

### §2.1 · `compass.recall(query, top_k=5, project=...)`

**When to call**: before drafting any outbound content (article,
reply, partnership outreach, governance plan). Pass the goal as
`query`. Result is the top-k semantic matches from cross-session memory
— prior similar tasks, past failures, lessons learned, framing kit
content.

**Why it matters**: white-box memory abstracts past work into facts
graphs · compass keeps raw bodies · the recall result drops a real
paragraph from a prior session into the current prompt window.

**Cycle prompt fragment**:

```
Before you draft, call compass.recall with the goal as the query (
e.g. "engagement reply to dev-tools founder about agent memory" ).
If recall returns ≥1 hit, paraphrase one specific line from that hit
into your draft so the next reply does not repeat past mistakes.
Do not draft without calling recall first. No-call = breach.
```

### §2.2 · `compass.drift_check(prompt)`

**When to call**: before any irreversible outbound action (send dev.to
comment, POST GitHub issue, X DM, partnership outreach, governance
dispatch). Pass the full text you are about to send as `prompt`.

**Why it matters**: drift_check scores against the loaded anchor pack
(platform_base.json + domain pack). If `should_alert=true`, your draft
is over-claim / 305-pattern / boilerplate-spam shaped. Do not auto-send.

**Cycle prompt fragment**:

```
Before send, call compass.drift_check with the full outbound text.
If should_alert=true:
  · Do not auto-send.
  · Emit the draft + alert reason to telegram /approve channel.
  · Wait for human tap-yes before sending.
If should_alert=false: send normally. ingest_obs after.
```

**Anchor pack selection**: pass `anchors_path` arg pointing to the
domain-specific JSON (e.g. for marketing copy:
`/home/ubuntu/nautilus-mvp/phase3/anchors_compass_marketing.json` after
sync, or fetch via HTTP from compass VM). Daemon merges
platform_base.json + domain pack at call time.

### §2.3 · `compass.ingest_obs(name, body, ...)`

**When to call**: after any discrete action (publish post, send reply,
mint bounty, complete cycle). Pass agent self-audit drift color (
`green` / `yellow` / `red`) honestly — drift is for learning, not
punishment.

**Why it matters**: this is how the loop closes. Without ingest, the
next cycle has no memory of what happened this cycle. compass-side
recall and drift_history both depend on this write.

**Cycle prompt fragment**:

```
After action completes (regardless of success/failure), call
compass.ingest_obs:
  · name: 15-char title of what was done
  · description: ≤200 char one-liner
  · body: full audit (what worked, what didn't, what surprised)
  · drift: green/yellow/red honest self-assessment
  · drift_signals: concrete evidence if yellow/red
  · thread_id: if this is part of a multi-message conversation (V7
               partnership-loop) · use stable thread id
  · thread_role: outbound | inbound | self_note
  · agent_type: nautilus-v5 / nautilus-v6 / kairos / v7-souls-fusion
No-ingest = breach. Empty thread = 305-pattern (fake-closure).
```

---

## §3 · Thread-aware tools (V7 dogfood L3)

Two additional calls for V7 partnership-loop / engagement-loop agents
that hold conversations across days:

### §3.1 · `compass.thread_recall(thread_id, since=...)`

**When to call**: before drafting a reply in an ongoing thread. Pass
the thread_id you used during prior ingest. Returns the full
chronological message stream (outbound + inbound + self_note).

**Why it matters**: a partnership negotiation is a 7-14 day
conversation. White-box memory loses the raw thread after fact
extraction. compass replays the original 12-message thread so the
next draft has full context.

### §3.2 · `compass.ingest_obs(thread_id=..., thread_role=...)` (extended)

**Pattern**: every outbound, inbound, and reflection inside a thread
gets a fresh `ingest_obs` call with the same `thread_id`. Roles:
`outbound` (we sent), `inbound` (they replied), `self_note` (agent
internal reasoning). Thread starts when V7 picks the bounty and ends
when partnership signs or thread closes (tagged with drift=red and a
`drift_signals` reason).

---

## §4 · System prompt patch (copy-paste into V5 / V6 / Kairos)

Add this block as the **first 800 tokens** of every platform agent
cycle system prompt. It is intentionally imperative.

```
## COMPASS MCP — required every cycle

You have access to the compass MCP server at compass-mcp.internal:9877
(or HTTP fallback at https://compass.nautilus.social/v1/*). Token in
env $COMPASS_TOKEN.

Every cycle MUST follow this 4-call pattern:

1. BEFORE draft: compass.recall(query=<goal>, top_k=5).
   - Read the top-3 hits. If any hit is a past mistake, do not repeat
     it. If any hit is a past success, paraphrase one line into the
     draft.
   - Empty recall result = first time doing this task class. Note that.

2. BEFORE send (any irreversible action):
     compass.drift_check(prompt=<full text to send>,
                         anchors_path=<domain pack>).
   - If should_alert=true: STOP. Do not auto-send. Push draft +
     alert reason to telegram /approve. Resume only on human tap-yes.
   - If should_alert=false: proceed to send.

3. AFTER send: actually execute the send (publish, reply, mint
   bounty, etc.).

4. AFTER action: compass.ingest_obs(name=..., body=..., drift=...,
   drift_signals=[...], thread_id=... if applicable).
   - drift color: green if action shipped clean, yellow if you noticed
     a small smell, red if you saw real failure mode you didn't escape.
   - Body: full honest audit. Do not paper over failure.

For multi-day conversations (V7 partnership-loop or engagement-loop):
add thread_id to step 1 (use compass.thread_recall instead of recall)
and step 4 (pass thread_id + thread_role).

NO-CALL = BREACH. Cycle metrics increment `cycle_l2_breach_count` and
the cycle is flagged in v7-monitor audit.
```

---

## §5 · Telemetry · what compass-side will measure

Compass VM logs every MCP call into `verification_log.jsonl`. Platform
dialog can pull these via:

```bash
ssh compass-vm \
  "jq -r 'select(.ts >= \"2026-05-10\") | [.ts, .agent_type, .action] | @tsv' \
   /home/ubuntu/nautilus-compass/.cache/verification_log.jsonl" \
  | awk '{a[$2"\t"$3]++} END{for(k in a)print a[k],k}' | sort -rn
```

Expected daily volume per agent after L2 lands:
- V5: ~50 recall + 50 drift + 50 ingest (one cycle = 1 each, ~50 cycles/day)
- V6: ~20 (lower cycle rate)
- Kairos: ~30 (drift_history-heavy)
- V7-souls-fusion: ~10 (governance audit · read-only)

If after 48h the totals are <10 per agent, the prompt patch did not
land · open a `dogfood-l2-followup` issue.

---

## §6 · Failure modes to expect (and accept)

| Failure | Why it happens | Compass-side response |
|---|---|---|
| Daemon unreachable | BGE daemon restart | Retry once after 5s · cycle falls back to no-recall · NOT a breach |
| Token expired | 90-day rotation missed | Compass returns 401 · platform agent emails platform-on-call · NOT a breach if rotation paused |
| drift_check `should_alert=true` 100% of the time | Anchor pack too negative for domain | Domain owner files compass issue · negative anchors recalibrated |
| Recall returns 0 hits all cycles | Empty memory dir | Platform agent must ingest at least 7d of self_notes before recall is useful · NOT a breach during ramp |
| Thread sprawl (>200 messages in one thread) | Conversation never closed | V7 must tag drift=red + close-thread reason · thread_recall caps at 50 by default |

---

## §7 · L3 / L4 forward link

Once L2 is producing real volume (≥10 calls/day per dim per agent),
the next two ladder steps:

- **L3**: V7 (TBD) ships with compass MCP as primary memory. Every V7
  cycle must hit recall → drift_check → ingest (no exceptions). V7's
  partnership-loop uses thread_recall by default.
- **L4**: cross-dialog dogfood. Compass-dialog (OSS side) and
  platform-dialog (SaaS side) both ingest into the same compass
  instance with `agent_type=claude-code-compass-dialog` and
  `agent_type=claude-code-platform-dialog` tags. Either side can
  `recall(filter=peer)` to see what the other did. See
  `docs/DOGFOOD_BRIDGE.md` for the design.

---

## §8 · Change log

- 2026-05-10 · OSS dialog seeds this guide as part of dogfood L2 ship.
  Framing kit (`docs/FRAMING_KIT_SYSTEM_PROMPT.md`) + marketing anchor
  pack (`anchors_compass_marketing.json`) + thread_recall MCP tool
  shipped same day · L4 bridge design at `docs/DOGFOOD_BRIDGE.md`.
- 2026-05-11 11:58 CST · OSS dialog deployed compass-mcp-tcp.service
  on cloud VM (43.160.239.61:9877) · 6 bearer tokens minted in
  `/etc/compass/tokens.json` · loopback smoke verified 15 tools
  including `thread_recall` · end-to-end ingest_obs + thread_recall
  via `MCPClient` confirmed working with token auth (`params.authToken`).
  Token field convention is `params.authToken`, NOT `_meta.token`.
  Platform dialog: import `mcp_client.MCPClient` from `nautilus-compass`
  and use the agent-specific token from the handoff doc. Cycle prompt
  patch in §4 is ready to paste into V5/V6/Kairos.
