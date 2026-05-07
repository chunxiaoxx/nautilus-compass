# Reddit r/MachineLearning Submission

## Subreddit

**r/MachineLearning** — use `[R]` flair (research)

> Do NOT post to r/LocalLLaMA first · they are noisier and karma-thirsty.
> r/MachineLearning is small and rigorous · earn karma there first.

## Title (≤300 chars · be specific not clickbait)

`[R] Nautilus Compass: 56.6% on LongMemEval-S using DeepSeek V3.2 + local BGE-m3 — full ablation across 5 components, all 6 LLMs benchmarked, $3.50/run.`

> Mods downrank promotional titles. Above is descriptive · cites specific
> benchmark and setup. Should pass new-post review.

## Body (markdown)

```markdown
We open-sourced **Nautilus Compass** today — an open-source memory layer
for LLM agents — alongside a paper benchmarking 6 LLMs on LongMemEval-S
and EverMemBench-Dynamic.

**Repo:** https://github.com/chunxiaoxx/nautilus-compass
**Paper:** <arxiv-id>

## Setup

- **Retrieval:** BGE-m3 dense (top-100) + bge-reranker-v2-m3 cross-encoder (top-30)
- **Augmentation:** 3-angle query rewriting + day-bucket diversification (max 2/date)
- **Generation:** type-aware prompt templates (one per question type)
- **Evaluation:** cross-judge replication (Cohen's κ=0.772, n=100 subset)

## LongMemEval-S Results (n=500)

| System | Accuracy | Cost | Method |
|---|---|---|---|
| Compass + DeepSeek V3.2 thinking | **56.6%** | $3.50 | this work |
| Zep (paper, n=500) | 55-60% | $20+ | graph DB + GPT-4o |
| mem0 + Vertex 005 | 35.2% | $4.20 | extracted facts |
| MemoBase | ~32% | - | per Mem0 paper |
| Compass + DeepSeek V4-pro think-high | 56.4% | $28 | tied V3.2, 8× cost |

(numbers verified on full 500 · no sampling)

## EverMemBench-Dynamic Results (n=500, 5-topic stratified)

| System | Accuracy | Source |
|---|---|---|
| MemoBase | 34.27 | Hu et al. 2026 Table 4 |
| Mem0 | 37.09 | Hu et al. 2026 Table 4 |
| Zep | 39.97 | Hu et al. 2026 Table 4 |
| **Compass (this work)** | **41.0** | this work |
| MemOS | 42.55 | Hu et al. 2026 Table 4 |
| EverCore | not reported | not in paper |

## Ablation (LongMemEval-S full 500)

| Pipeline | Accuracy | Δ |
|---|---|---|
| BGE-m3 alone | 41% | baseline |
| + cross-encoder rerank | 46% | +5 |
| + multi-angle query rewriting | **53%** | **+7 (+27 on single-session-user)** |
| + type-aware prompts | 56% | +3 |
| + DeepSeek V3.2 thinking-on | 56.6% | +0.6 |

The single largest win was query rewriting · larger than the reranker. The
3 angles are: literal restatement, topic noun phrase, conversational marker
("X said", "after Y"). Per-angle top-100 retrieval, union dedup, then rerank
the union with the original query.

## Counter-intuitive findings

**1. Thinking mode is per-model · per-release.**

| Model | Δ thinking-on |
|---|---|
| DeepSeek V3.2 | +10 pts |
| GLM-5.1 | +2 pts |
| Kimi K2.6 | ±0 |
| MiniMax M2.7 | -34 (44% refusal cascade) |
| DeepSeek V4-pro think-high | -0.2 (vs V3.2, at 8× cost) |

**2. n<100 is unreliable.** V4-pro sample-48 showed +4.2 vs V3.2 baseline;
full-500 showed -0.2. Five of six per-type point estimates from the sample
disagreed with full-500 by more than the per-type 95% CI half-width.

## What's open-sourced

- 5-stage pipeline as Python package (MIT)
- MCP server (Claude Desktop / Cline / Cursor compatible)
- A2A protocol adapter
- Evaluation scripts for both benchmarks (full reproduction)
- All 6-LLM evaluation logs
- Cross-judge replication subset
- bge-m3 + reranker daemon indexer
- Drift detector (orthogonal feature · AUC=0.92 · separate paper)

## What we'd love feedback on

1. **Is multi-angle query rewriting really the biggest lever, or is it that
   our baseline retriever is weak?** We tried E5-Mistral-7B-instruct as a
   stronger baseline and it underperformed BGE-m3 on this task — surprising.
   Anyone seen similar?
2. **Day-bucket diversification (max 2 per date)** got us +3 on multi-session.
   Is there a more principled diversification approach? MMR didn't help.
3. **The single-session-preference type** is our weakest (53%). The retrieved
   evidence is correct ~85% of the time but the LLM extracts the wrong
   preference. Prompt engineering hit a wall. Open to ideas.

Happy to answer methodology questions, share more detailed numbers, or
add another system to our head-to-head if there's interest.
```

## Posting timing

- **Tuesday or Wednesday · 1-3 PM ET** (matches HN sweet spot · academic
  audience awake on both coasts)
- AVOID: post within 24h of NeurIPS / ICLR / ACL deadlines (everyone is
  too busy to engage)

## Pre-post checklist

- [ ] Read AutoModerator rules (r/MachineLearning is strict on self-promotion)
- [ ] Make sure account has >100 comment karma · NEVER post from a fresh account
- [ ] Have 2-3 substantive comments on other r/MachineLearning posts in
      the past 30 days (mods check)
- [ ] Title uses [R] flair · not [P] (project) — paper exists so use research flair
- [ ] Repo has clear LICENSE file · clear citation block · clear reproduction guide
- [ ] No "please upvote" anywhere · no link to Twitter or HN

## Anticipated mod issues

- **"Promotional"** → describe as research with code release, not product launch
- **"Already posted"** → this is its first time on r/ML
- **"Self-promotion ratio"** → keep account ratio of replies-to-other-posts
  to your-own-posts at >9:1 lifetime

## After posting

- Same playbook as HN · respond within 30 min · zero marketing language
- If the post hits Hot / front-page of r/ML, expect 200-500 comments and
  several methodology challenges. Have the eval scripts open in a tab and
  be ready to run quick experiments people request.
- IF DOWNVOTED below 0 in first hour: don't delete · just stop checking ·
  the post will sink and no one remembers in a week.
