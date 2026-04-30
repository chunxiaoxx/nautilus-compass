# Contributing to zenmind-mem

Thanks for considering a contribution! Two big ways to help:

## 1. Add anchors for new domains

`anchors.json` (default) covers a Chinese/English engineering+research context. We need domain-specific anchor sets for:

- `anchors_legal.json` — legal research / contract drafting
- `anchors_medical.json` — clinical reasoning / case review
- `anchors_finance.json` — trading / risk / compliance
- ...

PRs that add an `anchors_<domain>.json` file are welcome. Each anchor file:
- Must have 25+ positive_anchors (task-shaped, not maxims — see existing file)
- Must have 25+ negative_anchors (concrete patterns the AI should NOT slip into)
- Test it: `ZMM_EMBEDDER_MODEL=BAAI/bge-m3 python tests/eval_drift.py` should show ROC AUC ≥ 0.75

The auto-selection in `recall.py:_select_anchors_path()` picks based on `cwd`. Add your domain pattern there.

## 2. Run public benchmarks

We have first numbers on LongMemEval-S subset 12. Help us:

- Run **full LongMemEval-S 500** (estimated ~1.5h on m3 + Linux). PR the result to `RESULTS.md`.
- Run on **PerLTQA** (Chinese long-term memory benchmark). Adapter not yet written.
- Run **head-to-head with mem0** on the same dataset. Requires OpenAI/Anthropic API key.

## 3. Drift detection improvements

The 4-step evolution (0.51 → 0.92 AUC) is documented in [CHANGELOG.md](CHANGELOG.md). Open ideas:

- Tri-band output already implemented (aligned / neutral / deviation)
- **Stretch goal**: dynamic anchor weighting (recently-confirmed anchors get more weight, ebbinghaus decay)
- **Stretch goal**: PostToolUse drift (catch AI mid-action, not just at prompt time)

## Dev setup

```bash
git clone <repo>
cd zenmind-mem
pip install -e .[dev,modelscope]
python tests/run_all.sh         # full eval suite (~5 min on small-zh, ~30 min on m3)
ruff check .
```

Eval scripts read `ZMM_EMBEDDER_MODEL` env var. Set it before runs.

## Code style

- `ruff` for lint (config in `pyproject.toml`)
- Functions ideally < 50 lines, files < 500
- Comments explain *why*, not *what*
- No emojis in code (only in user-facing hook output where they convey meaning)

## License of contributions

By submitting a PR you agree your contribution is MIT-licensed. Anchors files are CC0.
