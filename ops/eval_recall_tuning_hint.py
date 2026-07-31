#!/usr/bin/env python3
"""Convert eval_recall artifact into concrete tuning actions.

Usage:
  python ops/eval_recall_tuning_hint.py --artifact .cache/eval_recall.json
  python ops/eval_recall_tuning_hint.py --artifact ... --out .cache/eval_recall_tuning_hint.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

PRIORITY_WEIGHT = {
    "critical": 3,
    "high": 2,
    "medium": 1,
    "low": 0,
}


def read_artifact(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _collect_blocking_reason(recs) -> str:
    if not recs:
        return ""
    blocks = [
        r for r in recs
        if r.get("priority") in ("critical", "high")
        or r.get("action") in ("seed_memory_corpus",)
    ]
    if not blocks:
        return ""
    return " | ".join(r.get("reason", "").strip() for r in blocks if r.get("reason"))


def derive_next_actions(artifact: dict) -> dict:
    recs = artifact.get("recommendations", [])
    if not isinstance(recs, list):
        recs = []

    # keep deterministic priority order for planning systems
    recs_sorted = sorted(
        recs,
        key=lambda x: PRIORITY_WEIGHT.get(x.get("priority", "low"), 0),
        reverse=True,
    )

    next_actions = []
    for r in recs_sorted:
        action = {
            "priority": r.get("priority", "low"),
            "action": r.get("action", "unknown"),
            "reason": r.get("reason", ""),
            "next_step": r.get("next_step", ""),
            "evidence": r.get("evidence", {}),
        }
        next_actions.append(action)

    risk = "none"
    if any(x.get("priority") in ("critical", "high") for x in recs):
        risk = "high"
    elif any(x.get("priority") == "medium" for x in recs):
        risk = "medium"
    elif recs:
        risk = "low"

    blocking_reason = _collect_blocking_reason(recs)
    if risk == "low" and not blocking_reason:
        blocking_reason = ""

    summary = artifact.get("result_summary", {})
    delta_values = [
        v.get("delta_mrr_vs_flat")
        for v in summary.values()
        if isinstance(v, dict) and isinstance(v.get("delta_mrr_vs_flat"), (int, float))
    ]
    max_mrr_gain = max(delta_values) if delta_values else 0.0

    return {
        "next_actions": next_actions,
        "risk": risk,
        "blocking_reason": blocking_reason,
        "artifact_source": artifact.get("meta", {}).get("out_file"),
        "summary": {
            "n_memories": artifact.get("meta", {}).get("n_memories", 0),
            "n_impact": artifact.get("meta", {}).get("n_impact", 0),
            "n_tier_nonworking": artifact.get("meta", {}).get("n_tier_nonworking", 0),
            "max_delta_mrr_vs_flat": max_mrr_gain,
        },
    }


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact", required=True)
    ap.add_argument("--out")
    return ap.parse_args()


def main():
    args = parse_args()
    artifact_path = Path(args.artifact)
    artifact = read_artifact(artifact_path)

    out = derive_next_actions(artifact)
    out["generated_by"] = "ops/eval_recall_tuning_hint.py"
    out["artifact"] = str(artifact_path)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
