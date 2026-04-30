# Changelog

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
