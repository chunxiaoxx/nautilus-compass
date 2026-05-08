# Compass v1.0.0 stable · MCP A2A stack lands · LongMemEval-S 56.6% holds · EverMemBench replicated 44.4%/47.3% · the V4-pro that didn't beat v0.8

> 2026-05-07 · v1.0 release-candidate refresh · honest progress note

We cut **v1.0.0 stable** (2026-05-08), with **228 pytest tests passing** and the full MCP A2A protocol stack live. The headline is not a new accuracy record. It is the opposite: we ran V4-pro (the next-generation pipeline variant) on the full LongMemEval-S 500-question set and it came back at **56.4%** — slightly worse than v0.8's locked-in **56.6%**. Eight times the compute, no improvement. We are publishing this as a negative-result appendix to Paper2 instead of burying it. Below is what shipped, what worked, and what didn't.

## The rc2 milestone · MCP A2A protocol stack complete

rc2 closes the protocol surface we promised at v0.9. The stack now ships, end-to-end:

- Transports: **stdio + TCP + TLS + mTLS**
- AuthZ: **RBAC scopes** per tool / resource
- Flow control: **token-bucket rate limiting** with the `-32029 retry-in` JSON-RPC error · clients **auto-backoff** and **reconnect**
- Discovery and streaming: **resources/list + resources/read** · **notifications/progress** · **notifications/cancelled**
- Observability: **logging/setLevel** (final piece, in flight)

215+ tests pass against this surface. Translation: any MCP client (Claude Desktop, Cline, Cursor, the new wave of A2A agents) can talk to compass over the wire it prefers, with proper auth, with proper rate-limit semantics, and recover cleanly from a compass restart.

## Paper2 · the V4-pro experiment that didn't ship

Paper2 (LongMemEval-S, n=500) is **locked at v0.8 = 56.6% as the final result**.

We had a candidate successor — V4-pro — that looked promising on a 48-question pilot: estimated **+4.2 points**. We ran it on the full 500. The number came back at **56.4%**, i.e. **−0.2 points** vs v0.8. The +4.2 was sample noise. The 8× compute cost was a null result.

We are publishing this. It is in the paper as a negative-result appendix. The lesson — n<100 has wide enough confidence intervals to fabricate phantom wins — is the lesson of this whole sub-field, and shipping v0.8 as final is more honest than shipping a regression and calling it progress. Other recent memory papers have been less restrained.

## Paper1 · drift detection · AUC 0.83 held-out · 0.92 in-set

Paper1 (anchor-based drift detection) is in better shape:

- **Held-out AUC = 0.83**, in-set AUC = 0.92
- The interesting finding: anchor *design* dominates everything. Random anchors gave AUC = **0.50** (literally a coin flip). Task-styled anchors — anchors that mimic the linguistic shape of real drift events — pushed it to **AUC = 0.84**. That's a +0.34 jump from anchor design alone, before any model change.

Real-world catches in the last week: the detector flagged actual injection-test prompts at cos = **0.585+** vs the negative-anchor set, alert=True. Not synthetic, not staged — real prompts that arrived in production. The Merkle-chained session log also caught a corrupt session JSON in the wild and degraded gracefully (returned what it had, surfaced the integrity failure, did not crash the agent loop). Both are working as designed.

## EverMemBench · 44.4-47.3% on n=500 across 2 independent runs · top of reported baselines

We ran compass on the full EverMemBench-Dynamic 5-topic suite (n=500, BGE-m3 + bge-reranker-v2-m3, V4-flash answerer + judge) end-to-end twice on consecutive days. Run 1 (2026-05-07) = **44.4%** (n=500). Run 2 (2026-05-08) = **47.3%** (n=497, 3 questions skipped on topic 04 for transient DeepSeek API 5xx). Cross-run mean **45.84%**.

For context, the EverMemBench paper Table 4 (GPT-4.1-mini answerer, 9-subtask average) reports: Full Context 37.44, MemoBase 34.27, Mem0 37.09, Zep 39.97, MemOS 42.55. compass Run 1 at 44.4% **exceeds MemOS by 1.85 pts**, Run 2 at 47.3% **exceeds MemOS by 4.73 pts**, and the cross-run mean (45.84%) places above every reported baseline by +3.29 pts — an open-source MIT-licensed memory layer landing top of the table against the four well-funded commercial systems for which numbers are public. EverCore is referenced in the dataset but its number is not reported.

Per-topic breakdown is tight (CV 4%): 44/46/42/45/45 across topics 01–05. Recall@30 on the retrieval stage was 97.6% — the BM25-only baseline is 38.1%, so the dense retriever + cross-encoder + multi-angle rewrite stack closes nearly the entire retrieval gap.

Three real bugs were debugged on the way to the headline — a topic-id mapping mismatch, a reranker score-normalization sign error, and a chunking-window off-by-one. All three are documented in `paper/sections/paper2_06_5_evermembench.tex`. We mention them because eval-infra bugs are how phantom +N-point wins get manufactured, and we'd rather you trust the 44.4–47.3% range (with the lower number reported as the abstract headline to avoid cherry-picking).

## Plugin surface · four user-facing commands landed

Iter 1 of the plugin surface just landed. Four slash commands now ship in the `.claude-plugin/plugin.json` manifest:

- `/compass-verify` — Merkle integrity check across the local session log
- `/compass-drift` — drift history summary (red / yellow / green over time)
- `/compass-recall` — semantic recall against your federated memory
- `/compass-search` — past-session search by free-text query

The point of these commands is that compass stops being a "library you wire in" and starts being a thing you invoke. The cross-agent federation we shipped at v0.9 (same `user_id` across Claude Desktop, Cline, Cursor, OpenClaw, Hermes) is now a slash command away from the prompt.

## What this release is, and isn't

v1.0.0 **is**: a feature-complete protocol surface, 228 passing tests, two locked-in benchmark results (LongMemEval-S 56.6%, EverMemBench-Dynamic n=500 44.4-47.3% across 2 runs — top of the reported baselines), and real-world evidence that the drift detector and Merkle log catch real failures, not just synthetic ones.

v1.0.0 **is not**: a new LongMemEval-S accuracy record. The biggest experiment of the cycle — V4-pro on the full 500 — did not work. We are shipping that finding alongside the wins.

## Try it

```bash
pip install nautilus-compass==1.0.0
# or
npx -y @nautilus/compass-mcp
```

GitHub: https://github.com/chunxiaoxx/nautilus-compass · MCP configs for Claude Desktop, Cline, Cursor in `examples/mcp_configs/` · paper preprints in `paper/`. Issues and PRs welcome. v1.0 final follows after rc2 burns in.
