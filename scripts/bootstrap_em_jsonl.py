#!/usr/bin/env python3
"""Bootstrap 95% CI on EverMemBench per-question results.

Gives the paper a defensible confidence interval around the 44.4% headline
accuracy: instead of a bare point estimate on n=500, we report (lo, hi) at
95% so reviewers cannot dismiss compass as "could be noise vs Zep 40%".

Invoke:
  python scripts/bootstrap_em_jsonl.py [jsonl_path]

Default jsonl_path is paper/results/em_bge_v3_per_question.jsonl, the file
emitted by the patched evermembench_bge.py (see patch_evermembench_persist.py).

B=10000 nonparametric resamples is conservative for n=500 — Monte Carlo error
on the percentile bounds is well under 0.2pp, so the reported CI is stable.
Seed is fixed (20260507) so the paper number is reproducible bit-for-bit.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

DEFAULT_INPUT = Path("paper/results/em_bge_v3_per_question.jsonl")
SUMMARY_OUT = Path("paper/results/em_bge_v3_bootstrap_summary.json")
B = 10_000
SEED = 20260507
HIST_BINS = 50


def load_records(path: Path) -> list[dict]:
    if not path.is_file():
        print(f"ERR input not found: {path}", file=sys.stderr)
        sys.exit(2)
    out: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for ln, raw in enumerate(fh, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError as e:
                print(f"ERR line {ln}: {e}", file=sys.stderr)
                sys.exit(3)
            out.append(rec)
    if not out:
        print("ERR empty jsonl", file=sys.stderr)
        sys.exit(4)
    return out


def bootstrap_ci(oks: np.ndarray, rng: np.random.Generator) -> tuple[float, float, np.ndarray]:
    n = oks.shape[0]
    if n == 0:
        return (0.0, 0.0, np.zeros(B))
    idx = rng.integers(0, n, size=(B, n))
    means = oks[idx].mean(axis=1)
    lo = float(np.percentile(means, 2.5))
    hi = float(np.percentile(means, 97.5))
    return lo, hi, means


def histogram(means: np.ndarray) -> dict:
    counts, edges = np.histogram(means, bins=HIST_BINS)
    return {
        "bin_edges": [float(x) for x in edges.tolist()],
        "counts": [int(x) for x in counts.tolist()],
    }


def fmt_pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def fmt_ci(lo: float, hi: float) -> str:
    return f"({lo * 100:.1f}, {hi * 100:.1f})"


def main() -> int:
    in_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    records = load_records(in_path)

    by_topic: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        by_topic[str(rec.get("topic", "?"))].append(rec)

    rng = np.random.default_rng(SEED)
    rows: list[dict] = []

    for topic in sorted(by_topic):
        recs = by_topic[topic]
        oks = np.array([1.0 if bool(r.get("ok")) else 0.0 for r in recs])
        rec_hits = np.array([1.0 if bool(r.get("recall_hit")) else 0.0 for r in recs])
        lo, hi, means = bootstrap_ci(oks, rng)
        rows.append({
            "topic": topic,
            "n": int(oks.shape[0]),
            "n_correct": int(oks.sum()),
            "acc": float(oks.mean()),
            "recall_hit_rate": float(rec_hits.mean()),
            "acc_ci_lo": lo,
            "acc_ci_hi": hi,
            "bootstrap_hist": histogram(means),
        })

    all_oks = np.array([1.0 if bool(r.get("ok")) else 0.0 for r in records])
    all_rec = np.array([1.0 if bool(r.get("recall_hit")) else 0.0 for r in records])
    lo_all, hi_all, means_all = bootstrap_ci(all_oks, rng)
    overall = {
        "topic": "ALL",
        "n": int(all_oks.shape[0]),
        "n_correct": int(all_oks.sum()),
        "acc": float(all_oks.mean()),
        "recall_hit_rate": float(all_rec.mean()),
        "acc_ci_lo": lo_all,
        "acc_ci_hi": hi_all,
        "bootstrap_hist": histogram(means_all),
    }

    header = f"{'topic':<6} | {'n':>4} | {'acc':>6} | {'recall_hit':>10} | acc_95_CI"
    sep = "-" * len(header)
    print(header)
    print(sep)
    for row in rows:
        print(
            f"{row['topic']:<6} | {row['n']:>4} | "
            f"{fmt_pct(row['acc']):>6} | {fmt_pct(row['recall_hit_rate']):>10} | "
            f"{fmt_ci(row['acc_ci_lo'], row['acc_ci_hi'])}"
        )
    print(sep)
    print(
        f"{overall['topic']:<6} | {overall['n']:>4} | "
        f"{fmt_pct(overall['acc']):>6} | {fmt_pct(overall['recall_hit_rate']):>10} | "
        f"{fmt_ci(overall['acc_ci_lo'], overall['acc_ci_hi'])}"
    )

    SUMMARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "input": str(in_path),
        "B": B,
        "seed": SEED,
        "per_topic": rows,
        "overall": overall,
    }
    SUMMARY_OUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nsummary -> {SUMMARY_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
