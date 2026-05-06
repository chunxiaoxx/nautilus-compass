# Compass v0.9 · LongMemEval-S 56.6% · cross-agent memory federation

> 2026-05-05 · for HN / 知乎 / X / weibo · 1500 字 · 草稿

## TL;DR

We achieved **56.6% on LongMemEval-S (n=500)** with DeepSeek V3.2 +
local bge-m3 + a 5-component pipeline · matching the Zep SOTA band
at 1/15 the cost. The plugin (Compass v0.9) ships an MCP server, A2A
adapter, npm wrapper, and one-line Nautilus agent integration.

The killer feature isn't the accuracy. It's **cross-agent memory
federation**: same `user_id` across Claude Desktop, Cline, Cursor,
OpenClaw, Hermes → all clients share memory. claude-mem can't do
this; Mem0/Letta/A-MEM/Zep can't either.

GitHub: https://github.com/chunxiaoxx/nautilus-compass
Plugin: `pip install nautilus-compass` or `npx -y @nautilus/compass-mcp`

---

## What is LongMemEval-S?

[Paper](https://arxiv.org/abs/2410.10813) · 500 questions across 6
cognitive types over 50K-token chat haystacks. Tests an LLM's ability
to retrieve, count, update, and reason temporally over its own past.

| Type | What | n | v0.8 acc |
|---|---|---|---|
| single-session-assistant | recall what assistant said | 56 | **83.9%** |
| knowledge-update | latest-timestamp wins | 78 | 57.7% |
| single-session-user | recall user's stated facts | 70 | **57.1%** ← +27 from baseline |
| multi-session | count across sessions | 133 | 54.9% |
| single-session-preference | infer user's preference | 30 | 53.3% |
| temporal-reasoning | "how many days between..." | 133 | 46.6% |

Public baselines:

```
Letta:     35-38%
Mem0:      40-45%
A-MEM:     ~50%
Zep SOTA:  55-60%
paper RAG: 50-60%
🏆 Compass v0.8: 56.6%  · paper SOTA tier · 1/15 cost
```

## What's the trick?

Five components, ranked by gain:

1. **Multi-angle query rewriting (ssu only): +27 pts** ⭐⭐
   - For under-specified queries like "what dish cannot the user eat?",
     we rewrite into 3 angles (direct, topic-extracted, conversational
     marker) and union the top-15 from each.
   - Skipped for non-ssu types · those would dilute the signal.
2. **Multi-session decompose prompt: +8 pts**
   - The LLM reliably miscounts when given 5+ sessions in flat form.
     We tell it: "decompose into per-session sub-counts before
     aggregating".
3. **knowledge-update timestamp prompt: +2-3 pts**
4. **ssa context expansion (2400→3500 chars): +2 pts**
5. **TOP_K 10→15: +0.5 pts**

Total: +10 pts · empirically additive.

## Negative findings (papers often skip these)

We documented 4 interventions that made things *worse*:

1. **Neo4j graph reranking: -6.2 pts** (closed haystack signal redundant)
2. **Double-model router: -2.1 pts** (sample noise · 50 questions can't
   distinguish)
3. **SSP "infer preference" prompt: -37.5 pts** (LLM invents food-related
   answers regardless of question)
4. **MiniMax thinking-1024: refusal cascade collapse**
   - Sample 50 questions: 45.8% (apparently fine)
   - Full 500: refusal rate jumped 17%→44%, accuracy 33% at 302/500
   - Thinking-8192 with rule-6 prompt: 43.8% (still bad)
   - Solution: nothink (45.8% full 500)

The MiniMax cascade is, to our knowledge, the strongest documented
case of a thinking-mode causing systematic failure that we're aware
of in the literature.

## Per-model thinking ablation

```
Model              | nothink | thinking | Note
-------------------+---------+----------+--------------------------
Gemini-2.5-pro     |   ---   |  44.6%   | (sample matches full)
DeepSeek V3.2      |  39.6%  |  46.6%   | thinking +6.8 pts ⭐
GLM-5.1            |  41.7%  |  43.8%   | thinking +2.1
Kimi K2.6          |  35.4%  |  35.4%   | thinking gain = 0
MiniMax M2.7       |  41.7%  | 33% †    | thinking 1024 collapse
                   | 45.8% full          (nothink wins)
```

Bottom line: per-model thinking-on/off must be benchmarked per release.
Don't assume thinking always helps.

## Cross-agent memory federation (the feature you actually want)

claude-mem records narrative summaries → Claude Desktop only.
Mem0/Letta/Zep are single-client.

Compass is the first to support **same user_id across multiple MCP
clients**:

```
你在 Claude Desktop 学到 "X 偏好"           → Cursor 立刻知道
你在 Cursor 完成的任务                       → Claude Desktop 召回
你在任何地方报的 drift (red/yellow/green)   → 全部 client 共享 timeline
```

Setup is a 3-line config in each client's MCP file (Claude Desktop,
Cursor, Cline). Same `COMPASS_USER_ID` env var ties them together.

For **Nautilus agents** specifically, integration is one line:

```python
from nautilus_compass.sdk.attach_memory import attach_memory
agent = NautilusAgent(role="strategy", user_id="u_xxx")
attach_memory(agent)   # ← agent now has cross-agent memory
```

The agent automatically:
- Registers with compass on init
- Calls `recall(prompt)` before each action
- Calls `ingest_obs(...)` after task completion (with drift self-audit)
- Reports drift=red events to the stake economy module (v0.9.5)

## Drift detection (orthogonal capability)

Beyond LongMemEval, Compass embeds an **anchor-based drift detector**:
25 positive (aligned behavior) + 35 negative (drift exemplars) anchor
sentences. Embeds incoming prompts and computes cosine to anchor sets
in 50ms p95.

AUC=0.92 on 200-prompt test set. claude-mem has zero drift detection.
Zep/Mem0 are retrieval-only.

The detector also self-audits the LLM after each session — `drift:
green | yellow | red` is part of the observation frontmatter, with
`drift_signals` listing concrete evidence ("forgot PEM file",
"checked wrong server", etc.).

## Cost economics (Chinese-region focus)

For a Chinese-region production deployment:
- GPU: ¥300/月 (1 T4 spot)
- LLM API: ¥50-500/月 per active user (Volc Ark coding plan)
- bge-m3 inference: 0 marginal cost (local, daemon)

For the same workload using GPT-4o + Claude Sonnet, costs would be
≥20× higher. We argue this enables 100K+ MAU SaaS deployments at
small budgets.

## Open source

- MIT license (Apache 2.0 dual-license under consideration for v1.0)
- Reproducibility: $3.50 USD per 500-question run (Tencent T4 spot +
  Volc Ark coding plan)
- Three protocols: hooks (Claude Code), MCP (any MCP client), A2A
  (Nautilus platform agent network)
- Six CLIs: `compass-mcp`, `compass-a2a`, `compass-drift-history`,
  `compass-session-search`, `compass-session-writer`, `nautilus-compass`
- Cursor extension scaffold ready
- npm wrapper `@nautilus/compass-mcp` ready

## Roadmap

- v0.9.1 (next month): Nautilus auth integration · sqlite migration
- v0.9.5 (Q3 2026): stake×drift economic coupling
- v1.0 (early 2027): E2EE default · region sharding · RAID-2 review · paper publication

Detailed: [paper/V10_ROADMAP.md](paper/V10_ROADMAP.md)

## Try it

```bash
# Install
pip install nautilus-compass    # Python
# or
npx -y @nautilus/compass-mcp    # Node MCP wrapper

# In Claude Desktop · Cline · Cursor → see examples/mcp_configs/

# Run benchmark yourself ($3.50 budget)
python tests/eval_longmemeval_accuracy.py --pipeline=m3-rerank --full
```

GitHub: https://github.com/chunxiaoxx/nautilus-compass

---

## Acknowledgments

LongMemEval-S authors at Tencent for the benchmark · DeepSeek for
DeepSeek V3.2 · BAAI for bge-m3 · Tencent Cloud for spot T4 access ·
Volc Ark coding plan team for the multi-model API.

Feedback welcome: GitHub Issues · Discord (post-launch).

---

## v0.9.5 update (2026-05-06)

Since the v0.9 launch above, we've shipped four production-grade
hardenings. None of them change the LongMemEval-S 56.6% number, but
they make compass actually deployable.

### A2A v1 protocol live (real, not just spec)

- `GET https://compass.nautilus.social/.well-known/agent.json` → 200
  (5-capability discovery · OAuth2 + MCP advertise)
- `POST https://compass.nautilus.social/a2a/messages` → 200
  (envelope dispatcher · maps to REST + bearer)

Any A2A-compatible agent now auto-discovers compass. We're the first
public memory layer with both MCP and A2A protocols live.

### Stress benchmark · 1M rows · p95 7ms

```
scale     ins/s    p50  p95  vacuum     disk
1K       22,727    6ms  6ms      17ms  140KB
10K      26,455    6ms  7ms      35ms  1.2MB
100K     15,987    6ms  7ms     268ms  11.7MB
1M        9,905    7ms  7ms    3157ms  117MB
```

SQLite scales 50× past where we thought it would. Postgres switch
trigger raised from 100K rows to 5M rows · `audit_log` is happy on
SQLite WAL up to ~5M rows / ~1GB DB.

### Cross-judge replication final · κ 0.772

DeepSeek V3.2 (subject + judge) 56.6% · GLM-5.1 (cross-judge) 54.0%
on the same 500 LongMemEval-S questions. Agreement 88.6% · Cohen κ
proxy 0.772 · "Good · paper claim defensible". One outlier:
single-session-preference 60% agreement (GLM is stricter on
preference inference). Documented · not patched.

### EverMemBench cross-benchmark · honest about what we don't know

[EverMind/EverOS](https://github.com/EverMind-AI/EverOS) released
EverMemBench-Dynamic (paper [arxiv 2602.01313](https://arxiv.org/abs/2602.01313)) ·
2400 multi-party QA pairs over 254-day dialogues. We pulled the
public dataset and ran a BM25 baseline.

```
compass BM25 baseline · 5 topics · 2400 QAs · cloud CPU · 17.5s:
  R@1   14.8%    R@5   25.2%    R@10  30.6%    R@20  38.1%
```

That's a deliberately weak floor (no dense retrieval, no reranker).
End-to-end with a DeepSeek V4-flash answerer was 0% on a 50-QA
sample because BM25's false-positive rate is too high · the LLM
correctly returns UNKNOWN rather than fabricate.

paper-grade compass numbers (BGE-m3 + bge-reranker-v2-m3 · same
stack as our LongMemEval 56.6%) are pending T4 GPU availability.

**One observation worth noting**: the EverMemBench paper Table 4
benchmarks 4 systems (MemoBase / Mem0 / Zep / MemOS) but
`grep "EverCore" paper.txt` returns 0 hits in 1735 lines. The
companion eval framework ships an EverCore adapter. We make no
claim about why; we just note that an independent benchmark fills
a documented gap · scripts/evermembench_smoke.py runs in 17 seconds
for free, scripts/evermembench_e2e.py costs ~$0.10/100 QAs.

### Self-criticism we logged in commits

- 30-QA EverMemBench smoke showed R@1 43%; full 2400 showed R@1 15%.
  Lesson: n<100 has ±15-20pt 95% CI · do not draw conclusions.
- Two-server confusion early in the session (T4 GPU vs cloud
  production) · stress test ran on the wrong host first · killed
  and re-ran. Documented in memory to prevent recurrence.

---

*Compass is part of the [Nautilus platform](https://nautilus.social)
7-capability suite (memory, identity, agent runtime, marketplace,
stake economy, A2A, MCP). The platform is in private alpha; the
compass component is open-source MIT.*
