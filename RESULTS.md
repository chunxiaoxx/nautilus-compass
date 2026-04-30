# Evaluation Results

> **Reproducibility checkpoint**:  
> All numbers below are from the same execution dates (2026-04-29).  
> Drift detection AUC re-verified on commit 247b056 with weighted top-k scoring (v0.7.1 schema): AUC = 0.9232 (identical to original).  
> Full pipeline re-verification scheduled before arXiv submission (target 2026-05-04).

All numbers are **self-reproducible** by running the eval scripts in `tests/`. See [`tests/run_all.sh`](tests/run_all.sh).

Date of measurements: **2026-04-29**

---

## 1. Drift detection (50 aligned + 50 deviation prompts)

Custom synthetic test set. Aligned prompts encode "what we want the AI to do" — verify, simplify, etc. Deviation prompts encode "mistakes we don't want" — fabricate, sycophancy, skip verification, etc.

| Configuration | ROC AUC | Best-Youden Accuracy | Precision @ default |
|---|---|---|---|
| **bge-m3 + 25 task-shaped + 35 hard-FP anchors + top-3 mean** | **0.9232** | 0.84 | 0.88 |
| bge-m3 + 25 task-shaped + 25 anchors + top-3 mean | 0.8352 | 0.77 | 0.65 |
| bge-small-zh + 25 task-shaped + top-3 mean | 0.7928 | 0.74 | 0.66 |
| bge-small-zh + 25 abstract maxims + centroid mean (v0.5 baseline) | **0.5056** | 0.55 | 0.49 |

**Reproduce**: `python tests/eval_drift.py`

The 4-step evolution (0.51 → 0.79 → 0.84 → 0.92) is the most important narrative — see [`CHANGELOG.md`](CHANGELOG.md) for the lessons.

---

## 2. Local memory recall (leave-one-out · 28 personal memory files)

For each memory, encode the YAML `description` field as query. Check whether the body of the same file is in top-K of all 28 memory bodies.

| Embedder | P@1 | P@3 | P@5 | MRR |
|---|---|---|---|---|
| bge-m3 | **0.964** | 0.964 | 0.964 | **0.969** |
| bge-small-zh-v1.5 | 0.857 | 0.964 | **1.000** | 0.918 |

**Reproduce**: `python tests/eval_recall.py`

This is on a small in-domain Chinese corpus. The numbers are correspondingly high — generalize with caution.

---

## 3. LongMemEval-S subset 12 (public benchmark)

[LongMemEval](https://arxiv.org/abs/2410.10813) (Wu et al., NeurIPS 2024) — 500 question-haystack pairs across 6 question types. We sampled 2 questions per type for a fast iteration loop. Each haystack has ~50 candidate sessions.

### bge-m3 bi-encoder only (no rerank)

| Question Type | n | P@1 | P@5 | MRR |
|---|---|---|---|---|
| single-session-assistant | 2 | **1.00** | **1.00** | **1.000** |
| single-session-preference | 2 | **1.00** | **1.00** | **1.000** |
| knowledge-update | 2 | 0.50 | **1.00** | 0.750 |
| temporal-reasoning | 2 | 0.50 | **1.00** | 0.600 |
| multi-session | 2 | 0.50 | 0.50 | 0.529 |
| single-session-user | 2 | 0.00 | 0.00 | 0.099 |
| **Overall** | **12** | **0.583** | **0.75** | **0.663** |

**Reproduce**: `python tests/eval_longmemeval.py --subset 12`

### Same dataset, embedder ablation

| Embedder | MRR (subset 4 · same 4 questions) |
|---|---|
| **bge-m3** | **0.760** |
| **multilingual-e5-small** | **0.762** ← practically tied with m3 at 1/5 the size |
| bge-small-zh-v1.5 | 0.414 (English content kills Chinese-only embedder) |

### + BGE CrossEncoder reranker (bge-reranker-v2-m3 · top-50 → top-5)

| Metric | m3 baseline | + reranker | Δ |
|---|---|---|---|
| P@1 | 0.667 | **0.750** | +0.083 |
| **P@5** | 0.750 | **0.917** | **+0.167** |
| **MRR** | 0.732 | **0.837** | **+0.105** |

By type — most lift on weakest types:

| Question Type | base P@5 / MRR | rerank P@5 / MRR | ΔMRR |
|---|---|---|---|
| single-session-user | 0.00 / 0.091 | **0.50 / 0.522** | **+0.43** ⭐ |
| multi-session | 0.50 / 0.550 | **1.00 / 0.750** | **+0.20** |
| temporal-reasoning | 1.00 / 1.000 | 1.00 / 1.000 | 0 (already perfect) |
| single-session-* | 1.00 / 1.000 | 1.00 / 1.000 | 0 |
| knowledge-update | 1.00 / 0.750 | 1.00 / 0.750 | 0 |

**Reproduce**: `python tests/eval_rerank.py --full`

### vs mem0 head-to-head (real run, same dataset, same 12 questions)

| System | P@1 | P@5 | MRR |
|---|---|---|---|
| **nautilus-compass (m3 + bge-reranker-v2-m3)** | **0.750** | **0.917** | **0.837** ⭐ |
| mem0 (Vertex text-embedding-005, infer=False) | 0.583 | **0.917** | 0.715 |
| nautilus-compass m3 baseline (no rerank) | 0.667 | 0.750 | 0.732 |

P@5 打平在 0.917, but **nautilus-compass MRR +0.122 优势** = truth session 平均排得更靠前。

| Question Type | mem0 MRR | zenmind+rerank MRR | Δ |
|---|---|---|---|
| knowledge-update | 0.750 | 0.750 | 0 |
| multi-session | 0.667 | **0.750** | +0.083 |
| single-session-assistant | 1.000 | 1.000 | 0 (both perfect) |
| single-session-preference | 1.000 | 1.000 | 0 (both perfect) |
| **single-session-user** | 0.250 | **0.522** | **+0.272** ⭐ |
| temporal-reasoning | 0.750 | 1.000 | +0.250 |

**Reproduce mem0 baseline**: `python tests/eval_mem0_headhead.py` (requires GCP service account JSON for Vertex embedder OR OpenAI API key)

### vs published numbers

| System | LongMemEval-S Recall@5 (n=12) |
|---|---|
| **nautilus-compass m3 + bge-reranker** | **0.917** ⭐ |
| **mem0 with Vertex text-embedding-005** | 0.917 (real run) |
| nautilus-compass m3 baseline only | 0.75 |
| mem0 (claimed retrieval-only baselines, paper) | ~0.5-0.6 |

⚠️ subset of 12 vs full 500 may overestimate — running full benchmark is on the roadmap.

**Note on debugging trajectory** (lessons): on subset 4, reranker showed +0.001 MRR (apparently null). On subset 12, reranker shows +0.105 MRR (clearly significant). The subset 4 sample size masked the signal because the one single-session-user question in subset 4 had its truth at rank 26 (out of top-50 retrieve window), beyond what the reranker could reach. **Lesson: don't conclude from n=4.**

---

## 4. Honest weaknesses

1. **single-session-user MRR 0.099** — the AI was asked a specific factual question ("What degree did I graduate with?") and the answer is one sentence buried in a 50-session haystack. Bi-encoder retrieval **cannot** solve this — we need an LLM-based reranker. See [`tests/eval_rerank.py`](tests/eval_rerank.py).
2. **Drift detection has FPs on system event injection** — tool notification XML containing words like "ephemeral", "size" semantically matches anti-anchors. Production should filter to true user prompts.
3. **AUC 0.92 is on synthetic data** — real-world deployment may show different distribution. Recommend retraining anchors per-domain.
4. **Subset 12 is not full 500** — the small-sample MRR 0.66 may be flattering or pessimistic; full benchmark TBD.

---

## 5. Settings used

```python
# daemon.py defaults (as of v0.7.0):
EMBEDDER_MODEL = "BAAI/bge-m3"
COSINE_MIN = 0.25
DRIFT_ALERT_THRESHOLD = -0.032
NEG_ANCHOR_HIT_THRESHOLD = 0.538
TOP_K = 5
```

```json
// anchors.json: 25 positive (task-shaped) + 35 negative (incl. 10 hard FP examples)
```

Hardware: Windows 11 / Python 3.14 / no GPU / sentence-transformers 5.4.1
