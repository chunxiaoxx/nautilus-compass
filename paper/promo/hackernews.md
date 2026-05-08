# Hacker News Submission · compass v1.0

## Title (≤80 chars · the make-or-break field)

**Show HN: Long-term memory for LLM agents — 56.6% on LongMemEval, $3.50/run**

(alt 1) Show HN: Nautilus Compass — open-source memory layer for Claude Code / MCP
(alt 2) Show HN: I built persistent memory for Claude Code, ties Zep SOTA at 1/15 cost

> Choose primary based on overlap with same-week front page. If "memory" trending → alt 1. If "GPT-4o cost" trending → alt 2. Otherwise primary.

## URL field

`https://github.com/chunxiaoxx/nautilus-compass`

(NOT the arxiv link · GitHub gives more click-through and `Show HN` enforces working code)

## First comment (post within 60 sec of submission · this is the actual pitch)

```
Author here. Two months ago I started doing 8-hour Claude Code sessions and
hit the same wall ~30 times/day: "you forgot what I just said." So I wrote
200 lines of hook to give it persistent memory. That snowballed into Compass.

What it is:
- pip install nautilus-compass
- Claude Code plugin · MCP server (Claude Desktop, Cline, Cursor) · HTTP gateway
- 5-stage pipeline: BGE-m3 dense recall → bge-reranker-v2-m3 cross-encoder
  rerank → 3-angle query rewriting → type-aware prompting → judge chain
- All data local · MIT licensed

Numbers (full reproduction in repo):
- LongMemEval-S (n=500): 56.6% — ties Zep SOTA band, 15-20 pts above mem0/
  MemoBase. $3.50 total cost using DeepSeek V3.2 thinking.
- EverMemBench-Dynamic (n=500): 44.4% (Run 1) + 47.3% (Run 2 independent replication, n=497) — both above MemOS (42.55), mean 45.84% beats all 4 reported Table 4 baselines
  on paper Table 4.
- Cross-judge replication κ=0.772 on a 100-q subset.

The single largest win was multi-angle query rewriting (+27 pts on
single-session-user questions). Bigger than the reranker. Counter to my prior.

Counter-intuitive finding worth flagging: thinking-mode helps DeepSeek V3.2
(+10), helps GLM-5.1 (+2), is neutral on Kimi, and triggers a 44% refusal
cascade on MiniMax M2.7. Per-model · per-release benchmarking is mandatory,
not optional.

Failed experiments documented honestly:
- DeepSeek V4-pro think-high tied V3.2 at 8× cost. Headline stays V3.2.
- Sample-48 estimate showed +4.2 pts; full-500 showed -0.2. Don't trust n<100.

Happy to discuss methodology, reproducibility, or where the pipeline still
breaks (single-session-preference is our weakest at 53%).
```

## Anticipated comments + replies

**Q: "Just another RAG wrapper"**
> A: It's not single-pass cosine top-K. The pipeline does multi-angle query
> rewriting (3 reformulations · union dedup before rerank), cross-encoder
> reranking, day-bucket diversification (max 2 per date prevents single-session
> dominance), and reasoning-mode-aware LLM calls. Each stage is independently
> ablated in paper §4.2. The bi-encoder alone scores 41%; the full pipeline 56.6%.

**Q: "Why not Zep / mem0 / Letta?"**
> A: We benchmark against mem0 head-to-head in the repo (`tests/eval_mem0_headhead.py`).
> P@5 ties at 0.917; MRR is +0.122 in our favor with the reranker on. Zep is
> stronger on multi-session but uses GPT-4o + graph DB ($20+/run vs $3.50).
> Letta wasn't benchmarked yet — happy to add if their team wants to participate.

**Q: "Cross-judge methodology"**
> A: 100-question subset, two independent judges (DeepSeek V3.2-flash and Kimi
> K2.6) score the same 100 (Q, predicted, ground-truth) triples. Cohen's κ=0.772
> indicates substantial agreement. Disagreement subset (28 questions) was hand-
> labeled — judges agreed with hand-label 89%. Full data: appendix C.

**Q: "Why DeepSeek and not Claude / GPT?"**
> A: We tested 6: DeepSeek V3.2/V4, MiniMax M2.7, GLM-5.1, Kimi K2.6, plus
> Anthropic + OpenAI bindings. V3.2 thinking gave the best accuracy/$ ratio.
> Claude with thinking would likely match or exceed; we didn't run full 500
> on Claude because Anthropic doesn't offer batch pricing for paper-grade
> evals at our budget. PRs welcome.

**Q: "Production readiness?"**
> A: We've used it ourselves daily for two months. ~10K real prompts. Average
> retrieval latency ~120ms (BGE on a daemon). The drift detector (separate
> orthogonal feature, AUC=0.92) is what catches the 5% of queries where
> retrieval misses. Full SBOM + threat model in repo.

## Posting timing

- **Tuesday or Wednesday · 9-11 AM PT** (peak HN traffic + most engineers awake)
- AVOID: Mon (busy), Fri (low engagement), weekends
- AVOID: same-day major news (OpenAI keynote, FOMC, etc.)

## Pre-post checklist

- [ ] Repo README is the cleanest version (no half-finished sections)
- [ ] `pip install nautilus-compass` actually works on a fresh machine
- [ ] All claimed numbers in README match paper (no stale data)
- [ ] arxiv id is live · GitHub badge points to it
- [ ] First-comment text saved in browser draft · post within 60s of submission
- [ ] Have 2-3 friends on standby to upvote (NOT vote-rings · just real users
      who would have upvoted anyway · sends signal to ranker)

## After posting

- DO NOT: ask people to upvote on Twitter / WeChat / Slack (HN downranks
  detected vote rings within 5 min)
- DO: respond to every comment within 30 min for first 4 hours
- DO: keep replies factual · no marketing language · admit weaknesses
- IF FRONT PAGE: brace for 5K-15K visitors over 24h. Make sure repo
  doesn't 503 on docs hosting.
- IF NO TRACTION (≤10 votes in first 30 min): don't repost the same week.
  Wait 14 days · adjust title · try Tuesday next slot.
