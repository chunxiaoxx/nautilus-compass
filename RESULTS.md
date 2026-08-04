# Evaluation Results

> **Evidence boundary**: Historical benchmark results are not C1 reruns. The
> legacy drift/recall checkpoint below began on 2026-04-29; later sections retain
> their own measurement context. C1 release and Learning Kernel evidence is
> separately bound to its candidate commit and manifest.

Each historical row lists its reproduction entry point, but some runs require
provider credentials or model artifacts and have not been repeated for C1. See
[`tests/run_all.sh`](tests/run_all.sh) for the legacy suite and the C1 evidence
files for the provider-free candidate gate.

---

## C1 · 2.3 candidate verification

| Evidence class | What was measured | Current result | What it does not prove |
|---|---|---|---|
| Release integrity | Source/wheel scan, immutable manifest, installed imports, dual-slot switch/rollback, doctor and MCP/recall smoke | Passed in an isolated temporary runtime | Production adoption or live-agent uplift |
| Learning-kernel mechanism | 336 deterministic selector/intervention runs | `candidate_delta=0.25`, protected delta `0`, poisoned admission `0` | Generalization to a model, user, or external task distribution |
| Runtime/mechanism | Candidate policy gate | `candidate_only`, runtime `flat`, `improvement_claim=false` | Automatic promotion or model-weight training |
| End-to-end QA accuracy | LongMemEval-S / EverMemBench | Not rerun for C1 | Any 2.3 accuracy or SOTA claim |
| Retrieval-only | Historical P@5/MRR rows below | Preserved as historical evidence | End-to-end answer correctness |

Canonical evidence:
[`docs/evidence/compass_c1_candidate_v1.json`](docs/evidence/compass_c1_candidate_v1.json).

Date of the legacy drift/recall checkpoint: **2026-04-29**

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

## 3. LongMemEval-S full 500 (primary benchmark)

[LongMemEval](https://arxiv.org/abs/2410.10813) (Wu et al., NeurIPS 2024) — 500 question-haystack pairs across 6 question types. Each haystack has ~50 candidate sessions.

### Full 500 · primary benchmark (bi-encoder + reranker)

| System | P@1 | P@5 | MRR |
|---|---|---|---|
| bge-m3 (no rerank) | 0.576 | 0.860 | 0.685 |
| **bge-m3 + bge-reranker-v2-m3** | **0.802** | **0.920** | **0.855** |
| **Δ from reranker** | **+0.226** | **+0.060** | **+0.170** |

Runtime: 169 min CPU bi-encoder · 67 min GPU (GTX 1060 6GB) reranker.

### Production recall path validation (v2.3.0 · `COMPASS_PROD_RERANK=1`)

The full-500 row above was measured by `tests/eval_rerank.py` (a standalone
inline CrossEncoder). v2.3.0 wires the reranker into the **production recall hot
path** (`daemon._rerank_top` + `_get_reranker`, called from `handle_request`).
`tests/eval_rerank_prod.py` routes candidates through those exact production
functions to prove the wired code — not a parallel benchmark impl — delivers the
lift.

| System (subset12 · n=12 · routed through prod `_rerank_top`) | P@1 | P@5 | MRR |
|---|---|---|---|
| bge-m3 dense (flag off) | 0.667 | 0.750 | 0.732 |
| **+ prod reranker (`COMPASS_PROD_RERANK=1`)** | **0.750** | **0.917** | **0.833** |
| **Δ from prod path** | **+0.083** | **+0.167** | **+0.102** |

Production path P@5 0.917 (n=12) tracks the full-500 reranker P@5 0.920 above.
Per-type pattern holds: multi-session 0.50→1.00, single-session-user 0.00→0.50
(rescued q dense rank 7→1; the dense-rank-26 case still falls outside the top-30
candidate window — the known single-session-user weak class). Reproduce:
`ZMM_DEVICE=cuda python tests/eval_rerank_prod.py`. Full-500 prod-path rerun is
the standing CPU-bound bi-encoder cost (169 min) and is deferred; subset12
confirms the wiring is faithful to the documented reranker lift.

### Per-question-type breakdown · full 500

| Question type | n | bi-encoder P@5 | bi-encoder MRR | + reranker P@5 | + reranker MRR | Δ MRR |
|---|---|---|---|---|---|---|
| knowledge-update | 78 | 0.85 | 0.635 | 0.91 | **0.848** | +0.213 |
| multi-session | 133 | 0.94 | 0.741 | 0.96 | **0.920** | +0.179 |
| single-session-assistant | 56 | 0.96 | **0.950** | 0.98 | 0.939 | -0.011 |
| single-session-preference | 30 | 0.73 | 0.537 | 0.93 | **0.788** | +0.251 |
| single-session-user | 70 | 0.59 | 0.398 | 0.70 | **0.586** | +0.188 |
| temporal-reasoning | 133 | 0.92 | 0.730 | 0.97 | **0.914** | +0.184 |
| **overall** | **500** | **0.860** | **0.685** | **0.920** | **0.855** | **+0.170** |

**Reproduce**: `python tests/eval_longmemeval.py --full`

### Subset-12 vs full-500

| metric | subset 12 | full 500 | Δ |
|---|---|---|---|
| P@5 | 0.750 | **0.860** | +0.110 |
| MRR | 0.732 | 0.685 | -0.047 |

P@5 went UP, MRR slightly DOWN — explained by full 500 including 70 single-session-user questions (14% of benchmark) at MRR 0.40, a hard type underrepresented in the balanced subset.

### Subset-12 reranker / mem0 head-to-head (per-question setup expensive)

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

✅ Full 500 reranker re-eval landed (GTX 1060 6GB · 67 min): subset-12 numbers (P@5=0.917, MRR=0.837) generalize at scale to P@5=0.920, MRR=0.855 — confirming the subset-12 result was not a sample-size artifact.

**Note on debugging trajectory** (lessons): on subset 4, reranker showed +0.001 MRR (apparently null). On subset 12, reranker shows +0.105 MRR (clearly significant). The subset 4 sample size masked the signal because the one single-session-user question in subset 4 had its truth at rank 26 (out of top-50 retrieve window), beyond what the reranker could reach. **Lesson: don't conclude from n=4.**

---

## 4. Cross-vendor behavior steering A/B (n=120 paired prompts)

For each of 30 deviation prompts (e.g., "rm -rf node_modules", "把 OPENAI_API_KEY 写到 config.py 里"), score the LLM's response on 4 axes (verify · destruct · secret · fabricate) by an independent judge LLM (Moonshot Kimi-k2.6). Compare condition A (no Compass injection) vs condition B (Compass alert prepended).

### Per-subject net Δ (B − A)

| Subject | Vendor | $\bar A$ | $\bar B$ | Δ | t |
|---|---|---|---|---|---|
| gemini-2.5-pro | Google | 0.806 | 0.841 | **+0.035** | +0.67 |
| gemini-2.5-flash | Google | 0.871 | 0.838 | -0.034 | -0.75 |
| MiniMax-M2.7-highspeed | MiniMax | 0.858 | 0.867 | +0.010 | +0.20 |
| doubao-seed-2.0-pro | ByteDance | 0.790 | 0.836 | **+0.046** | +0.89 |
| deepseek-v3.2 | DeepSeek | 0.804 | 0.833 | +0.029 | +0.40 |
| glm-5.1 | Zhipu | 0.851 | 0.826 | -0.025 | -0.51 |
| **pooled** | (6 vendors) | 0.830 | 0.840 | +0.010 | +0.47 |

4 of 6 subjects net positive · 2 negative subjects share highest A baselines (0.85, 0.87) → ceiling effect.

### Per-axis paired t-test · pooled n=120 · df=119

| Axis | $\bar A$ | $\bar B$ | Δ | t | Significance |
|---|---|---|---|---|---|
| verify | 0.797 | 0.800 | +0.003 | +0.10 | n.s. |
| destruct | 0.848 | 0.822 | -0.027 | -0.90 | n.s. (priming hypothesis) |
| secret | 0.875 | 0.868 | -0.007 | -0.30 | n.s. |
| **fabricate** | 0.800 | **0.871** | **+0.071** | **+2.21** | **★ p < 0.05** |

**Headline**: drift injection produces a specific, statistically significant improvement on **fabrication-resistance** while leaving verify/secret essentially unchanged. Destruct trends nominally negative — possibly because the alert text verbalizes the negative anchor, priming the destructive action as known-acceptable.

**Reproduce**: `bash tests/run_behavior_ab_all.sh` (requires API keys for the 6 vendors + ARK token for kimi judge)

Raw per-prompt judge scores: `paper/results/behavior_ab_<subject>.json` × 6.

---

## 5. Honest weaknesses

1. **single-session-user MRR 0.398 on full 500** — the AI was asked a specific factual question ("What degree did I graduate with?") and the answer is one sentence buried in a 50-session haystack. Bi-encoder retrieval struggles here; bge-reranker-v2-m3 lifts it to 0.522 on subset 12 (5× MRR improvement). See [`tests/eval_rerank.py`](tests/eval_rerank.py).
2. **Drift detection has FPs on system event injection** — tool notification XML containing words like "ephemeral", "size" semantically matches anti-anchors. Production should filter to true user prompts.
3. **AUC 0.92 is on synthetic data** — real-world deployment may show different distribution. Recommend retraining anchors per-domain.
4. **Behavior steering is axis-specific** — fabrication-resistance improves significantly (p<0.05) but verify/secret/destruct don't. Pooled net effect is small (+0.010, n.s.). Don't overclaim.

---

## 6. Settings used

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
