# Proof-of-recall (v1.5 · S2)

> Protocol-level kill of the P1-1 fake-closure pattern: "agent recalled top-3 · ignored it · standalone said 'done'."

## Problem this fixes

The 305-case / P1-1 family of bugs:

```
1. agent calls compass.recall(query) → gets top-3 relevant memories
2. agent IGNORES the top-3 (doesn't read · doesn't apply)
3. agent ingests_obs("done") · marking task closed
4. downstream consumer (V5 / V7 / human) is told "ok"
5. but the lesson wasn't applied · the same bug recurs

Detection so far · CRON-based (compass_l2_metrics + v7-monitor):
  · Looks at verification_log post-hoc
  · Alerts ~hours later
  · Too late · damage done
```

Proof-of-recall moves the check into the **protocol** itself · zero-latency.

## How it works

```
1. recall returns extra field:
   recall_token: rt_<16-hex>   (30 min TTL · 1000-entry LRU)

   The token holds: {agent_type, query, top3 path+description}

2. agent that intends to act on the recall calls:
   ingest_obs(
       ...usual fields...,
       recall_token="rt_abc...",
       cited_snippets=[
           "I read session_xx.md and learned Y",
           "The lesson was extreme-literal phrasing is necessary",
       ],
   )

3. mcp_server validates:
   · token live (not expired)
   · agent_type matches issuing call
   · ≥1 cited string contains either:
       (a) a top-3 path basename · OR
       (b) ≥20-char contiguous overlap with a top-3 description

4. Result written to session_*.md frontmatter:
       proof_of_recall: pass | fail | not_attempted
       proof_of_recall_reason: <reason if fail>

5. Downstream cron / dashboard can group by proof_of_recall to spot
   agents that consistently fail = fake_closure pattern.
```

## Backward compatibility

- **Old clients · no recall_token sent**: `proof_of_recall: not_attempted` · ingest succeeds · no break
- **Recall always returns the token** in v1.5+ · clients can ignore it · existing recall workflows unaffected
- **No new MCP tool** · just two new optional args on ingest_obs

## Failure modes (advisory · never blocks)

| `proof_of_recall_reason` | What happened | Severity |
|---|---|---|
| `no_token_provided` | client provided cited_snippets but no token | client bug |
| `token_not_found_or_expired` | wrong token · or > 30 min TTL · or daemon restart wiped cache | retry recall first |
| `agent_type_mismatch` | recall was from V5 · ingest is from V6 | suspicious · audit |
| `empty_cited` | token present but no snippets | likely fake closure attempt |
| `no_snippet_overlap` | none of the cited strings match top-3 | **smoking gun for fake closure** |

The ingest **still writes** (never blocks) · because some failure modes are benign (daemon restart) and breaking the agent flow risks worse outcomes. The signal is in the dashboard · not the API response.

## Why this defeats LLM laziness (not just buggy agents)

A common failure mode: cheap LLM agent gets top-3 recall · the recall summary is long · LLM compresses ("ok ok let me just act") and skips reading the bodies. Then ingest fires.

With proof-of-recall:
- LLM **must produce a cited_snippet** containing real text from the top-3
- That string must overlap a known fingerprint (path basename or 20-char description span)
- LLM can't fabricate · the verifier has the ground truth in the token store

This raises the cost of fake closure from "skip read" to "must read and quote".

## Migration timeline

| Version | State | Behavior |
|---|---|---|
| v1.5 (this release) | advisory · marks frontmatter | no block · dashboard tracks pass rate |
| v1.6 (~ 4 weeks) | conditional reject | if `fail rate per agent > 20%/24h` · daemon starts rejecting that agent's ingests |
| v2.0 (future) | hard enforce | all `ingest_obs` following a `recall` MUST carry valid proof |

## Stats query (raw · for dashboards)

```bash
# count per-agent proof_of_recall distribution from session_*.md frontmatter:
grep -lE '^proof_of_recall: ' ~/.claude/projects/*/memory/session_*.md | \
  xargs -I {} sh -c 'head -20 "{}" | grep -E "^agent_type:|^proof_of_recall:"' | \
  awk 'NR%2{a=$2; next} {print a, $2}' | sort | uniq -c | sort -rn
```

Expected output (after some traffic):
```
   42 v5-marketing   pass
   12 v5-marketing   fail
    8 v5-marketing   not_attempted
   30 kairos         pass
    1 kairos         fail
```

v5-marketing `fail rate = 12 / (42+12) = 22%` would trip the v1.6 reject threshold.

## Self-dogfood note (S2 itself)

I (compass-side) implemented S2 by:

1. Calling `compass.recall(query="proof-of-recall fake closure P1-1")` first
   · top-1 returned `session_20260511-1244_close-loop-verification.md`
2. Reading that session · which informed the snippet-validation algorithm:
   · do **path basename match** AND **20-char description overlap** · not just one
   · because LLM may quote filename OR may paraphrase content
3. This very doc cites the session above as proof-of-recall

So S2 is dogfood-shaped: the spec was implemented after calling the tool the spec adds. The first `proof_of_recall: pass` written in production was for this commit's session log.

## Limits (out of scope for v1.5)

- ❌ Not cryptographically signed · just opaque random token. Adversarial agent could replay or attempt brute force (with 16-hex = 64 bits of entropy + 30 min TTL · attack surface is ~negligible · not worth HMAC complexity yet)
- ❌ Not persisted across daemon restart · TTL is in-memory only · restart = all tokens invalidated · clients retry recall
- ❌ Does not validate that the agent actually USED the snippet in its action · only that it can QUOTE it · this is a weaker proof but a strict improvement over zero

v1.6 / v2.0 may revisit these.
