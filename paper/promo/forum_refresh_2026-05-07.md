# Forum Refresh · nautilus-compass v1.0.0 · 2026-05-08

> Status: full MCP A2A stack online (TLS+mTLS+RBAC+rate-limit+resources+progress+cancel+logging spec-complete). LongMemEval-S = 56.6% (v0.8, locked). V4-pro full-500 came back at 56.4%, no improvement, shipping as a negative result. EverMemBench-Dynamic n=500 = **44.4% (Run 1)** and **47.3% (Run 2 replication, n=497)** — cross-run mean 45.84% exceeds MemOS (42.55) by +3.29 pts, top of the four reported Table 4 baselines. Drift detector AUC=0.83 held-out. Five user-facing slash commands shipped: `/compass-verify`, `/compass-drift`, `/compass-recall`, `/compass-search`, `/compass-status`. Third-party stdlib MCP shim ships in `examples/`.

---

## Hacker News pitch

**Title (≤80 chars):** Show HN: We tried a fancier LLM memory model. It didn't beat the simple one.

**First comment (post within 60 sec):**

```
Author here. v1.0.0 stable of Compass is out. Headline isn't a single win — it's a
documented null result we decided to ship rather than bury.

Two months ago we estimated DeepSeek V4-pro think-high would beat V3.2 on
LongMemEval-S by +4.2 pts based on a 48-question sample. We ran the full
500. V4-pro: 56.4%. V3.2: 56.6%. No improvement, at 8x the API cost. The
sample-48 estimate was wrong. We're locking V3.2 as the final config and
keeping the V4-pro logs in the repo so others don't repeat this.

What is shipped, factually:
- 5-stage retrieval (BGE-m3 + bge-reranker-v2-m3 + 3-angle rewriting +
  type-aware prompts + judge chain)
- Full MCP A2A: TLS, mTLS, RBAC, rate-limit, resources, progress, cancel.
  Structured logging is in flight.
- Hash-chained session log; /compass-verify recomputes the Merkle root.
  In real use it has caught corrupt JSON cleanly instead of silently
  serving stale state.
- Drift detector, AUC=0.83 on held-out. Has flagged real prompt-injection
  samples in our daily traffic, not just synthetic ones.
- 4 slash commands: /compass-verify, /compass-drift, /compass-recall,
  /compass-search.

Numbers (full reproduction in repo):
- LongMemEval-S, n=500: 56.6% (v0.8, locked)
- EverMemBench-Dynamic n=500 (5 topics): 44.4% (Run 1) and 47.3% (Run 2 independent replication, n=497) — both above MemOS (42.55), mean 45.84% beats by +3.29 pts
- V4-pro full-500: 56.4% (-0.2 vs V3.2, 8x cost)

MIT, all data local, pip install nautilus-compass. Happy to discuss the
n<100 sampling failure, the MCP auth surface, or where retrieval still
breaks (single-session-preference still our weakest).

https://github.com/chunxiaoxx/nautilus-compass
```

---

## r/LocalLLaMA pitch

**Title:** [Release] nautilus-compass v1.0.0 — local-first LLM memory + MCP server (MIT, looking for testers)

**Body:**

```markdown
v1.0.0 is up. Local-first memory for LLM agents, MCP-native, MIT licensed.

Install:
    pip install nautilus-compass==1.0.0

What it does, concretely:
- Retrieval: BGE-m3 dense + bge-reranker-v2-m3 cross-encoder, runs on CPU.
  No external API calls for retrieval. Embeddings stay on disk.
- MCP A2A server: TLS + mTLS + RBAC + rate-limit + resources + progress +
  cancel. Structured logging in flight. Drop into Claude Desktop, Cline, or
  Cursor.
- Hash-chained session log. `/compass-verify` recomputes the Merkle root,
  catches tampered or corrupt entries. Already saved us once when a JSON
  write got truncated.
- Drift detector (AUC=0.83 held-out). It has flagged actual prompt-injection
  attempts in daily logs, not just adversarial test sets.
- 4 slash commands: /compass-verify (Merkle integrity), /compass-drift
  (drift history per session), /compass-recall (semantic recall),
  /compass-search (session search).

Numbers we are sure of:
- LongMemEval-S n=500: 56.6%, locked
- EverMemBench-Dynamic n=500: 44.4% (Run 1) + 47.3% (Run 2) e2e — both exceed MemOS
  (42.55) by +1.85 pts, top of the four reported Table 4 baselines
- V4-pro full-500: 56.4% — null result, sampled +4.2 at n=48 reverted to
  -0.2 at n=500. Don't trust n<100.

What we want testers for:
1. MCP auth surface — mTLS + RBAC paths, especially anything that fails
   open under malformed certs.
2. /compass-drift on your real session logs. Synthetic adversarials are
   easy; we want false-positive rates on actual usage.
3. Anyone running it on Apple Silicon or ROCm — BGE daemon perf reports
   welcome.

MIT. https://github.com/chunxiaoxx/nautilus-compass

File issues with reproduction steps. We respond.
```

---

## X/Twitter thread

**[1/6]**
nautilus-compass v1.0.0 stable is out. Two-run EverMemBench replication (44.4% / 47.3%) plus a negative-result V4-pro experiment we chose to ship rather than bury.

We sampled DeepSeek V4-pro think-high at n=48 and saw +4.2 over V3.2.
Ran the full 500. Got -0.2.

n<100 estimates lie. Locking V3.2 at 56.6% as final.

**[2/6]**
LongMemEval-S, n=500:
- V3.2 thinking: 56.6% (locked)
- V4-pro think-high: 56.4% — 8x cost, no gain

EverMemBench-Dynamic, n=500 (5 topics):
- compass: 44.4-47.3% e2e (2 independent runs, mean 45.84%)
- MemOS:   42.55
- Zep:     39.97

+1.85 over MemOS · top of the four reported Table 4 baselines. Open-source MIT pipe lands above commercial systems with public numbers.

**[3/6]**
v1.0.0 ships full MCP A2A:
- TLS + mTLS
- RBAC
- rate-limit
- resources, progress, cancel
- structured logging (in flight)

Drop-in for Claude Desktop / Cline / Cursor. All local. MIT.

**[4/6]**
Two production catches worth flagging:

1. Hash-chained session log + /compass-verify recomputed the Merkle root
   on a truncated JSON write. Caught silently-corrupt state before it
   poisoned retrieval.

2. Drift detector (AUC=0.83 held-out) flagged real prompt-injection
   samples in daily traffic, not synthetic ones.

**[5/6]**
4 user-facing slash commands shipped:
- /compass-verify — Merkle integrity check
- /compass-drift  — drift history per session
- /compass-recall — semantic recall
- /compass-search — session search

Each one wraps a real workflow we hit weekly. No demo-ware.

**[6/6]**
What's still broken:
- single-session-preference is our weakest type
- structured logging on the MCP path not finished
- need testers for mTLS edge cases and false-positive rates on real
  drift logs

MIT. pip install nautilus-compass==1.0.0

https://github.com/chunxiaoxx/nautilus-compass
