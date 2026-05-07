"""compass · paper2 · cross-judge agreement analysis.

Compares two LongMemEval-S evaluation runs (same subject · different judge)
to compute self-judge bias.

For paper §6 Limitations · we need:
  · agreement % (same verdict on same question)
  · per-type agreement
  · confusion matrix · where do judges disagree

Usage:
  python tools/cross_judge_analysis.py \
    --self  .cache/longmemeval_acc_m3_rerank_full_<v0.8_ts>.jsonl \
    --cross .cache/longmemeval_acc_m3_rerank_full_<crossjudge_ts>.jsonl \
    --output paper/results/cross_judge_analysis.json

Expected output:
  · overall_agreement: 0.95 → very low self-judge bias (good for paper)
  · overall_agreement: 0.80 → moderate · noted in limitations
  · overall_agreement: <0.70 → significant bias · paper claim weakened
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def _is_correct(d: dict) -> bool:
    """Normalize is_correct field · jsonl stores as string sometimes."""
    v = d.get("is_correct")
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.lower() in ("true", "1", "yes")
    if isinstance(v, (int, float)):
        return bool(v)
    return False


def load_jsonl(path: Path) -> dict:
    """Load per-question results · keyed by question_id."""
    by_qid = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                qid = obj.get("question_id") or obj.get("qid")
                if qid:
                    by_qid[qid] = obj
            except Exception:
                continue
    return by_qid


def compute_agreement(self_run: dict, cross_run: dict) -> dict:
    """Returns full agreement breakdown."""
    common = set(self_run) & set(cross_run)
    if not common:
        return {"error": "no common questions", "self_n": len(self_run), "cross_n": len(cross_run)}

    overall_self = sum(1 for qid in common if _is_correct(self_run[qid]))
    overall_cross = sum(1 for qid in common if _is_correct(cross_run[qid]))
    agree = sum(1 for qid in common if _is_correct(self_run[qid]) == _is_correct(cross_run[qid]))
    n = len(common)

    by_type_data = defaultdict(lambda: {"agree": 0, "total": 0,
                                          "self_correct": 0, "cross_correct": 0,
                                          "self_only": 0, "cross_only": 0})
    for qid in common:
        s = self_run[qid]
        c = cross_run[qid]
        qtype = s.get("question_type") or c.get("question_type") or "?"
        d = by_type_data[qtype]
        d["total"] += 1
        if _is_correct(s):
            d["self_correct"] += 1
        if _is_correct(c):
            d["cross_correct"] += 1
        if _is_correct(s) == _is_correct(c):
            d["agree"] += 1
        elif _is_correct(s) and not _is_correct(c):
            d["self_only"] += 1
        elif _is_correct(c) and not _is_correct(s):
            d["cross_only"] += 1

    by_type = {}
    for qtype, d in by_type_data.items():
        n_t = d["total"]
        by_type[qtype] = {
            "n": n_t,
            "self_acc": round(d["self_correct"] / n_t, 3) if n_t else 0,
            "cross_acc": round(d["cross_correct"] / n_t, 3) if n_t else 0,
            "agreement": round(d["agree"] / n_t, 3) if n_t else 0,
            "self_only_correct": d["self_only"],
            "cross_only_correct": d["cross_only"],
            "delta_acc": round((d["self_correct"] - d["cross_correct"]) / n_t, 3) if n_t else 0,
        }

    # Confusion matrix
    confusion = {"both_right": 0, "both_wrong": 0, "self_only": 0, "cross_only": 0}
    for qid in common:
        s_ok = _is_correct(self_run[qid])
        c_ok = _is_correct(cross_run[qid])
        if s_ok and c_ok:
            confusion["both_right"] += 1
        elif not s_ok and not c_ok:
            confusion["both_wrong"] += 1
        elif s_ok and not c_ok:
            confusion["self_only"] += 1
        elif c_ok and not s_ok:
            confusion["cross_only"] += 1

    return {
        "n_common": n,
        "self_run_n": len(self_run),
        "cross_run_n": len(cross_run),
        "overall": {
            "self_acc": round(overall_self / n, 3),
            "cross_acc": round(overall_cross / n, 3),
            "agreement": round(agree / n, 3),
            "delta_acc": round((overall_self - overall_cross) / n, 3),
        },
        "confusion_matrix": confusion,
        "self_judge_bias_estimate": {
            "absolute_pts": round(abs(overall_self - overall_cross) / n, 3),
            "kappa_proxy": round(2 * agree / n - 1, 3),
            "interpretation": _interpret_agreement(agree / n),
        },
        "by_question_type": by_type,
    }


def _interpret_agreement(rate: float) -> str:
    if rate >= 0.95:
        return "Excellent · very low self-judge bias · paper claim strong"
    if rate >= 0.85:
        return "Good · low self-judge bias · paper claim defensible"
    if rate >= 0.75:
        return "Moderate · documented bias · note in §Limitations"
    if rate >= 0.65:
        return "Poor · significant bias · paper claim weakened · investigate"
    return "Critical · likely model collusion · re-design eval"


def format_report(analysis: dict) -> str:
    """Human-readable report for paper / CHANGELOG."""
    if "error" in analysis:
        return f"[ERROR] {analysis['error']} · self_n={analysis.get('self_n')} · cross_n={analysis.get('cross_n')}"

    o = analysis["overall"]
    bias = analysis["self_judge_bias_estimate"]
    conf = analysis["confusion_matrix"]
    n = analysis["n_common"]

    lines = [
        "=" * 60,
        "Cross-Judge Replication · Self-Judge Bias Analysis",
        "=" * 60,
        f"\n  n_common questions:  {n}",
        f"  self-judge acc:      {o['self_acc']:.3f}",
        f"  cross-judge acc:     {o['cross_acc']:.3f}",
        f"  delta:               {o['delta_acc']:+.3f}",
        "",
        f"  agreement rate:      {o['agreement']:.1%}",
        f"  bias (abs pts):      {bias['absolute_pts']:.3f}",
        f"  Cohen κ proxy:       {bias['kappa_proxy']:.3f}",
        "",
        f"  → {bias['interpretation']}",
        "",
        "Confusion matrix:",
        f"  both right:    {conf['both_right']:4d}  ({conf['both_right']/n*100:.1f}%)",
        f"  both wrong:    {conf['both_wrong']:4d}  ({conf['both_wrong']/n*100:.1f}%)",
        f"  self only OK:  {conf['self_only']:4d}  ({conf['self_only']/n*100:.1f}%)",
        f"  cross only OK: {conf['cross_only']:4d}  ({conf['cross_only']/n*100:.1f}%)",
        "",
        "Per question_type:",
    ]
    for qtype, d in sorted(analysis["by_question_type"].items()):
        lines.append(
            f"  {qtype:32s} n={d['n']:3d}  "
            f"self={d['self_acc']:.3f}  cross={d['cross_acc']:.3f}  "
            f"agreement={d['agreement']:.1%}  Δ={d['delta_acc']:+.3f}"
        )
    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--self", dest="self_path", required=True, type=Path,
                   help="Self-judge run (e.g. v0.8 final · DeepSeek subject + DeepSeek judge)")
    p.add_argument("--cross", dest="cross_path", required=True, type=Path,
                   help="Cross-judge run (e.g. DeepSeek subject + GLM-5.1 judge)")
    p.add_argument("--output", type=Path, default=None,
                   help="Save analysis JSON · prints report to stdout always")
    args = p.parse_args()

    if not args.self_path.exists():
        sys.exit(f"self_path not found: {args.self_path}")
    if not args.cross_path.exists():
        sys.exit(f"cross_path not found: {args.cross_path}")

    self_run = load_jsonl(args.self_path)
    cross_run = load_jsonl(args.cross_path)
    print(f"[load] self_run={len(self_run)} · cross_run={len(cross_run)}")

    analysis = compute_agreement(self_run, cross_run)
    report = format_report(analysis)
    print(report)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(analysis, ensure_ascii=False, indent=2),
                               encoding="utf-8")
        print(f"\n[save] analysis → {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
