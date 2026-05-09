#!/usr/bin/env python3
"""Summary JSON -> LaTeX table row generator for paper2.

After a full-500 eval produces `longmemeval_acc_*_summary.json`, run this
to emit a ready-to-paste LaTeX row for Table~\\ref{tab:per-type} comparing
the new run against the v0.8 baseline numbers hard-coded below.

Usage:
  py -3 paper/gen_v10_rc1_table.py <summary.json> [<baseline_summary.json>]

If baseline is omitted, the v0.8 numbers from paper2_04_eval.tex are used.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# v0.8 per-type accuracy from paper2_04_eval.tex tab:per-type
V08_BASELINE = {
    "single-session-assistant":   (56,  0.839),
    "knowledge-update":           (78,  0.577),
    "single-session-user":        (70,  0.571),
    "multi-session":              (133, 0.549),
    "single-session-preference":  (30,  0.533),
    "temporal-reasoning":         (133, 0.466),
}
V08_OVERALL = (500, 0.566)

TYPE_ORDER = [
    "single-session-assistant",
    "knowledge-update",
    "single-session-user",
    "multi-session",
    "single-session-preference",
    "temporal-reasoning",
]


def _pct(x: float) -> str:
    return f"{x*100:.1f}\\%"


def _delta(new: float, old: float) -> str:
    d = (new - old) * 100
    sign = "+" if d >= 0 else ""
    return f"{sign}{d:.1f}"


def emit_table(new_summary: dict, baseline: dict = None) -> str:
    baseline = baseline or {k: v[1] for k, v in V08_BASELINE.items()}

    by_type = new_summary.get("by_type", {})
    overall = new_summary.get("accuracy")
    n_overall = new_summary.get("n", 500)

    lines = []
    lines.append(r"\begin{table}[h]")
    lines.append(r"\centering \small")
    lines.append(r"\begin{tabular}{lrrrr}")
    lines.append(r"\toprule")
    lines.append(r"\textbf{Type} & \textbf{n} & \textbf{v0.8} & \textbf{v1.0-rc1} & \textbf{\(\Delta\)} \\")
    lines.append(r"\midrule")
    for t in TYPE_ORDER:
        n_t = V08_BASELINE[t][0]
        v08 = baseline.get(t, V08_BASELINE[t][1])
        new = by_type.get(t, {}).get("acc")
        if new is None:
            lines.append(rf"{t.replace('-', '--')} & {n_t} & {_pct(v08)} & --- & --- \\")
        else:
            lines.append(rf"{t.replace('-', '--')} & {n_t} & {_pct(v08)} & \textbf{{{_pct(new)}}} & {_delta(new, v08)} \\")
    lines.append(r"\midrule")
    if overall is not None:
        lines.append(rf"\textbf{{Overall}} & {n_overall} & {_pct(V08_OVERALL[1])} & \textbf{{{_pct(overall)}}} & \textbf{{{_delta(overall, V08_OVERALL[1])}}} \\")
    else:
        lines.append(rf"\textbf{{Overall}} & {n_overall} & {_pct(V08_OVERALL[1])} & --- & --- \\")
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\caption{v1.0-rc1 vs v0.8 on LongMemEval-S. New features:")
    lines.append(r"temporal scratch-pad prompt, ssu utterance-pair retrieval,")
    lines.append(r"self-consistency n=3 vote, top-k 5\(\to\)10 context, hybrid BM25+dense RRF.}")
    lines.append(r"\label{tab:v10-rc1}")
    lines.append(r"\end{table}")
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    new_path = Path(sys.argv[1])
    if not new_path.is_file():
        print(f"no such file: {new_path}", file=sys.stderr)
        return 1
    summary = json.loads(new_path.read_text(encoding="utf-8"))
    print(emit_table(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
