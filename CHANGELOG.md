# Changelog

## [1.5.2] · 2026-05-13 — "self-verify caught fake-closure · 3 gates"

Patch over v1.5.1. Self-verifying v1.5.1 surfaced one fake-closure
(numeric_claims hook ran 0 times because age_gate skipped) plus two
secondary issues. v1.5.2 ships three real gates; one (drift_check
in stop_hook) is deferred to v1.5.3 pending local BGE daemon wiring.

### #1 · stop_hook 24h glob ingest (was: latest-only + age_gate)

`stop_hook.py` now scans every `session_*.md` from the last 24h
(via new `recent_session_memories(within_hours=24)` helper) and
ingests numeric_claims for any not yet seen by `already_ingested`
(jsonl source-path dedup). The age_gate still applies to strategy
matching only, not to numeric_claims.

Real effect: jsonl `~/.cache/compass/numeric_claims.jsonl` went
from 2 → 17 records on first run · 9 new sessions covered · 7
distinct sources. Single-latest-only path missed 15 records.

### #2 · numeric_claims reverse regex + frontmatter seed helper

`numeric_claims.py` PATTERNS extended with reverse forms
(`entries:1076`, `agents=4`, `tools: 22`) plus new
`_parse_seed_block()` extracting from yaml `numeric_claims_seed`
list in frontmatter.

Validation: fixture with 5 seed strings → 4/5 matched (entries 56,
port 8770, agents 4, tools 22). Fifth ("pos 28 neg 28 anchors")
intentionally not matched · `pos`/`neg`/`anchors` not registered
high-value entities. Self_verify session frontmatter helper found
0 matches because seed text was placed in body, not frontmatter
(my own process bug, not plugin bug).

### #3 · ASCII alert · safe on GBK consoles

`recall_start` cross_ref alert no longer embeds non-ASCII glyphs
(替换 unicode 三角 → `[!]` 符号 + ASCII 文本). Avoids
`UnicodeEncodeError` on Windows GBK terminals when the alert
prints during recall banner injection.

### #4 · drift_check in stop_hook · DEFERRED to v1.5.3

Wiring drift_check HTTP into stop_hook needs local BGE daemon
ready + compass_http auth setup. Local daemon was loading at ship
time. Not blocking · the 3 gates above ship clean.

---

## [1.5.1] · 2026-05-13 — "data hygiene · 4 signal gates"

Patch over v1.5.0. Four small gates that tighten recall signal
after 12 days of real dogfood showed the plugin was drowning in its
own session flow.

### #1 · Importance gate (write-side)

`session_*.md` files now require `drift: red` frontmatter to enter
the recall index. `feedback_*` / `reference_*` / `anchor_*` bypass
the gate (explicit user intent → always keep).

Real effect: `C--Users-chunx` project 767 → 56 entries (−92.7% noise).
`recall_start` banner now displays the real count.

### #2 · numeric_claims hook (anti-hallucination)

New `numeric_claims.py` with 5 regex patterns (entries / percentage /
agents / tools / port). `stop_hook` ingests at session close to
`~/.cache/compass/numeric_claims.jsonl` (append-only audit log).
`recall_start` cross-references the next query: if the query
contains a number for the same entity that disagrees with the
14d-recent history, a `cross_ref alert` is embedded in the recall
banner.

Real trigger observed: query mentioning `9999 entries` +
`100 agents` fired 2 alerts against the last session's `56 entries`
/ 25+35 anchor claim.

### #4 · Query expansion (read-side)

`query_synonyms.json` · 18 high-frequency keys · on key match,
append up to 8 synonyms to the query before BGE embedding.

Example: `"daemon 挂了"` →
`"daemon 挂了 | 守护进程 BGE 9876 9877 systemd"`.

Real effect: top-5 for that query now includes sessions that only
used "守护进程" (Chinese) — would have missed under the literal
"daemon" token. daemon-related hit scored 0.553.

### #5 · archived_at decay

Sessions older than 30 days drop from the candidate pool unless the
query contains a history keyword (`历史 / 曾经 / 旧 / archive / old /
history`). All current sessions < 30d so the trigger path is
deployed but not yet firing.

### Dropped

`loop_anchor` drift gate (originally planned as #3) cut. Plugin has
no hook surface into `/loop` iteration state so the proposal was a
phantom need.

### Files

- `recall.py` · importance gate (filter during index build) ·
  `_expand_query()` + synonym-file loader · archived_at filter.
  +92 lines.
- `stop_hook.py` · `ingest_numeric_claims(session_md)` call at
  session close. +9 lines.
- `numeric_claims.py` · new · 5 regex patterns ·
  `ingest_numeric_claims` + `cross_ref_numeric_claims` + JSONL audit.
- `query_synonyms.json` · new · 18 keys mapped to synonym lists.
- Version: `pyproject.toml` / `__init__.py` / `recall.PLUGIN_VERSION`
  aligned to **1.5.1** (were drifting at 1.2.0 / 0.9.5 / v0.7 ·
  this release closes the version-drift debt).

### Why a patch, not a minor

All four gates are data-hygiene tuning of the same surfaces shipped
in v1.5.0 (write path, recall path). No new tool, no new protocol,
no new MCP method. Clean `X.Y.1` bump.

### Migration

None. Drop-in. Existing session files re-indexed on next daemon
rebuild (~30s).

---


## [1.5.0] · 2026-05-11 — "proof-of-recall · protocol-level fake-closure killer"

Same day as v1.4. Ships S2 from `specs/SPEC-S2-proof-of-recall.md`.

### S2 · Proof-of-recall protocol

`recall` now returns a `recall_token` (16-hex nonce · 30 min TTL · 1000-entry
LRU). Subsequent `ingest_obs` can pass `recall_token` + `cited_snippets`:

- validation: agent_type match · token live · ≥1 cited string overlaps a top-3
  entry (path basename OR ≥20-char description overlap)
- result written to session_*.md frontmatter as
  `proof_of_recall: pass | fail | not_attempted`
- failure modes (advisory · never blocks):
  - `no_token_provided` · `token_not_found_or_expired` · `agent_type_mismatch`
  - `empty_cited` · `no_snippet_overlap` ← the smoking gun for P1-1 pattern
- backward compatible: omit both args → `not_attempted` · old clients no break

### Why this matters

Kills the P1-1 / 305 fake-closure mode at protocol level:

```
before: recall → agent ignores → ingest "done" → cron catches hours later
after:  recall → agent must quote top-3 → ingest validates → frontmatter records
        → dashboard groups by proof_of_recall → fake_closure has zero-latency signal
```

### Files

- `mcp_server.py` · in-memory token store · `_mint_recall_token` + `_validate_recall_proof`
  · hooked into `tool_recall` (mint on hit) and `tool_ingest_obs` (validate)
  · SERVER_VERSION 1.4.0 → 1.5.0
- `tests/test_proof_of_recall.py` · 10 unit tests (token TTL, LRU, validation paths)
- `tests/test_proof_of_recall_e2e.py` · 5 E2E tests (recall → ingest round-trip)
- `docs/PROOF_OF_RECALL.md` · protocol spec · migration timeline (v1.5 advisory →
  v1.6 conditional reject → v2.0 hard enforce) · self-dogfood note

### Tests

```
tests/test_proof_of_recall.py:     10/10 PASS
tests/test_proof_of_recall_e2e.py:  5/5  PASS
```

### Tool surface

ingest_obs schema gains 2 optional args (`recall_token`, `cited_snippets`).
Other 14 tools unchanged.

### Migration

v1.5 is advisory only · no agent code change required · all existing flows work.
Clients that opt in get a fake-closure receipt in the session frontmatter.
v1.6 will start rejecting agents with > 20% fail rate over 24h (TBD).

---

## [1.4.0] · 2026-05-11 — "cross-project recall · L5 dispatch protocol · L2 gate alarm"

Same day as v1.3. Three additions that don't depend on platform-side
wiring (so they ship now while platform L2 evidence gate is still empty):

### S3 · Cross-project recall (`scope` parameter)

`compass.recall()` now accepts `scope` argument:

- `scope="project"` (default) · current behavior · single project memory
- `scope="user"` · union across all projects under `~/.claude/projects/`
  (excluding `_*` platform internals) · same user · cross-language ok
  (BGE-m3 multilingual)

Wired in `daemon.py` via new `_list_user_project_dirs()` helper and a
union-then-score loop. `mcp_server.py` forwards the param. Per-result
`project` field tagged so callers see which project each hit came from.

Smoke verified on cloud daemon (2 projects · `C--Users-chunx` + `default`):

- backward compat: no scope arg → defaults to `project` (existing behavior)
- scope=user: scans both, returns 5 hits with origin tags
- invalid scope: rejected with helpful error
- warm-cache perf: 1.07x avg vs scope=project (well below 30% target)
- cold-cache first run: 2.16x · acceptable since BGE embed dominates

Use case white-box can't do: lessons from nautilus debugging (305-case,
P1-1 fake-closure) auto-surface when writing in chunx or zenmind project.
Entity-graph systems can't union entities across unrelated codebases;
black-box embedding union just works.

### specs/ · Dispatch protocol for L5 dogfood

Four new docs in `specs/` (committed but no GitHub issue yet · waiting
for L2 evidence gate to be hit):

- `DISPATCH_PROTOCOL.md` · how platform agents pick up compass upgrade
  specs · 5-condition review gate · drift_check + proof-of-recall
  required in every PR body
- `SPEC-S1-anchor-learner.md` · weekly cron auto-tune anchors_*.json
  based on FP/FN signal · suggested owner V5 · 3 days · NOT dispatched
  yet
- `SPEC-S2-proof-of-recall.md` · protocol-level kill of P1-1
  fake-closure mode · recall_token nonce + cited_snippets validation ·
  high-risk so self-implement · 5 days
- `SPEC-S3-cross-project-recall.md` · implemented in this release

### ops/ · L2 evidence gate Telegram alarm

`ops/monitor_l2_evidence_gate.{sh,py}` cron (every 6h) reads
`/var/log/compass-l2-metrics.json` (from `compass_l2_metrics.py`),
tracks per-agent consecutive-miss streak, alerts Telegram if any of
nautilus-v5/v6/v7-souls-fusion/kairos misses 3 consecutive 6h windows
(= 18h continuous miss). 24h cooldown per agent to avoid spam.

Reason: v1.0 → v1.3 has been shipping infra fast, but verification_log
shows zero platform-side calls (V5 = 0, V6 = 0, V7 = 0, Kairos = 0 in
the last 7 days). This is the same fake-closure pattern as 305-case
and P1-1. The alarm now catches it in 18h instead of via human review.

Hard gate: SPEC-S1 will NOT be dispatched to V5 until V5 hits ≥10
calls/day for 3 consecutive days. Documented in
`specs/DISPATCH_PROTOCOL.md` §0.

### Tool surface

15 → 15 (no new MCP tool · just new `scope` arg on `recall`).

---

## [1.2.0] · 2026-05-11 — "dogfood ladder · thread recall · cloud MCP TCP"

Two days after `v1.1.0`. Closes the "infra-without-consumer" gap: v1.0
shipped MCP / A2A protocols and a token-authed TCP server, but in the
72 hours after launch zero platform-side agents called any compass MCP
tool. v1.2 fixes this with a 5-level dogfood ladder, a thread-aware
recall primitive for multi-day partnership / engagement loops, and a
cloud MCP TCP deployment that ships verified end-to-end. Tool surface
14 → 15.

### Dogfood ladder · structural fix for cross-agent consumption

Introduced the dogfood ladder evidence model (`docs/L2_WIRE_GUIDE.md`,
`docs/DOGFOOD_BRIDGE.md`) — five distinct levels with distinct
evidence standards:

- **L0** · platform solo cron · today's baseline
- **L1** · compass MCP endpoint live · zero platform-side calls (the
  bad state · same anti-pattern as 305-case "shipped but never
  consumed")
- **L2** · platform agents (V5 / V6 / Kairos) call compass MCP
  recall + drift_check + ingest every cycle · evidence: ≥10 daily
  calls per agent in `verification_log.jsonl`
- **L3** · V7 (TBD) compass-first · every cycle =
  recall → draft → drift_check → send → ingest
- **L4** · cross-dialog · compass-dialog and platform-dialog ingest
  into the same cloud instance · either side recalls the other's work

Ship targets L2 ready (wire guide + 6 minted tokens + cloud endpoint
live + cycle-prompt patch documented) so the platform side can move
from L1 to L2 without re-designing anything.

### `thread_recall(thread_id)` · multi-day conversation recall (L3 enabler)

New MCP tool · v1.2 tool count 15. Returns the chronological message
stream for a long-running back-and-forth tagged with a stable
`thread_id` frontmatter field. Whereas `recall` does semantic top-k
across all memory, `thread_recall` returns the full ordered sequence
for one thread.

Use case: V7 partnership-loop. An agent talks with a founder over
7-14 days across many messages. White-box memory abstracts these
into facts and loses the raw thread — compass keeps raw
`session_*.md` per message tagged with `thread_id`, so the next
reply draft has the full 12-message history reconstructable.

Companion change to `ingest_obs`: two new optional inputs
`thread_id` (stable id, e.g. `thread_devto_azender1_safeagent`)
and `thread_role` (`outbound` / `inbound` / `self_note`). When set,
frontmatter records them so `thread_recall` can filter.

End-to-end verified via `MCPClient` → `compass-mcp-tcp.service` →
BGE daemon → memory dir on cloud VM (`session_20260511-1200_L2-E2E-smoke.md`).

### Cloud MCP TCP endpoint · `compass-mcp-tcp.service`

New systemd unit at `ops/compass-mcp-tcp.service`. Deploys the MCP
TCP server on the compass cloud VM, bound to `127.0.0.1:9877`.
Loads bearer tokens from `/etc/compass/tokens.json` (0640 root:ubuntu).

Why loopback-only: even with token auth, exposing MCP TCP to the
public internet means tokens travel in cleartext. Platform agents
on the same VM use loopback directly; cross-machine dialog Claude
Code sessions use SSH tunnel:

```
ssh -fN -L 9877:127.0.0.1:9877 cloud
```

Then either dialog can register `nautilus-compass-cloud` in
`~/.claude.json` mcpServers and call compass tools natively.

Six bearer tokens minted (nautilus-v5, nautilus-v6, kairos,
v7-souls-fusion read-only, claude-code-compass-dialog,
claude-code-platform-dialog) with token-scoped RBAC (tools.read,
tools.write).

### `ops/mcp_stdio_to_cloud.py` · stdio → cloud TCP wrapper

50-line Python wrapper that lets Claude Code's stdio MCP transport
talk to the cloud TCP MCP server. Reads JSON-RPC from stdin, injects
`params.authToken` from `COMPASS_CLOUD_TOKEN` env, forwards to cloud
over TCP, streams responses back to stdout (bytes-level · works
around Windows GBK encoding).

Setup once in `~/.claude.json` mcpServers and any Claude Code
session can call compass tools natively, no more
`subprocess.run python -c "from mcp_client import ..."` boilerplate.

### `anchors_compass_marketing.json` · 31 + 37 anti-overclaim pack

New domain anchor pack for drift_check on outbound marketing copy.
Borns from the 305-case + P1-1 case (two over-claim incidents in
24 hours · 2026-05-09 and 2026-05-10).

- 31 positive anchors: honest factual framing (black-box vs white-box,
  the four published numbers, architectural ceiling caveat, no
  "industry SOTA")
- 37 negative anchors: over-claim language (industry SOTA, zero token,
  100% recall, dead competitors, hype words, generic CTAs,
  305-pattern fake-closure)

v1.1 calibration round 1 (2026-05-11) sharpened the 305-anchor and
100%-recall-anchor to absolute-claim phrasing after a baseline run
on a real azender1 dev.to reply draft showed 4/5 paragraphs
false-positive should_alert. After calibration: 2/5 false positives.
Calibration is an iterative process · future rounds will track
true-positive vs false-positive rates from real outbound to
auto-retrain anchor weights.

### `docs/FRAMING_KIT_SYSTEM_PROMPT.md` · ~1500-token agent system prompt pack

Loaded as the first part of any agent system prompt that writes
public-facing compass copy (V5 marketing cycle, V6 content gen,
V7 engagement / partnership-loop). Locks in the four published
numbers (56.6 / 44.4 / AUC 0.83 / $3.50), the architectural
identity (only public memory layer with zero LLM extraction at
index time), and the 10 "what you must NOT claim" rules. Pairs
with `anchors_compass_marketing.json` for post-generation drift_check.

### Tool surface

14 → 15 MCP tools. New: `thread_recall`.

`ingest_obs` gains two optional inputs (`thread_id`, `thread_role`)
without changing required-args contract.

### Verified ship evidence (2026-05-11 11:58-13:06 CST)

- Cloud `compass-mcp-tcp.service` active (running) on 127.0.0.1:9877
- 6 tokens loaded from `/etc/compass/tokens.json` · token auth
  verified (`params.authToken`)
- 15 tools listed via `tools/list` · `thread_recall` present
- `ingest_obs(thread_id='thread_L2_dogfood_verification', ...)` →
  `thread_recall` round-trip · full body returned in chronological
  order
- 3 dogfood session lessons ingested to cloud via local Windows
  → SSH tunnel → cloud MCP TCP · platform-dialog token simulated
  recall returns those 3 hits cross-dialog (federation verified)
- `drift_check` on azender1 reply draft (5 paragraphs) returned
  real signals with FP at 2/5 after v1.1 anchor calibration
- Git commits `0ee5bb0` (5 ship files), `4385a68` (ops wrapper +
  127.0.0.1 rebind), this release (anchor v1.1 + CHANGELOG)

### Coordination with platform dialog

Tokens and cycle-prompt patch handed off to platform dialog via
`_compass_tokens_handoff.md` (gitignored). Platform-side next:
update V5 / V6 / Kairos cron system prompts with the 4-call cycle
pattern (recall → drift_check → send → ingest), add
`helix.compass_call_count_24h` metric. L2 evidence gate: ≥10 daily
calls per agent in 48 hours.

### What's not in this release

- v1.2 ship of A2A polling tool (cross-dialog real-time messaging)
  · waiting on Claude Code MCP runtime extensions or polling
  fallback in v1.3
- V7 itself (compass-first super-agent) · waits on L2 evidence
  showing platform agents really consume compass MCP daily
- Outreach drafts to `@max_quimby`, `@andreap`, `@supertrained`
  · waits on raw comments
- arxiv moderation: papers 7569111 + 7570898 still in queue
  (Monday morning UTC · normal weekend hold)

## [1.1.0] · 2026-05-09 — "recall consumption fix · V7 v0.2 governance plan"

Released 12 hours after `v1.0.0`. Three production bug fixes around recall
consumption that were exposed by a sister-agent post-mortem, plus a new
capability-driven governance layer (V7 v0.2) and a session-recovery
utility. Tool surface 10 → 14.

### Recall consumption · the failure mode this fixes

Recall today returned title + 120-char description per hit. Agents
skimmed labels (e.g. "audit-gate / xhs-cards-embed / wxid"), assumed
they had consumed the memory, and acted without ever reading the body.
Same anti-pattern reproduced across sessions despite recall hitting the
exact right files. Fix is three layers:

- **v0** (recall.py) · top-3 hits in both metadata and vector mode now
  embed first 800 chars of post-frontmatter body in an indented `│`
  block. Agent gets actual rules in working context — no extra `Read`
  tool call required to consume.
- **v1** (recall.py) · anti-anchor alerts now embed past-mistake body
  via two-tier match: substring 6-gram against the anchor + lesson
  concept frontmatter (Tier 1, precise), falling back to recent
  `drift!=green` sessions (Tier 2, the agent's own self-reported slips).
  Alert is now actionable, not just a label.
- **v2** (`recall_consumption.py` · new module) · detects "recall fired
  but never `Read`'d" drift signal. Walks back to the N-th most-recent
  recall block in the session jsonl, extracts paths, checks subsequent
  assistant turns for matching `Read` tool_use. Surfaces in `drift_check`
  MCP tool result (independent of BGE daemon · runs even when daemon
  unreachable) and in `mid_session_hook` every 25 tool calls (only nags
  when ≥3 unconsumed and ratio < 0.3). Verified on a 130MB session: 41
  recall hits surfaced, 0 consumed.

### V7 governance v0.2 · capability-driven plan (no templates)

`v0.1 governance_dispatch` was a fan-out router · static dict mapping
channel → executor. SaaS dialog correctly pushed back: template libraries
can't cover the long tail of industries.

`v0.2 governance_plan` (new MCP tool) replaces the template approach by
reading two registries instead of carrying logic in V7:

1. `~/.claude/projects/_platform_registry/agents_capabilities.json`
   (live · platform exports) · falls back to bundled
   `examples/v7_default_capabilities.json`
2. `~/.claude/projects/_platform_registry/anchor_packs_phases.json`
   (live · platform exports) · falls back to bundled
   `examples/v7_default_phases.json`

For each phase, V7 finds the best-scoring executor by capability match
(+10 capability id, +5 domain match, +3 anchor pack match). Adding a
new vertical = 1 row in `platform_anchor_packs` (phases JSONB) + 1 row
in `platform_agents.metadata.capabilities[]`. Zero V7 source change.

Demo verifies two domains: `marketing/dev-tools` (4-phase DAG → V5)
and `caishen-finance/audit` (5-phase DAG · V6 wins for `numeric-audit`
because V5 doesn't declare it · V5 takes write+publish).

Full schema in [`docs/PLATFORM_HANDSHAKE.md`](docs/PLATFORM_HANDSHAKE.md) §9.
Platform-side has 4 new wires to ship (capability export, phases ALTER+
export, DAG-aware minting, telegram `/plan` command) tracked in §9.4.

### New utility · session image surgeon

`scripts/session_image_surgeon.py` recovers a Claude Code session that
the API rejects with `400 Could not process image`. Stream-validates
every base64 image (magic bytes + size + Pillow verify), replaces only
the bad ones with a text placeholder, preserves all other content.

Used today to unstick a 130MB / 32914-line session: 45 images total,
44 valid, 1 corrupted ("PIL Truncated File Read"). Session resumed via
`claude --resume <sessionId>` with full context intact.

### Tool surface

10 → 14 MCP tools:

- New: `governance_plan` (V7 v0.2)
- Already in v1.0: `recall`, `drift_check`, `ingest_obs`, `drift_history`,
  `session_search`, `profile`, `feedback_log`, `long_task`,
  `submit_platform_task`, `ingest_platform_task_result`,
  `governance_dispatch`, `governance_audit`, `governance_lock_check`

### Compatibility

- Backward compatible with v1.0.0 callers · all v1.0 tools have
  unchanged signatures
- `recall` response shape extended (extra body lines under existing
  hits) · downstream parsers tolerant of header-style listings still
  work
- `drift_check` output may now include trailing consumption block ·
  parsers should tolerate optional trailing sections

### Files changed

- `recall.py` · v0 + v1 (body embed + lesson finder)
- `recall_consumption.py` · NEW · v2 detection module
- `mcp_server.py` · `governance_plan` tool + drift_check consumption hook
- `mid_session_hook.py` · periodic consumption check
- `examples/v7_default_capabilities.json` · NEW
- `examples/v7_default_phases.json` · NEW
- `examples/v7_governance_demo.py` · + step 5 v0.2 plan smoke
- `scripts/session_image_surgeon.py` · NEW
- `docs/PLATFORM_HANDSHAKE.md` · §9 added
- `governance.lock` · refreshed (recall.py is L0)

### Eval headlines (unchanged from v1.0.0)

LongMemEval-S 56.6% (n=500) · EverMemBench-Dynamic 47.3% (n=497, run 2) ·
Drift detector ROC AUC 0.83 (held-out) · Reproduction cost $3.50.

---

## [1.0.0] · 2026-05-08 — "stable · promote rc2 verbatim · repo public"

`1.0.0-rc2` (2026-05-07) ships unchanged as `1.0.0`. No code or test
changes since rc2; this entry exists to mark the stable cut and bump
version strings (`pyproject.toml`, `package.json`, `.claude-plugin/plugin.json`,
`mcp_server.SERVER_VERSION`) from `1.0.0-rc2` to `1.0.0`.

The full feature surface — MCP A2A protocol with TLS/mTLS, per-token RBAC,
per-token rate limiting, auto-reconnect client with `-32029` backoff,
`resources/*` for session-log streaming, `notifications/{progress,cancelled,message}`,
`logging/setLevel`, third-party stdio shim, plus the slash-command plugin
surface — is unchanged from rc2 and is documented below under that entry.

The repository went **public** on 2026-05-08 — code, anchors, frozen
test data, and audit-log tooling are MIT-licensed (CC0 for anchor files)
at https://github.com/chunxiaoxx/nautilus-compass.

### Eval headlines (locked)

- LongMemEval-S n=500: **56.6%** (v0.8 · 2026-05-04 lock)
- EverMemBench-Dynamic n=500: **44.4% (Run 1)** / **47.3% (Run 2, n=497)** ·
  cross-run mean **45.84%** · 95% CI on Run 2: [42.9%, 51.7%] (B=10000 bootstrap) ·
  tops every reported Table 4 baseline (Mem0 37.09, Zep 39.97, MemOS 42.55)
- Cross-judge sensitivity (Gemini 2.5 Pro on stratified n=100 of Run 2):
  DS V4-flash 42.0% · Gemini 2.5 Pro 28.0% · Cohen's κ = 0.70 · 14
  asymmetric DS=Y/Gemini=N disagreements · honest range [28%, 42%],
  balanced-judge mid ~35-40%
- Drift detector: **AUC 0.83** held-out (50/50 aligned/deviation, 2026-04-29) ·
  0.92 in-set
- V4-pro full-500: **56.4%** (-0.2 vs v0.8, 8× compute, shipped as Appendix C
  negative result)

### Tests · 228 passing · 0 flake · 0 regression

### Known non-blocking

- Tier 2 #19 · v1 vs v2 driver ablation — deferred (non-blocker)
- Tier 3 · Gate48 Run C' at temp=0.7 — deferred (non-blocker)

---

## [1.0.0-rc2] · 2026-05-07 — "MCP A2A production-hardened · TLS · RBAC · rate limit"

rc1 shipped the MCP surface as **preview**. rc2 promotes it to
production-ready: TLS + mTLS, per-token RBAC, per-token rate limiting,
an auto-reconnect client with -32029 backoff, a three-peer scoped A2A
demo, and `resources/*` for streaming session logs. 110 new tests
(77 → 187), 0 flake, 0 regression.

### 🎯 Highlights since rc1

- 📓 **`logging/setLevel` + `notifications/message`** (Task #59) ·
  MCP 2024-11-05 logging spec · per-session threshold dict threaded
  through `handle_message` so each TCP connection holds its own level ·
  invalid level → `-32602` so clients fail loud · `MCPClient.set_log_level(level)` +
  `call_tool(..., log_cb=fn)` dispatches `notifications/message` frames
  alongside progress · `_log` closure reads the level dict on every
  emit so a setLevel mid-session takes effect on the next frame · the
  shared `long_task` demo tool now emits start (`info`) + per-step
  (`debug`) + cancel (`warning`) records · capabilities advertise
  `"logging": {}` in initialize · 14 tests
- 🧩 **Plugin slash-command surface** (Task #62 + #63) ·
  `.claude-plugin/plugin.json` manifest synced with pyproject ·
  5 user-facing commands `/compass-{verify,drift,recall,search,status}`
  wrap the existing CLIs · `skills/compass-integrity/SKILL.md`
  auto-trigger pre-flight before recall · fixed real bug:
  `compass_verify.py` `UnicodeEncodeError` on Windows GBK piped stdout
  (✓ glyph) by forcing stdout/stderr to UTF-8 · 6 manifest tests
- 📡 **`notifications/progress` + `notifications/cancelled`** (Task #58) ·
  MCP 2024-11-05 progress spec · server emits intermediate frames when
  a call carries `_meta.progressToken` · `MCPClient.call_tool(...,
  progress_cb=fn)` auto-injects a token and dispatches frames to the
  callback before returning the final reply · `client.cancel(rid)`
  sends fire-and-forget cancel · 13 tests incl. full TCP e2e + cb
  exception isolation + mid-flight cancel shortens emission
- 🔐 **TLS + optional mTLS for TCP transport** (Task #53) ·
  `--tls-cert / --tls-key / --tls-client-ca` on server · `tls=True` +
  `tls_ca_cert` + `tls_client_cert/key` on client · banner prints
  `(tcp)` vs `(tls)` · 10 tests incl. full mTLS round-trip + bad-CA /
  missing-cert rejection
- 🛡️ **Token-scoped RBAC** (Task #49) · per-token scope sets
  (`tools.read` / `tools.write` / `resources.read` / `*`) ·
  `--token-file TOKENS.json` for out-of-band rotation · tools/list
  now scope-filtered · 21 tests
- 🎚️ **Per-token rate limit** (Task #51) · classic token-bucket ·
  `--rate-limit TOKEN=rps/burst` · returns -32029 with exact retry-in
  delay · 23 tests
- ♻️ **Client auto-backoff on -32029** (Task #52) · `MCPClient(...
  rate_limit_retries=N)` parses the server's retry-in and sleeps
  automatically · opt-in (default 0 preserves strict behaviour) ·
  16 tests
- 📡 **MCP resources/\*** (Task #48) · `compass://session/...`
  URIs · `resources/list` + `resources/read` · session-log
  streaming for peers · 16 tests
- 🔁 **MCPClient with transparent reconnect** (Task #46) ·
  exponential backoff · reconnect telemetry · 6 tests
- 🤝 **A2A demo v2** (Task #50) · three scoped peers
  (observer / reasoner / admin) · real RBAC denial surfaced in the
  demo · resources round-trip end-to-end · 4 tests
- 🩺 **server/status endpoint** (Task #45) · active connections,
  bytes in/out, per-token call counts, uptime · thread-safe
- 🔑 **TCP transport with token auth** (Task #42) · `authToken` on
  initialize · shipped baseline before RBAC/TLS layered on top

### Changed

- `pyproject.toml` · v1.0.0-rc1 → v1.0.0-rc2
- `mcp_server.py` gained TLS plumbing, RBAC enforcement, rate-limit
  dispatch gating. Banner now announces transport variant.
- `mcp_client.py` promoted to a library surface · TLS + backoff +
  reconnect telemetry · `MCPClientError` kept for callers.
- A2A demo rewritten around scoped tokens + resources.

### Tech debt closed

- MCP surface is no longer "preview" · TCP transport API frozen for
  1.0.0 final (stdio was already stable).
- Release automation still the rc1 machinery (`.github/workflows/
  release.yml` + `scripts/release_notes_extract.py`) · rc2 slice
  extraction verified.

### Known gaps · remaining v1.0 blockers

- full-500 re-run with V4-pro (Task #27 · running on T4)
- v1 vs v2 driver ablation (Task #20 · blocked on #27)
- notifications/progress + cancelled (deferred · no current consumer)

### Notes

- Plaintext TCP remains the default for localhost dev. TLS is opt-in ·
  enable it whenever the server binds to a non-loopback interface.
- Rate limit and RBAC compose: RBAC decides *can*, rate limit decides
  *how much*. A token with `*` scope but a 1 rps / 1 burst bucket is a
  valid production pattern for emergency admin access.
- Test count on this branch: **187 passed · 56s** on Python 3.13.

## [1.0.0-rc1] · 2026-05-07 — "integrity chain · MCP A2A preview · temporal push"

Release candidate for v1.0. Tamper-evidence + temporal reasoning + cross-agent
MCP surface. Eval gates still running (subset-48 on T4, full-500 V4-pro rerun
pending) — promoting to 1.0.0 after gates pass.

### 🎯 Highlights

- 🔒 **Merkle hash chain for session memory tamper-evidence** ·
  new `merkle_chain.py` module · `.chain.json` persisted alongside
  `projects/<slug>/memory/*.md` · `compass_verify` CLI detects edits/deletes
  · SHA-256 chained over file content + filename · atomic json write
- ⏱️ **Absolute time anchor rewrite in session_writer** (Task #30) ·
  memory writes now emit absolute timestamps (ISO-8601 + day bucket) instead
  of relative "3 sessions ago" phrasing · paper §6 temporal qt +X pts expected
- 📅 **Temporal-reasoning prompt + timeline scratch-pad** (Task #22) ·
  per-qt prompt template that builds an explicit date timeline before
  answering · `extract_temporal_answer()` post-parser · gated by
  `ZMM_TEMPORAL=1` (default on · set `0` for ablation)
- 🗣️ **ssu utterance-pair retrieval** (Task #23) ·
  single-session-user qt now retrieves adjacent user/assistant pairs instead
  of standalone chunks · ssu the weakest type in v0.9 · re-run pending
- 🎲 **Self-consistency n=3 majority vote** (Task #24) ·
  3-sample judge with majority answer · median confidence · variance-reduced
  compared to single-shot · ~3× token cost on judge pass only
- 🔀 **Hybrid BM25 + dense RRF retrieval** (Task #25) ·
  Reciprocal Rank Fusion over BM25 lexical + BGE-m3 dense · k=60 ·
  complements dense-only on rare-token queries (numbers, names, codes)
- 👥 **Cross-judge replication with Claude** (Task #26) ·
  DeepSeek V3.2 self-judge + Claude Opus cross-judge · κ reporting ·
  paper-defensible replacement for single-judge over-claim
- 📈 **Context top-5 → top-10 expansion** (Task #28) ·
  doubled context ceiling after reranker became reliable · trades ~2× prompt
  tokens for recall@10 lift · paper §6.2 ablation
- 🧩 **MCP A2A server (preview)** · new `mcp_server.py` stdio + TCP
  transports · JSON-RPC 2.0 · proxies to BGE-m3 daemon on `127.0.0.1:9876` ·
  marked **preview** in v1.0-rc1 · API may still shift before 1.0.0 final
- 🧪 **ZMM_TEMPORAL env gate** · A/B toggle for temporal prompt ·
  `ZMM_TEMPORAL=0` falls back to generic prompt · used by
  `tests/eval_longmemeval_accuracy.py`

### Added

- `merkle_chain.py` · tamper-evidence hash chain (update_chain / verify_chain
  / built-in smoke test + CLI)
- `mcp_server.py` · stdio + TCP MCP A2A server (preview)
- `ZMM_TEMPORAL` env gate wired into `tests/eval_longmemeval_accuracy.py`
- Timeline scratch-pad + `extract_temporal_answer()` post-parser
- BM25 + dense RRF hybrid retrieval path
- Self-consistency n=3 judge sampler · majority vote + median conf
- ssu utterance-pair retrieval variant
- Cross-judge replication harness · DeepSeek + Claude · κ computation

### Changed

- `pyproject.toml` · v0.9.5 → v1.0.0-rc1
- `session_writer.py` · absolute time anchors (Task #30)
- Context ceiling top-5 → top-10 (Task #28) · reranker gate retained

### Tech debt

- FastAPI `@app.on_event("startup")` → lifespan context manager (Task #39).
  Removes the DeprecationWarning from `test_http_server_e2e.py`. Lifespan
  handler runs the exact same init sequence (`init_db` → `init_audit_table`
  → `_start_audit_thread`) so behaviour is unchanged. Shutdown path left
  empty — the audit thread is daemonized. Verified by rerunning the full
  73-test suite with `-W error::DeprecationWarning`: 73 passed, 0 warnings.
- MCP raw JSON-RPC onboarding kit (Task #40). `docs/mcp-usage.md` grew a
  "Raw JSON-RPC (non-Claude clients)" section with the 3-step handshake
  (initialize → tools/list → tools/call) as literal wire-format JSON ·
  plus a shipped `scripts/mcp_smoke_rpc.py` that runs the same handshake
  end-to-end against the real server. Verified against a live daemon:
  initialize returns `nautilus-compass v1.0.0-rc1`, tools/list returns
  all 7 tools, `--tool recall --query "..."` returns real hits. Script
  forces UTF-8 on subprocess pipes so it works on Windows (GBK default
  would otherwise choke on the `·` midpoint character in tool schemas).
- Release automation pre-staged (Task #41). `.github/workflows/release.yml`
  fires on `v1.*` tag push, runs the full 78-test pytest sweep as a
  release gate, then auto-drafts the GitHub release with notes extracted
  from CHANGELOG.md by `scripts/release_notes_extract.py`. rc tags are
  marked prerelease automatically. 5 unit tests
  (`tests/test_release_notes_extract.py`) guard against header-style
  drift in CHANGELOG that would silently break the slice.

### Known gaps · v1.0 blockers (tracked in `docs/v1.0-checklist.md`)

- subset-48 A/C/D delta ≥ 0 vs baseline (Task #29 · ✓ closed · Run D +4.2 pts)
- full-500 re-run with V4-pro (Task #27 · running on T4 · ETA ~7h · watcher
  auto-triggered after gate48 sign-off)
- v1 vs v2 driver ablation (Task #20 · blocked on #27)

### Notes

- Merkle chain is append-friendly: `update_chain` re-baselines to current
  state · `verify_chain` reports mismatches without mutating disk · see
  `merkle_chain.py` smoke test for the 6-step contract
- MCP server shipped as preview; stdio transport is stable, TCP transport
  subject to change in 1.0.0 final. Protocol layer now has a **31-test**
  pytest suite (Task #37 + #38 · `tests/test_mcp_server.py` +
  `tests/test_a2a_adapter.py` + `tests/test_merkle_chain.py`) wired into
  CI as `v10-protocol-tests`. The Merkle tests caught one real bug on
  landing: a corrupted `.chain.json` used to crash `verify_chain` with
  `JSONDecodeError` — now the verifier treats it like a missing chain
  and reports `valid=False` so the caller can re-baseline.
  **Live-daemon smoke** (Task #40 · `scripts/mcp_smoke_rpc.py`): full 3-step
  handshake works end-to-end against the real server — initialize returns
  `nautilus-compass v1.0.0-rc1`, tools/list returns all 7 tools, `recall`
  returns 3 hits at cosine 0.432, `drift_check` flags a prompt-injection
  sample with alert=True against negative anchors. Promoting MCP to
  **stable** in 1.0.0 still requires one third-party client (Hermes or
  OpenClaw, not our own smoke) running a full session.
  **TCP transport landed** (Task #42). `mcp_server.py --transport tcp
  --host H --port P --token SECRET` accepts concurrent line-delimited
  JSON-RPC clients with token auth. Bad token → `-32001 unauthorized`
  + immediate disconnect. Token is stripped from the params before the
  handler sees it · never echoed. Covered by 4 new TCP subprocess tests
  in `tests/test_mcp_server.py` (total 82 tests green). Previous
  CHANGELOG claim of "stdio + TCP transports" was aspirational at rc1
  cut — now real.
  **Smoke script dual-transport** (Task #43). `scripts/mcp_smoke_rpc.py`
  grew `--transport tcp --host --port --token` flags backed by a
  Transport abstraction (`StdioTransport` / `TcpTransport`). Same 3-step
  handshake over both. Verified against a live TCP server: good-token
  `drift_check` returns alert=True cos=0.591; bad-token returns -32001
  with exit code 1 for scripting.
  **Operator status endpoint** (Task #45). New `server/status` JSON-RPC
  method returns `{active_connections, total_connections, auth_failures,
  messages_handled, uptime_seconds, server}`. Unauthenticated-safe
  (aggregates only · no tool output or per-client state), backed by a
  thread-safe counter set in mcp_server.py that the TCP loop bumps
  per-connection and per-message. `scripts/mcp_smoke_rpc.py --status`
  prints a one-line summary. 3 new tests in test_mcp_server.py cover
  in-process status, counter increments over TCP, and auth_failures
  tracking across good/bad-token clients.
  **Smoke keepalive mode** (Task #44). `scripts/mcp_smoke_rpc.py`
  grew `--keepalive SEC [--keepalive-limit N] [--keepalive-timeout S]`
  that runs `ping` every SEC seconds after handshake and prints the
  per-ping round-trip latency. Exits non-zero on any timeout, closed
  socket, or non-empty ping result. Useful as a `watch`-style probe of
  deployed TCP servers. Covered by 2 new subprocess tests: success
  path (3 pings land against a live server) and failure path (server
  killed mid-stream → smoke exits non-zero with ERR on stderr within
  the keepalive-timeout window).
  **Client library with auto-reconnect** (Task #46). New `mcp_client.py`
  ships a `MCPClient(host, port, token)` context manager with a thin
  API (`.list_tools()` `.call_tool(name, args)` `.ping()` `.status()`).
  I/O errors (ConnectionReset / BrokenPipe / timeout) trigger exponential
  backoff reconnect + re-handshake, transparent to the caller. Bad-token
  handshake surfaces immediately as `MCPClientError` · no silent retry
  loop on permanent auth failure. Telemetry counters `reconnect_count` +
  `last_reconnect_reason` are readable per-client. 6 new tests in
  `tests/test_mcp_client.py` cover handshake, ping, status, bad-token
  rejection, full reconnect-after-server-restart cycle, and bounded
  retry exhaustion. Total suite 93 tests green.
  **A2A peer-to-peer demo** (Task #47). `examples/a2a_peer_demo.py`
  spins up two independent MCPClient peers (Observer + Reasoner)
  talking to one TCP server. Observer writes 3 observations via
  ingest_obs · Reasoner recalls them + runs drift_check on a prompt-
  injection sample. Verified end-to-end against the live daemon:
  session files actually land on disk (session_20260507-1205_MCP-TCP-
  auth-landed.md et al.), recall returns real top-k hits (score=0.645),
  drift_check fires alert=True against BGE-m3 negative anchors. 4 new
  tests in test_a2a_peer_demo.py assert both peers register,
  drift/recall survive round-trip, token auth enforces, and bad-token
  raises MCPClientError. 97 tests green.
  **MCP resources/* for session log exposure** (Task #48). Implements
  the `resources/list` + `resources/read` half of the MCP spec so peer
  agents can read each other's session logs directly, not just through
  `recall`'s snippet. URIs use `compass://session/<project>/<file>`.
  `initialize` now advertises `capabilities.resources`. Listing is
  mtime-descending, capped at 50 entries · reads are capped at 256 KiB
  with a truncation marker. Path-traversal, scheme, and extension
  checks reject any URI that isn't a plain session_*.md under
  `~/.claude/projects/<proj>/memory`. `MCPClient` grew
  `.list_resources()` + `.read_resource(uri)`. 16 new tests cover
  capability advertisement, listing + limit, reading bodies,
  truncation, URI parameter validation (7 bad-URI cases including
  path traversal and URL-encoded splits), missing-file -32002, and
  full TCP round-trip with a fake projects root. Total suite 113 green.
  **Token-scoped RBAC** (Task #49). Shipped v1.0-grade authorization on
  top of the bearer-token auth from #42. `--token` is now repeatable and
  accepts `TOKEN:scope1,scope2` form; `--token-file` points at a JSON
  `{token: [scopes]}`. Three scopes today: `tools.read` (recall,
  drift_history, session_search, profile, drift_check), `tools.write`
  (ingest_obs, feedback_log), `resources.read`. Wildcard `*` grants
  everything; legacy `--token FOO` without scopes still maps to `*` for
  backward compat. `tools/list` filters per-token, `tools/call` rejects
  out-of-scope names with -32001 and a message naming the required
  scope. No --token → dev mode · None-scopes grants everything
  (localhost trust). Covered by 21 tests · parse/load/dispatch units
  plus 3 end-to-end TCP subprocess tests (reader, writer, unknown).
  Total suite 134 green.
  **A2A demo v2 · scoped peers + resources** (Task #50). Rebuilt
  `examples/a2a_peer_demo.py` to showcase the end-to-end v1.0 story:
  three peers (observer / reasoner / admin) authenticate with distinct
  scoped tokens, observer writes session logs via `ingest_obs`, and
  reasoner — restricted to `tools.read + resources.read` — confirms
  RBAC by having `ingest_obs` rejected with -32001, then uses
  `resources/list` + `resources/read` to fetch the 507-byte body
  observer just wrote (real YAML frontmatter round-trip over TCP).
  Live run against the daemon: `resources/read
  compass://session/...session_20260507-1221_MCP-TCP-auth-landed.md · 507B`.
  Added 4 tests covering RBAC denial in the demo flow, resources
  round-trip, scope-filtered tools/list, and denial when
  `resources.read` is absent. Legacy --token path still works. Total
  suite 138 green.
  **Per-token rate limiting** (Task #51). RBAC decides "can" · this
  decides "how much". Classic token-bucket, refill at `rps`, cap at
  `burst`, per-token lock so well-behaved peers never contend.
  Gates `tools/call`, `resources/list`, `resources/read`; `initialize`,
  `ping`, `server/status`, notifications stay free (protocol chatter).
  Config: `--rate-limit TOKEN=rps/burst` repeatable CLI flag, or
  extend `--token-file` to the dict form
  `{token: {scopes: [...], rate_limit: {rps: N, burst: M}}}` (legacy
  list form still accepted · merges with new form). On exhaustion
  replies `-32029 rate limited · retry in Xs` with the exact refill
  delay. Tokens without a bucket are unlimited (safe default ·
  localhost dev, long-running agents). 23 tests cover bucket math
  (drain/refill/cap/reject-bad-args), dispatch gating (tools/call +
  resources/read + ping-passes), schema parsing (dict/list/defaults/
  reject-bad), plus 2 end-to-end TCP tests (pipelined flood hits
  -32029 after burst · refill after sleep unblocks). Total suite 161
  green.
  **MCPClient auto-backoff on -32029** (Task #52). Mirror of #51 on the
  client. The server already includes the exact refill delay in its
  rate-limit message · this teaches `MCPClient` to parse it and retry
  transparently. Opt-in via `MCPClient(..., rate_limit_retries=N)`
  (default 0 · strict legacy behaviour preserved); on -32029 we parse
  `retry in X.Ys`, sleep that long × `rate_limit_multiplier` (default
  1.5 for jitter margin), and retry. Non-rate errors (-32001, etc.)
  still bubble immediately. Exposes `rate_limit_waits` +
  `last_rate_limit_wait_s` for dashboards. 16 tests cover regex parser
  (7 parameterised cases · including clamped negatives), unit dispatch
  with a fake socket (zero-retry / sleep-then-succeed / exhaust /
  pass-through / multiplier math), plus 2 end-to-end TCP tests (real
  rate-limited daemon · opt-in retry succeeds · default still raises).
  Total suite 177 green.
  **TLS + optional mTLS for TCP transport** (Task #53). Cross-machine
  A2A was plaintext · v1.0 blocker. Server gains `--tls-cert PATH
  --tls-key PATH` (both required · enables TLS) and `--tls-client-ca
  PATH` (enables mTLS · client cert verification). Handshake failures
  log `TLS-HANDSHAKE-FAIL · addr · reason` and drop the socket without
  taking down the listener. Client gains `tls=True`, `tls_verify=True`,
  `tls_ca_cert`, `tls_client_cert`+`tls_client_key` for mTLS, and
  `tls_server_hostname` for SAN override. Startup banner now announces
  `(tcp)` vs `(tls)` so operators can't mistake one for the other.
  Plaintext stays the default (localhost dev · stdio transport
  unaffected). 10 tests cover _build_server_ssl_context (happy, mTLS,
  missing-cert raises), full E2E (TLS round-trip, plaintext-client
  rejected, bad-CA rejected, tls_verify=False bypasses, mTLS happy,
  mTLS rejects no-cert peer), and CLI validation (--tls-cert without
  --tls-key exits 2). Built a self-signed cert factory on `cryptography`
  that includes SKI/AKI/KeyUsage so Python 3.13's strict SSL accepts
  them. Total suite 187 green.
- `sdk/a2a_adapter.py` version bumped `0.9.0-dev` → `1.0.0-rc1`;
  `DISCOVER_CAPABILITIES` is now documented in `CAPABILITIES` and
  guaranteed zero-side-effect (test enforces this)
- MCP server usage doc landed: `docs/mcp-usage.md`
- Gate48 finding for paper2 §4.6: `ZMM_VOTE=3` on gemini-2.5-flash at
  `temperature=0.1` gives 0 accuracy gain at 2.6× cost (flash outputs
  are near-deterministic at low temp, 3 samples collapse to identical
  answers). Revisit at `temperature=0.7` as Task #36.

## [0.9.5] · 2026-05-06 — "production-validated · A2A live · cross-benchmark"

Production hardening + A2A v1 protocol surface + EverMemBench cross-validation.

### 🎯 Highlights

- 🌐 **A2A v1 Protocol live in production** · ext https://compass.nautilus.social
  - GET `/.well-known/agent.json` · 5-capability discovery · OAuth2 + MCP advertise
  - POST `/a2a/messages` · envelope dispatcher · maps to REST + bearer
  - HTTP 200 verified ext (TLS · nginx · 67-320ms)
- 🛡️ **Audit log Stage 0+1 deployed** · prod hardened against high-frequency events
  - login + oauth.token 1/10 sampling · signup 100% audit
  - async deque + 5s background flusher · 0 lock contention
  - VACUUM in retention cron (Stage 0 disk reclaim)
- 📊 **Stress benchmark · 1M rows · p95 7ms** (50× under 100ms threshold)
  - Postgres switch trigger raised 100K → 5M rows (real benchmark · not heuristic)
- 📈 **Cross-benchmark on EverMemBench-Dynamic** · paper §6.5 final (n=500)
  - First independent benchmark filling EverCore omission gap
  - BM25 lower-bound (free): R@1 14.8 / R@5 25.2 / R@20 38.1
  - **compass full stack (BGE-m3 + reranker + multi-angle rewrite + day-bucket + V4-pro):**
    **recall@30 97.6% · e2e 44.4% on n=500 (5 topics · v2 driver · 2026-05-07)**
  - Position vs paper Table 4 baselines: **above all 4 reported** ·
    MemoBase 34.27 < Mem0 37.09 < Zep 39.97 < MemOS 42.55 < **compass 44.40**
  - Per-topic CV 4% · paper-defensible
- 🔬 **Cross-judge replication final** · n=500 · κ 0.772 · 88.6% agreement
  - DeepSeek V3.2 self-judge 56.6% · GLM-5.1 cross-judge 54.0% · Δ -2.6 (Good)

### Added

- A2A v1 protocol endpoints in `compass_http_v09.py` (+162 lines)
- `init_audit_table()` + `write_audit()` async deque + flusher
- `/v1/audit_log` self-export · GDPR delete/cancel/export endpoints
- `paper/AUDIT_PARTITION_SPEC.md` revised with real stress numbers
- `paper/sections/paper2_06_5_evermembench.tex` cross-benchmark (189 LOC · 4 tables)
- `scripts/stress_audit.sh` 4-scale benchmark
- `scripts/evermembench_smoke.py` BM25 R@K (free)
- `scripts/evermembench_e2e.py` BM25 + LLM e2e (~$0.10/100 QAs)
- `ops/prometheus_alerts.yml` 6 alerts
- `paper/REAL_USER_ONBOARDING.md` OpenClaw priority playbook
- `package.json` + `bin/compass-mcp.js` npm wrapper
- `tools/cross_judge_analysis.py` cross-judge κ analysis tool

### Changed

- nginx: + `/a2a/` + `/.well-known/agent.json` + `/metrics` location blocks
- AUDIT_PARTITION_SPEC trigger: 100K → 5M rows (data-driven)
- `paper2_03_method.tex` 9 hedge edits (over-claim → empirical)
- `paper2_appendix_crossjudge.tex` filled with real κ data
- `landing/index.html` v1.0 design · Nautilus dark theme

### Production verified (ext https://compass.nautilus.social)

- ✅ /healthz · 1281 req/s · p95 125ms
- ✅ /.well-known/agent.json · 200 (320ms · TLS)
- ✅ /a2a/messages · 200 (envelope reply)
- ✅ /metrics · Prometheus scrape-ready
- ✅ Self-heal: kill -9 → systemd restart 12s
- ✅ Live metrics: 305 users · 305 audit_events_24h · 0 drift_red

### Self-criticism

- 30-QA EverMemBench smoke (R@1 43%) over-optimistic vs full 2400 (R@1 15%)
  - n<100 CI ±15-20pt · documented in paper §6.5
- BM25 e2e 0% on EverMemBench (BGE-m3 + reranker pending T4 GPU)
- Two-server confusion early (T4 vs cloud) · stress test ran on wrong host
  - resolved · memorized to prevent recurrence

### CI · 2026-05-07 patch (post-tag)

- ✅ All 9 CI jobs green on main · ruff lint + py 3.10/3.12 ubuntu/macos matrix +
  v0.9 integration + npm wrapper + MCP smoke + Cursor extension build
- ✅ arXiv build workflow green · paper1 LaTeX compiles end-to-end
- Fixes (commits d3f179f → c2ff348):
  - `pyproject.toml` ruff config · ignore stylistic E/F rules · keep bug-catchers
  - `pyproject.toml` explicit packages list · `__init__.py` at root · `pip install -e .`
    now actually creates an importable `nautilus_compass` package (was broken before)
  - 14 modules · `sys.stdout.reconfigure(encoding="utf-8")` instead of
    `TextIOWrapper(sys.stdout.buffer)` · old pattern caused buffer aliasing →
    "I/O operation on closed file" under multi-import
  - 9 modules · CI fallback for `~/.claude/plugins/nautilus-compass` hardcoded
    paths · falls back to `Path(__file__).resolve().parent` when user-level
    plugin dir absent (CI runners + fresh clones)
  - `session_search.py` · added missing `PROJECTS.exists()` guard (parity with
    drift_history.py) · was raising `FileNotFoundError` on CI
  - `tests/test_e2e_encryption.py` · added missing `import os`
  - `paper/nautilus-compass.tex` · `\usepackage{cite}` → `\usepackage[round]{natbib}`
    + `\bibliographystyle{plain}` → `\bibliographystyle{plainnat}` ·
    sections used `\citep` / `\citet` (natbib syntax) · 45 unresolved citations
    + bbl incompatibility error fixed
  - `.github/workflows/ci.yml` · Test matrix · removed selftest.py and
    eval_recall.py (depend on user-specific memory data unavailable in CI) ·
    kept eval_drift.py (anchors-only · 100 hardcoded prompts)

### Promo · 2026-05-07

- 6 launch channels · `paper/promo/` (1184 lines)
  - `x_thread_zh.md` · 9 推 X 中文 thread + 配图 + 互动话术
  - `x_thread_en.md` · 9 tweets English thread
  - `hackernews.md` · Show HN title + first comment + reply playbook
  - `reddit_ml.md` · [R] flair · methodology callouts
  - `wechat_long_post.md` · ~5000 字公众号长文
  - `zhihu_tech.md` · ~5000 字知乎技术文
- `paper/V1.0_LAUNCH_DAY.md` · D-7 → D+7 timing playbook · 6 channels +
  cancel conditions + emergency contacts
- `paper/sections/paper2_00_abstract.tex` · expanded with EverMemBench 41% +
  cross-judge κ + V4-pro tied verdict (≤200 word target)

## [0.9.0-dev] · 2026-05-05 — "cross-agent · MCP/A2A · 56.6% on LongMemEval-S"

### 🎯 Highlights

- 🏆 **LongMemEval-S full-500 final = 56.6%** (DeepSeek V3.2 + 5 项加成 · ¥10 总成本)
  - 接近 Zep SOTA 下沿 (55-60%) · paper RAG SOTA 同档 (50-60%)
  - +12 pts vs Gemini-2.5-pro baseline (44.6%)
  - 1/15 cost vs commercial API stack
- 🆕 **Cross-agent memory federation** · 跨 Claude Desktop · Cline · Cursor · OpenClaw · Hermes 共享 memory
- 🆕 **MCP server v0.9** · 7 tools (4 new: ingest_obs · drift_history · session_search · profile)
- 🆕 **A2A adapter** · 4 capabilities (STORE/RETRIEVE/PROFILE/DRIFT_HISTORY)
- 🆕 **npm wrapper** · `nautilus-compass-mcp` · `npx -y` 即用
- 🆕 **session_writer + drift-aware obs** · session 末自动蒸馏 · drift 自审 (claude-mem 替代 + 增强)

### Added

- `session_writer.py` · Volc Ark DeepSeek session 蒸馏 (¥0.05/session)
- `drift_history.py` + `session_search.py` · cross-project · ASCII timeline · keyword + drift filter
- `daemon_anchor_loader.py` · 3-layer anchors (platform_base + domain + tenant)
- `anchors_platform_base.json` · 通用 15 pos + 25 neg
- `sdk/compass_client.py` · multi-agent ingest SDK · offline buffer · E2EE-ready
- `sdk/attach_memory.py` · one-line Nautilus agent integration
- `sdk/a2a_adapter.py` · A2A protocol HTTP service (4 capabilities)
- `sdk/mcp_adapter.md` · MCP server installation spec
- `mcp_server.py` · 3 tools → 7 tools
- `npm/` · `nautilus-compass-mcp` Node wrapper · auto Python detection
- `cursor-extension/` · VS Code extension TypeScript scaffold
- `examples/openclaw_integration.py` · `examples/hermes_integration.py`
- `examples/mcp_configs/` · paste-ready Claude Desktop · Cline · Cursor configs
- `paper/PLATFORM_FUSION.md` · 8 fusion points
- `paper/V09_USER_SCHEMA.md` · multi-user · multi-region · E2EE schema
- `paper/V09_API_SPEC.md` · server endpoint spec + FastAPI 实施
- `paper/V10_ROADMAP.md` · 12-month 17-phase roadmap
- `paper/RESULTS_v0.8.md` · 论文级 final 数据
- `paper/STAKE_DRIFT_COUPLING.md` · #4 fusion · economic spec
- `paper/sections/paper2_*.tex` · paper 2 LaTeX 8/8 sections (abstract · intro · related · method · eval · discussion · limitations · opensource)
- `INSTALL.md` · 3 install methods + 4 client configs
- `tools/migrate_from_v5.py` · v5-memory migration · #8 fusion
- `tests/test_compass_v09.py` · 7 integration tests
- `.github/workflows/ci.yml` · v0.9 multi-Python + npm + cursor + smoke
- `LICENSE` · MIT 首次正式声明

### Changed

- `pyproject.toml` v0.7 → v0.9.0-dev · 5 entry points · keyword expanded
- `mcp_server.py` v0.7 → v0.9 · 3 tools → 7 tools
- `stop_hook.py` · 加 session_writer 调用 · 不依赖 claude-mem
- `landing/index.html` · 加 v0.9 路线 + 8 fusion points sections
- `README.md` · LongMemEval section ~54% → 56.6% final
- `paper/results/experiments_20260505.csv` · v0.8 final 行填入 + 6 类型分项

### Removed

- claude-mem dependency (234 MB cache + uv tool + .claude-mem data)
  - session_writer 自给 · 不需要 claude-mem 写 session memory
  - v0.9 之前可共存 · 现在 compass 完整覆盖

### Performance

- LongMemEval-S full-500: **0.466 (baseline) → 0.566 (v0.8)** · +10 pts
- Per-type: ssa 76.8→83.9 · ku 51.3→57.7 · ssu 30.0→**57.1** ⭐⭐ · ms 43.6→54.9 · ssp 33.3→53.3 · temporal 45.9→46.6
- bge-m3 daemon recall p95: ~200ms (no change)
- session_writer cost: ¥0.05/session via Volc Ark DeepSeek V3.2

### Negative findings (paper 价值)

- Neo4j graph rerank: -6.2 pts (closed haystack 上跟 cross-encoder 重复)
- Double-model router (ssp+ku 用强 model): -2.1 pts (sample noise)
- SSP "infer preference" prompt: -37.5 pts (LLM 跑偏 · 撤回)
- MiniMax thinking-1024: 44% refusal cascade · full-500 collapsed at 33%
- Kimi K2.6 thinking: 0 gain (vs DeepSeek +10)


## [0.7.0] - 2026-04-29 — "from coin-toss to 0.92 AUC"

### 🎯 Drift detection: 0.51 → 0.92 AUC

Rebuilt the persona drift detection from the ground up in 4 steps:

1. **Anchors task-shaped**: replaced 25 abstract maxims with 25 task-pattern sentences that match real prompt distribution. AUC 0.51 → 0.79.
2. **Top-k mean scoring**: replaced anchor centroid mean (which blurs each anchor's semantics) with top-3 cosine mean. Marginal gain.
3. **bge-m3**: switched embedder from bge-small-zh-v1.5 (Chinese-only) to bge-m3 (1024d, 100+ languages). AUC → 0.84.
4. **Hard FP examples** added back into negative_anchors (10 examples → 35 total). AUC → **0.92**.

### 📊 LongMemEval-S benchmark (subset 12 · n=12 · 6 question types × 2)

| System | P@1 | P@5 | MRR |
|---|---|---|---|
| **nautilus-compass (m3 + bge-reranker-v2-m3)** | **0.750** | **0.917** | **0.837** |
| nautilus-compass (m3 only · no rerank) | 0.667 | 0.750 | 0.732 |
| mem0 (claimed retrieval-only) | n/a | ~0.6 | ~0.55 |

Reranker gives biggest lift on weakest question types:
- single-session-user: MRR 0.091 → 0.522 (**5x improvement**)
- multi-session: MRR 0.55 → 0.75 (+0.20)
- Other types already at MRR 1.0 baseline (ceiling)

Embedder ablation (subset 4 only):
- bge-small-zh-v1.5: MRR 0.414 (English content kills Chinese-only)
- bge-m3: MRR 0.760
- multilingual-e5-small: MRR 0.762 (practically tied with m3)

### 🆕 Added

- `tests/eval_calibrate.py` — cosine 分布校准建议 threshold
- `tests/eval_drift.py` — 50 aligned + 50 deviation drift detection AUC
- `tests/eval_recall.py` — leave-one-out P@1/3/5/MRR
- `tests/eval_longmemeval.py` — LongMemEval-S retrieval benchmark
- `tests/eval_rerank.py` — bi-encoder + CrossEncoder reranker pipeline
- `tests/run_all.sh` — full eval suite runner
- `pyproject.toml` + `LICENSE` (MIT) — pip packaging
- `.github/workflows/ci.yml` — CI on Linux + macOS · Python 3.10/3.12
- `OPEN_SOURCE_READINESS.md` — go/no-go decision tree
- `README_OPEN_SOURCE_DRAFT.md` — public-ready README

### 🔧 Changed

- `daemon.py` line 41-58: default embedder bge-m3 (was bge-small-zh) · all thresholds tunable via `ZMM_*` env vars
- `daemon.py` line 215-225: removed centroid mean (was blurring anchors)
- `daemon.py` line 282-310: drift scoring now top-3 mean, not centroid
- `recall.py` line 543, 601: daemon ping timeout 0.3s → 2.0s (m3 cold load was being misjudged unreachable)
- `recall.py`: dynamic embedder label in hook output (was hardcoded `BGE-bge-small-zh`)
- `anchors.json`: 25 positive (task-shaped) + **35 negative** (was 25, +10 hard FP examples added)

### 📝 Calibration values (m3 + 35 anchors · LongMemEval-validated)

```python
COSINE_MIN = 0.25                  # query↔memory recall threshold
DRIFT_ALERT_THRESHOLD = -0.032     # m3 + hard FP best Youden J
NEG_ANCHOR_HIT_THRESHOLD = 0.538   # neg ↔ memory p95
```

### ⚠️ Known issues

- m3 (~3 GB RAM) sometimes silently OOMs on Windows native Python 3.14. Recommended: WSL2.
- HF Hub downloads are flaky on Win/py3.14 (httpx client closes mid-request). Use `pip install -e .[modelscope]` and `install.sh` for ModelScope mirror fallback.
- Drift detection has false positives on system event injections (tool notifications mentioning "ephemeral", "size") that semantically overlap with anti-anchors. Production hooks should filter to true user prompts only.
- single-session-user retrieval MRR 0.099 — known limitation of bi-encoder-only retrieval. Use the BGE-CrossEncoder rerank path for production (see `tests/eval_rerank.py`).

### 📦 Dependencies

- Required: `sentence-transformers>=2.7`
- Optional: `modelscope` (China mirror), `hf_transfer` (faster HF download)
- Embedder: `BAAI/bge-m3` (default), or `intfloat/multilingual-e5-small`, or `BAAI/bge-small-zh-v1.5`
- Reranker (optional): `BAAI/bge-reranker-v2-m3`

## [0.6.0] - 2026-04-26

- Initial daemon TCP socket on 127.0.0.1:9876
- Strategy distillation (DPT-Agent style) via `strategy_store.py`
- Time-bucket recall (24h vs 7d+ warning)
- 3-hook lifecycle (UserPromptSubmit + PostToolUse + Stop)
- Per-domain anchors (vc / zenmind / default)
