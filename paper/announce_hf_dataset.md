# Nautilus Compass · HF Dataset v1.2 Released

**TL;DR**: First public release of behavioral anchors for black-box LLM agent persona drift detection — MIT, no PII, jsonl-ready.

**Dataset**: https://huggingface.co/datasets/chunxiaox/nautilus-compass-test-data
**Code**: https://github.com/chunxiaoxx/nautilus-compass
**Demo Space**: https://huggingface.co/spaces/chunxiaox/nautilus-compass

## What shipped (2026-05-13)

68 behavioral anchors (31 positive + 37 negative · English · jsonl) used by Nautilus Compass to score agent persona drift turn-by-turn:

```python
from datasets import load_dataset
ds = load_dataset(
    "chunxiaox/nautilus-compass-test-data",
    "marketing-anchors-v1.2",
    split="anchors"
)
```

## The core idea

Most agent-safety monitors are post-hoc — they classify the final output. Compass measures drift turn-by-turn with one cosine call:

```
drift_score(msg) =
    topk_mean( cos(BGE-m3(msg), positive_anchors) )
  - topk_mean( cos(BGE-m3(msg), negative_anchors) )
```

No model internals · no entity extraction at index time · no LLM in the request path. The whole detection step is one embedding + cosine.

**Held-out drift detection AUC = 0.83** (paper in arxiv moderation).

## Why this anchor pack

This release covers the **compass project's own marketing-copy agent** — meaning it's the anchor pack we dogfood on our own outreach drafts. Calibrated against 13 blog drafts; round-2 anchors rewritten to extreme-literal phrasing to suppress topical false positives.

## Coming next

- `roc-eval-v1` · labeled drift-detection ROC data (cosine + binary labels · ~500 utterances) · ETA 2-3 days
- `claude-code-sessions-v1` · redacted multi-turn agent traces · ETA 2-3 weeks
- `anchors-domain-{finance,legal,medical}` · per-domain anchor packs · community-contributed welcome

## Who should care

- **LLM agent builders** running anything multi-turn in production
- **Safety researchers** measuring persona drift / jailbreak trajectory (Foot-in-the-Door style)
- **Memory layer maintainers** comparing black-box vs. white-box trade-offs (Mem0g/OMEGA at 90%+ LongMemEval vs. Compass 56.6% with zero LLM-extraction cost)

## License & contribution

MIT · contributions welcome at github.com/chunxiaoxx/nautilus-compass · open an issue if you want a new domain anchor pack.

Thanks to **Niels Rogge** (Hugging Face open-source team) for the onboarding push.
