# PaperWithCode Submission · nautilus-compass · 2026-05-08

> Two leaderboard claims · user submits manually after arxiv ID issued · arxiv ID
> backfilled into both submissions before publish · all numbers traced to
> `paper/RESULTS_v0.8.md` (LongMemEval-S) and
> `paper/results/evermembench_n500_v2_20260507.log` (EverMemBench-Dynamic).

---

## Submission 1 · LongMemEval-S leaderboard

- **PWC URL**: `https://paperswithcode.com/sota/longmemeval-s`
  *[TODO verify slug — PWC slug naming is inconsistent. The dataset card likely
  lives at `https://paperswithcode.com/dataset/longmemeval` (singular,
  unhyphenated). The associated SOTA leaderboard slug observed in similar
  benchmarks pattern follows `sota/<task>-on-<dataset>`. Concrete
  candidates to check before submission, in order of likelihood:*
  1. `https://paperswithcode.com/sota/long-term-memory-evaluation-on-longmemeval-s`
  2. `https://paperswithcode.com/sota/question-answering-on-longmemeval-s`
  3. `https://paperswithcode.com/sota/longmemeval-s` (only if PWC has a
     short alias)
  *If none exist, submit the paper first; PWC auto-generates a leaderboard
  on first claim. Screenshot the empty/missing state and flag.*]
- **Method name**: `nautilus-compass v0.8`
  (the v0.8 driver = the 56.6% headline · `tests/eval_longmemeval_accuracy.py
  --pipeline=m3-rerank --full`)
- **Authors**: chunxiaoxx (Nautilus Open Platform)
- **Paper link**: `arxiv.org/abs/[TODO arxiv ID — paper2 first · paper1 separately]`
- **Code link**: `https://github.com/chunxiaoxx/nautilus-compass`
- **Claimed metric**: **56.6% accuracy (n=500)** · per-question JSONL +
  summary in `.cache/longmemeval_acc_m3_rerank_full_1777975609.jsonl`
  (cited verbatim from `RESULTS_v0.8.md` §Reproducibility).

### Method description (≤500 chars)

> nautilus-compass v0.8 closes the LLM-as-judge gap with a 5-component
> pipeline: BGE-m3 dense retrieval (top-50), bge-reranker-v2-m3 cross-encoder
> (top-20), multi-angle query rewriting (3 angles, union-deduplicated), 6
> question-type-aware prompts, and DeepSeek V3.2 thinking as the answerer
> (Volc Ark · ~$0.002/q). Note: paper Table 4 baselines use GPT-4.1-mini;
> we substitute DeepSeek V3.2 — comparable tier, 1/15 cost. n=500. (495 chars)

### Hyperparameters block

| Field | Value |
|---|---|
| `retriever` | BGE-m3 (BAAI · MIT · 1024-dim) |
| `reranker` | bge-reranker-v2-m3 |
| `top_k_recall` | 50 |
| `top_k_rerank` | 20 (effective TOP_K 15 after day-bucket filter) |
| `context_char_limit` | 1500 (ssa pipeline expanded to 3500) |
| `per_day_max` | 2 sessions |
| `query_rewrite_angles` | 3 (union-deduplicated) |
| `answerer` | DeepSeek V3.2 thinking (Volc Ark · `ZMM_THINKING=on`) |
| `judge` | DeepSeek V3.2 thinking (LLM-as-judge protocol) |
| `seeds` | deterministic per `tests/eval_longmemeval_accuracy.py` |

### Reproducibility section

```bash
git clone https://github.com/chunxiaoxx/nautilus-compass
cd nautilus-compass
export ARK_API_KEY=<your-volc-ark-key>
export ZMM_LLM_PROVIDER=ark
export ZMM_SUBJECT_MODEL=deepseek-v3.2
export ZMM_JUDGE_MODEL=deepseek-v3.2
export ZMM_DEVICE=cuda
export ZMM_RERANKER_MODEL=BAAI/bge-reranker-v2-m3
export ZMM_THINKING=on
export ZMM_QUERY_REWRITE=on
python tests/eval_longmemeval_accuracy.py --pipeline=m3-rerank --full
```

- **Hardware**: 1× NVIDIA T4 (Tencent Cloud spot · `43.173.164.32`)
- **Wall clock**: 7.79 h GPU (28058 s end-to-end)
- **Cost**: ¥10 total (≈ $1.50 USD · GPU spot + DeepSeek V3.2 API)
- **Per-question logs**: `.cache/longmemeval_acc_m3_rerank_full_1777975609.jsonl`
- **Summary**: `.cache/longmemeval_acc_m3_rerank_full_1777975609_summary.json`

### 6 question-type breakdown (n=500)

| Type | n | acc |
|---|---|---|
| single-session-assistant | 56 | 83.9% |
| knowledge-update | 78 | 57.7% |
| single-session-user | 70 | 57.1% |
| multi-session | 133 | 54.9% |
| single-session-preference | 30 | 53.3% |
| temporal-reasoning | 133 | 46.6% |
| **Overall** | **500** | **56.6%** |

---

## Submission 2 · EverMemBench-Dynamic leaderboard

- **PWC URL**: `https://paperswithcode.com/sota/[TODO verify slug]`
  *[TODO verify slug — EverMemBench was released by Hu et al. 2026
  (arxiv 2602.01313) and is comparatively new. PWC slug candidates, in
  order of likelihood:*
  1. `https://paperswithcode.com/sota/long-context-question-answering-on-evermembench-dynamic`
  2. `https://paperswithcode.com/sota/memory-on-evermembench`
  3. `https://paperswithcode.com/sota/evermembench-dynamic`
  *Dataset card likely at `https://paperswithcode.com/dataset/evermembench`.
  If no leaderboard exists yet, our submission would be the first to populate
  it — flag this in the cover note to the moderator and link Hu et al. 2026
  (arxiv 2602.01313) so PWC indexes the dataset alongside the claim.*]
- **Method name**: `nautilus-compass v2 driver`
  (`scripts/evermembench_v2.py` · BGE-m3 + bge-reranker-v2-m3 + multi-angle
  rewrite + day-bucket diversification · DeepSeek V4-flash answerer & judge)
- **Authors**: chunxiaoxx (Nautilus Open Platform)
- **Paper link**: `arxiv.org/abs/[TODO arxiv ID — same paper as above]`
- **Code link**: `https://github.com/chunxiaoxx/nautilus-compass`
- **Claimed metric**: **44.4-47.3% Average accuracy (2 independent runs · n=500 / n=497 · mean 45.84% · 5 topics ×
  100 QAs)** · recall@30 = 97.6% · raw run log
  `paper/results/evermembench_n500_v2_20260507.log` (line 87:
  `OVERALL  n=500 · recall@30=97.6% · acc=44.4%` (Run 1, 2026-05-07).
  Independent rerun on the identical pipeline (Run 2, 2026-05-08): `OVERALL  n=497 · recall@30=98.2% · acc=47.3%` (3 questions on topic 04 skipped due to transient DeepSeek API 5xx).

### Method description (≤500 chars)

> nautilus-compass v2 retrieval stack on EverMemBench-Dynamic: BGE-m3 dense
> top-100 → bge-reranker-v2-m3 top-30 → multi-angle query rewrite (3
> angles) → day-bucket diversification (max 2 sessions per date) → 2500-char
> context window → DeepSeek V4-flash answerer & judge. **Note vs paper Table 4**:
> we use V4-flash answerer; Hu et al. used GPT-4.1-mini (comparable tier,
> different vendor). 5.58 h on 1× T4. (498 chars)

### Hyperparameters block

| Field | Value |
|---|---|
| `retriever` | BGE-m3 (BAAI · MIT · 1024-dim) |
| `reranker` | bge-reranker-v2-m3 |
| `top_k_recall` | 100 |
| `top_k_rerank` | 30 |
| `context_char_limit` | 2500 |
| `per_day_max` | 2 sessions |
| `query_rewrite_angles` | 3 (union-deduplicated) |
| `answerer` | DeepSeek V4-flash (Volc Ark · `reasoning_mode="non-think"`) |
| `judge` | DeepSeek V4-flash (`max_tokens=256`, see bug archeology in §6.5) |
| `n_per_topic` | 100 |
| `topics` | 01, 02, 03, 04, 05 (all 5 EverMemBench-Dynamic topics) |

### Per-topic breakdown (n=500)

| Topic | n | recall@30 | acc |
|---|---|---|---|
| 01 | 100 | 97.0% | 44.0% |
| 02 | 100 | 95.0% | 46.0% |
| 03 | 100 | 98.0% | 42.0% |
| 04 | 100 | 99.0% | 45.0% |
| 05 | 100 | 99.0% | 45.0% |
| **All (Run 1)** | **500** | **97.6%** | **44.4%** |
| **All (Run 2)** | **497** | **98.2%** | **47.3%** |
| **Mean of 2 runs** | — | 97.9% | **45.84%** |

Cross-topic CV = 4% (low variance · consistent across topics).

### Position vs Table 4 baselines (per paper §6.5 narrative)

```
Full Context (1M tokens, no memory)  37.44
+ MemoBase                            34.27
+ Mem0                                37.09
+ Zep                                 39.97
+ MemOS                               42.55
+ nautilus-compass (us, Run 1)        44.40   ← claimed primary
+ nautilus-compass (us, Run 2)        47.28   ← independent replication
+ nautilus-compass (us, 2-run mean)   45.84   ← cross-run average
+ EverCore                            not reported in paper
```

compass at 44.40 (Run 1) and 47.28 (Run 2) places **+1.85 to +4.73 pts above MemOS** (mean 45.84 = +3.29) (the previous top
reported entry in Hu et al. Table 4) and above all four reported
baselines, filling the documented EverCore gap with an open-source,
self-hosted alternative.

### Reproducibility section

```bash
# Same install as Submission 1
export VOLC_ARK_KEY=<...>
python scripts/evermembench_v2.py \
    --topics 01,02,03,04,05 \
    --n-per-topic 100 \
    --top-k-recall 100 \
    --top-k-rerank 30 \
    --ctx-chars 2500 \
    --answerer deepseek-v4-flash \
    --judge deepseek-v4-flash
```

- **Hardware**: 1× NVIDIA T4 (Tencent Cloud spot · `43.173.164.32`)
- **Wall clock**: 5.58 h (20079 s end-to-end · log timestamp confirms)
- **Cost**: ~$25 USD LLM API (per §6.5 of paper2)
- **Raw log**: `paper/results/evermembench_n500_v2_20260507.log` (92 lines)

### Honest disclosure (visible on submission)

The original Hu et al. 2026 paper Table 4 baselines all use
`gpt-4.1-mini` as the answerer. We use DeepSeek V4-flash. While both are
"cheap thinking-tier" models from their respective vendors, **the
answerer-choice axis is not held constant against Table 4**. We document
this in §6.5 of the paper and have surfaced it in the method description
above. A same-answerer comparison would require either (a) us re-running
all 5 baselines on V4-flash, or (b) the EverMemBench authors publishing
GPT-4.1-mini numbers for compass — neither is in scope for v1.0.

---

## Pre-submission checklist

- [ ] arxiv ID acquired (paper2 first · paper1 separately)
- [ ] arxiv ID backfilled into BOTH submissions (search-replace
      `[TODO arxiv ID]` in this file before submitting)
- [ ] PWC account created (`chunxiaoxx` handle · same as GitHub)
- [ ] Both papers claimed under same author handle (paper1 + paper2 ·
      cross-link them in PWC author profile)
- [ ] Both leaderboards verified to exist:
  - [ ] LongMemEval-S slug confirmed (search PWC for `longmemeval`;
        screenshot if absent · flag in moderator note)
  - [ ] EverMemBench-Dynamic slug confirmed (search PWC for
        `evermembench`; screenshot if absent · flag in moderator note)
- [ ] Code repo `github.com/chunxiaoxx/nautilus-compass` is public
- [ ] Repo README mentions PWC submissions (add a "Leaderboard claims"
      section linking to both PWC URLs once approved)
- [ ] §6.5 LaTeX answerer-name pinned to V4-flash (current draft has
      one residual `V4-pro think-high` in Table~\ref{tab:em-full-stack}
      caption — fix before submitting paper)

## Post-submission monitoring

- Watch PWC moderation queue → typical 24–72 h
- Monitor for community questions / methodology challenges in PWC
  comments (subscribe to email notifications on the leaderboard page)
- Cross-link to methodology in `paper2 §6.5` + `RESULTS_v0.8.md`
- If a moderator asks for a third-party reproduction, point to the
  reproducibility scripts in the repo + per-question JSONL artifacts

## Risk · MemOS / EverMind challenge

If a MemOS author or an EverMind author challenges the 44.4-47.3% number:

- **Per-question JSONL**: regenerating a v3 run with full per-question
  outputs (in progress as of 2026-05-08). Current v2 log
  `paper/results/evermembench_n500_v2_20260507.log` provides per-batch
  acc/recall but not per-question detail. Pre-empt this with a public
  v3 JSONL drop **before** the PWC submission goes live if possible.
- **Bootstrap CI script**: `scripts/bootstrap_em_jsonl.py` ready to
  produce 95% CI from per-question JSONL once available.
- **Cross-judge with Claude script**: `scripts/cross_judge_em_claude.py`
  ready · prior LongMemEval cross-judge gave κ=0.772 (paper-defensible).
- **Full reproduction data**: `paper/results/evermembench_n500_v2_20260507.log`
  (92 lines · all 5 topics · per-batch progress). Plus the answerer-axis
  caveat is already disclosed (see "Honest disclosure" above) so a
  challenge on that ground has an upfront answer.

---

## Slug verification gotcha (where I'm not 100% sure)

PWC slug naming is **inconsistent** across benchmarks. Patterns I've
observed:

| Pattern | Example |
|---|---|
| `sota/<dataset>` | rare · e.g. `sota/imagenet` |
| `sota/<task>-on-<dataset>` | most common · e.g. `sota/question-answering-on-squad` |
| `sota/<dataset>-<variant>` | e.g. `sota/glue-cola` |

For the two leaderboards in this submission:

1. **LongMemEval-S** — likely `sota/long-term-memory-evaluation-on-longmemeval-s`
   or `sota/question-answering-on-longmemeval-s`. **Not 100% sure** which
   PWC will accept; the Wu et al. NeurIPS 2024 paper may not yet have a
   PWC leaderboard at all (search before submitting).
2. **EverMemBench-Dynamic** — likely no leaderboard exists yet (paper
   only released 2026; arxiv 2602.01313). Submission may **create the
   leaderboard** rather than join one. Flag in the moderator note.

Mitigation: when manually submitting, screenshot the PWC search results
for `longmemeval` and `evermembench` first. If no leaderboard found,
include a note to the PWC moderator linking the source dataset paper
(Wu et al. 2024 arxiv 2410.10813 for LongMemEval; Hu et al. 2026 arxiv
2602.01313 for EverMemBench). PWC moderators will create the
leaderboard and process the claim together.
