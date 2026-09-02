# compass × LongMemEval-V2

Memory backend, judge-hygiene tooling, and tuning artifacts for
[LongMemEval-V2](https://github.com/xiaowu0162/LongMemEval-V2) (Wu et al.,
arXiv 2605.12493, Apache-2.0). All credit for the benchmark itself belongs to
its authors; this package is our method implementation and evaluation
tooling, released under MIT.

## What's here

| Path | What |
|---|---|
| `compass_backend/lmev2_memory.py` | Our memory backend on the official `Memory` interface: per-state sliding-window chunks + local BGE-m3 dense + BM25/dense RRF fusion. No LLM extraction, no data egress, no LLM controller at query time. |
| `judge_hygiene/` | The rejudge tools that found and fixed a silent judge-budget failure (4096-token cap eaten by reasoning → systematic zeroing). Full story in `docs/PROTOCOL.md` §1.1. |
| `patches/` | Patches we ran against the upstream harness: abstention prompt alignment (d12), judge retry hardening, and an abstention-gate experiment (d4) that **failed our preregistered gates** and is kept for the record. |
| `docs/PROTOCOL.md` | Judge-hygiene protocol — the scoring discipline we propose every LLM-judged benchmark adopt (budget floors, dual abstention calibers, config-complete scorecards). |
| `docs/ATTRIBUTION.md` | Upstream facts, official baseline table, and honest placement of our scores. |

## Results (honest coordinates)

LME-V2-Small, reader Qwen3.5-9B, our doubao judge (full-set LLM, low/16384):

| System | Small overall |
|---|---|
| Official no-retrieval | 1.3% |
| Official RAG query→slice | 42.8% |
| **compass (this backend, tuned)** | **web 40.0% / ent 38.4%** (joint ≈39.3%) |
| Official RAG slice+notes | 51.0% |
| Official AgentRunbook-R | 58.6% |
| Official AgentRunbook-C | 74.9% |

We sit at the official entry-level RAG baseline. Two structural caliber
differences (official context budget 200k vs our 24k; official mostly
programmatic scoring vs our all-LLM judge) explain part of the gap; closing
the rest via the three-pool design + budget is our active roadmap. We publish
the full coordinate table rather than only our internal delta because our own
judge-budget incident taught us what half-reported numbers cost.

Untuned→tuned internal: web 19.6%→40.0%, ent 12.8%→38.4% (2026-08-30 →
09-02, with scoring correction).

## Quick start

```bash
git clone https://github.com/xiaowu0162/LongMemEval-V2   # upstream harness (Apache-2.0)
# place compass_backend/lmev2_memory.py into memory_modules/, register, and run
# the official evaluation scripts with a memory config pointing at it.
```

See upstream README for `@register_memory` / `insert` / `query` details.

## License & attribution

- Upstream benchmark + harness: Apache-2.0, (c) LongMemEval-V2 authors. Not redistributed here.
- This package: MIT. Patches reference upstream files but embed none of them.
