#!/usr/bin/env python3
# Usage: python tests/cross_judge_analysis.py <rejudged.jsonl>
"""Cross-judge agreement analysis · Gemini vs Claude on LongMemEval.

Reads the jsonl produced by tests/claude_rejudge.py (which augments
each record from eval_longmemeval_accuracy.py with claude_judge_raw /
claude_is_correct) and reports:

  · n, gemini_acc, claude_acc
  · raw agreement %
  · Cohen's kappa  (chance-corrected agreement)
  · first 20 disagreements: qid · qt · gemini · claude · truth · answer
  · per-question_type agreement table

Stdlib only — kappa is 4 lines of math. No pandas, no scipy.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def cohen_kappa(gemini: list, claude: list) -> float:
    """Binary Cohen's kappa. Inputs are parallel lists of bool.

    k = (po - pe) / (1 - pe)
      po = observed agreement
      pe = expected agreement under independence
    """
    assert len(gemini) == len(claude) and len(gemini) > 0
    n = len(gemini)
    po = sum(1 for a, b in zip(gemini, claude) if a == b) / n
    pg = sum(gemini) / n
    pc = sum(claude) / n
    pe = pg * pc + (1 - pg) * (1 - pc)
    if pe >= 1.0:
        return 1.0  # perfect marginal match · no chance disagreement possible
    return (po - pe) / (1 - pe)


def snippet(s: str, n: int = 80) -> str:
    s = (s or "").replace("\n", " ").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rejudged", help="jsonl from tests/claude_rejudge.py")
    ap.add_argument("--max-disagreements", type=int, default=20)
    args = ap.parse_args()

    path = Path(args.rejudged)
    if not path.exists():
        print(f"[error] not found: {path}", file=sys.stderr)
        return 2

    gemini_labels: list = []
    claude_labels: list = []
    disagreements: list = []
    by_qt_total: dict = defaultdict(int)
    by_qt_agree: dict = defaultdict(int)
    by_qt_gem_correct: dict = defaultdict(int)
    by_qt_cla_correct: dict = defaultdict(int)

    n_rows = 0
    n_missing = 0
    with path.open("r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                rec = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if "claude_is_correct" not in rec or "is_correct" not in rec:
                n_missing += 1
                continue
            n_rows += 1
            g = bool(rec["is_correct"])
            c = bool(rec["claude_is_correct"])
            qt = rec.get("question_type", "unknown")
            gemini_labels.append(g)
            claude_labels.append(c)
            by_qt_total[qt] += 1
            if g == c:
                by_qt_agree[qt] += 1
            if g:
                by_qt_gem_correct[qt] += 1
            if c:
                by_qt_cla_correct[qt] += 1
            if g != c and len(disagreements) < args.max_disagreements:
                disagreements.append({
                    "qid": rec.get("question_id", "?"),
                    "qt": qt,
                    "gemini": "CORRECT" if g else "INCORRECT",
                    "claude": "CORRECT" if c else "INCORRECT",
                    "truth": snippet(rec.get("truth", rec.get("answer", "")), 100),
                    "answer": snippet(rec.get("model_answer", ""), 100),
                })

    if n_rows == 0:
        print("[error] no valid rows (need both is_correct and claude_is_correct)", file=sys.stderr)
        return 1

    gem_acc = 100.0 * sum(gemini_labels) / n_rows
    cla_acc = 100.0 * sum(claude_labels) / n_rows
    n_agree = sum(1 for a, b in zip(gemini_labels, claude_labels) if a == b)
    agreement_pct = 100.0 * n_agree / n_rows
    kappa = cohen_kappa(gemini_labels, claude_labels)

    print("=" * 64)
    print(" Cross-Judge Agreement · Gemini-2.5-pro vs Claude")
    print("=" * 64)
    print(f"  n                    : {n_rows}")
    if n_missing:
        print(f"  skipped (missing)    : {n_missing}")
    print(f"  gemini_acc           : {gem_acc:.2f}%  ({sum(gemini_labels)}/{n_rows})")
    print(f"  claude_acc           : {cla_acc:.2f}%  ({sum(claude_labels)}/{n_rows})")
    print(f"  raw agreement        : {agreement_pct:.2f}%  ({n_agree}/{n_rows})")
    print(f"  Cohen's kappa        : {kappa:.4f}  ({interpret_kappa(kappa)})")
    print()

    # Per-question-type table
    print("Per question_type:")
    print(f"  {'type':<22} {'n':>5} {'agree%':>8} {'gem%':>8} {'cla%':>8}")
    print(f"  {'-' * 22} {'-' * 5} {'-' * 8} {'-' * 8} {'-' * 8}")
    for qt in sorted(by_qt_total.keys()):
        n = by_qt_total[qt]
        ap_ = 100.0 * by_qt_agree[qt] / n
        gp = 100.0 * by_qt_gem_correct[qt] / n
        cp = 100.0 * by_qt_cla_correct[qt] / n
        print(f"  {qt:<22} {n:>5} {ap_:>7.1f}% {gp:>7.1f}% {cp:>7.1f}%")
    print()

    # Disagreements
    n_dis = n_rows - n_agree
    print(f"Disagreements ({n_dis} total · showing first {min(len(disagreements), n_dis)}):")
    if not disagreements:
        print("  <none>")
    else:
        for i, d in enumerate(disagreements, 1):
            print(f"  {i:>2}. {d['qid']} [{d['qt']}]")
            print(f"      gemini={d['gemini']}  claude={d['claude']}")
            print(f"      truth : {d['truth']}")
            print(f"      answer: {d['answer']}")
    return 0


def interpret_kappa(k: float) -> str:
    """Landis & Koch (1977) interpretation."""
    if k < 0.0:
        return "worse than chance"
    if k < 0.20:
        return "slight"
    if k < 0.40:
        return "fair"
    if k < 0.60:
        return "moderate"
    if k < 0.80:
        return "substantial"
    return "almost perfect"


if __name__ == "__main__":
    sys.exit(main())
