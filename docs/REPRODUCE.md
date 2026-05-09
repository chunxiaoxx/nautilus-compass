# Reproduction guide · papers + benchmarks

> One-page "how do I get the numbers" guide for reviewers and external
> independent replicators. Two papers, three benchmarks, one drift detector.

---

## TL;DR

Every number in our two papers is reproducible from inputs in this repo.
Three benchmarks; each has a runner script and a frozen log of our run.

| Number you want | Run this | Frozen log |
|---|---|---|
| LongMemEval-S 56.6% (Paper 2 abstract) | `python scripts/eval_lme.py --model deepseek-v3.2-thinking` | `paper/RESULTS_v0.8.md` |
| EverMemBench-Dynamic 44.4% / 47.3% (Paper 2) | `python scripts/evermembench_bge.py` | `paper/results/em_bge_v3_per_question.jsonl` |
| Drift AUC 0.83 held-out (Paper 1) | `python scripts/eval_drift.py --split heldout` | `paper/results/drift_heldout_50_50.json` |
| Bootstrap 95% CI on EverMemBench (Paper 2 §6.5) | `python scripts/bootstrap_em_jsonl.py paper/results/em_bge_v3_per_question.jsonl` | `paper/results/em_bge_v3_bootstrap_summary.json` |
| Cross-judge κ=0.70 vs Gemini (Paper 2 §6.5) | `python scripts/cross_judge_em_gemini_vertex.py` | `paper/results/em_cross_judge_gemini_per_question.jsonl` |

---

## Setup (one-time)

```bash
# 1. Clone
git clone https://github.com/chunxiaoxx/nautilus-compass
cd nautilus-compass

# 2. Python env (3.9+)
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .[dev]

# 3. Embedder daemon (BGE-m3 at 127.0.0.1:9876)
bash daemon_start.sh
# Cold load ~30 s · subsequent <200 ms
```

If you don't want to run the BGE-m3 daemon locally (it needs ~8 GB RAM
or GPU for speed), point `COMPASS_EMBED_BASE` at our hosted endpoint:

```bash
export COMPASS_EMBED_BASE=https://compass.nautilus.social/v1/embed
# free tier 1k embeddings/day; sign up for more
```

---

## Paper 1 reproduction · drift detection

### Datasets

- **In-set (anchor authoring data, AUC 0.92)**: `paper/data/drift_inset.jsonl`
  · 220 prompt-response pairs · the 60 anchors were authored from this
- **Held-out (Paper 1 headline AUC 0.83)**: `paper/data/drift_heldout_50_50.jsonl`
  · 100 prompt-response pairs · 50 aligned + 50 deviation, frozen 2026-04-29

### Run

```bash
python scripts/eval_drift.py \
    --anchors anchors_platform_base.json \
    --split heldout \
    --output paper/results/drift_heldout_50_50.json
# Expected: AUC 0.83 (±0.01), threshold -0.032 at best Youden's J
```

### Verify

```bash
python -c "
import json
d = json.load(open('paper/results/drift_heldout_50_50.json'))
print('AUC:', round(d['auc'], 3))
"
# AUC: 0.83
```

---

## Paper 2 reproduction · LongMemEval-S 56.6%

### Dataset

LongMemEval-S 500-question public split from
[Wu et al. 2024](https://arxiv.org/abs/2410.10813). Place at
`paper/data/longmemeval_s.jsonl` (we don't redistribute their data).

### Run

```bash
# v0.8 locked config: DeepSeek V3.2 thinking + 5-stage retrieval
export DEEPSEEK_API_KEY=sk-...
python scripts/eval_lme.py \
    --config paper/configs/lme_v0.8.yaml \
    --output paper/results/lme_v0.8.json
# ~5.6 hours · ~$3.50 LLM API · expected 56.6%
```

### Verify

```bash
grep "OVERALL" paper/RESULTS_v0.8.md
# OVERALL  n=500 · acc=56.6%
```

---

## Paper 2 reproduction · EverMemBench-Dynamic 44.4-47.3%

### Dataset

EverMemBench-Dynamic 5-topic public release from
[Hu et al. 2026](https://arxiv.org/abs/2401.13961). Place at
`paper/data/evermembench_dynamic/`.

### Run (one independent run = ~5.6 h on T4)

```bash
export DEEPSEEK_API_KEY=sk-...
python scripts/evermembench_bge.py \
    --output paper/results/em_per_question.jsonl
# Run 1 (2026-05-07) yielded 44.4% on n=500
# Run 2 (2026-05-08) yielded 47.3% on n=497 (3 transient API skips)
```

### Bootstrap 95% CI on Run 2

```bash
python scripts/bootstrap_em_jsonl.py paper/results/em_bge_v3_per_question.jsonl
# ALL  n=497  acc=47.3%  95% CI=(42.9, 51.7)
```

### Cross-judge with Gemini (Vertex AI)

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa.json
python scripts/cross_judge_em_gemini_vertex.py \
    paper/results/em_bge_v3_per_question.jsonl 100 \
    --model gemini-2.5-pro
# Expected: gemini_acc 28%, deepseek_acc 42%, kappa 0.70
# 14 disagreements all DS=Y/Gemini=N (judge-family bias documented in §6.5)
```

The frozen Gemini per-question log lives at
`paper/results/em_cross_judge_gemini_per_question.jsonl` so reviewers can
inspect the 14 disagreements without re-running the API ($1.50 saved).

---

## Verifying our locked numbers without re-running anything

If you trust our frozen logs and just want to check the math, run:

```bash
python scripts/bootstrap_em_jsonl.py paper/results/em_bge_v3_per_question.jsonl
# 5 sec · pure numpy bootstrap · no API calls
```

This confirms the published 47.3% [42.9, 51.7] CI from the per-question log.

---

## Hardware footprint

| Workload | Min spec | Comfortable spec |
|---|---|---|
| BGE-m3 daemon | 8 GB RAM CPU | 16 GB RAM, 1 × T4 / 3060 |
| Drift eval (held-out 100 questions) | 4 GB RAM | 8 GB RAM |
| LongMemEval-S 500 | 4 GB RAM (LLM is API) | 8 GB RAM |
| EverMemBench 500 | 8 GB RAM (LLM is API) | 16 GB RAM, 1 × T4 |

We ran all three eval workloads on a single Tencent Cloud T4 VM
(16 GB RAM, T4 GPU 16 GB VRAM, $0.50/hour); total ~12 hours wall-clock,
~$50 LLM API cost end-to-end.

---

## Common reproduction failures & fixes

| Symptom | Cause | Fix |
|---|---|---|
| `ConnectionRefused 127.0.0.1:9876` | daemon not started | `bash daemon_start.sh` |
| `sentence_transformers OOM` | <8 GB RAM | use hosted embedder via `COMPASS_EMBED_BASE` |
| `429 Too Many Requests` from DeepSeek | rate limit hit | reduce `max_concurrent` in config to 4 |
| Run 1 vs Run 2 acc diff > 5 pts | LLM-judge stochasticity | expected · see Paper 2 §6.5 |
| Gemini judge says everything INCORRECT | Vertex AI returning empty `parts[]` | check `max_tokens >= 256` (gemini-2.5-pro reserves thoughts tokens) |
| `AUC < 0.7` on drift held-out | wrong anchors loaded | confirm `anchors_platform_base.json` is the v1.0.0 set; do not use `anchors_adapted.json` |

---

## Citation reminder

Please cite both papers if you reproduce or build on the eval setup:

```bibtex
@misc{nautiluscompass-drift-2026, ... }
@misc{nautiluscompass-memrecall-2026, ... }
```

Full bib in [README.md](../README.md#citation).

Bug reports / reproduction failures → open a GitHub issue with the
command you ran and the unexpected output. We aim for 48 h triage.
