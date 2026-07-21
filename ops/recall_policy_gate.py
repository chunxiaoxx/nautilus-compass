#!/usr/bin/env python3
"""Build a machine-readable recall policy gate from raw-vs-guarded artifacts.

The gate does not decide whether the whole benchmark run is valid. It decides
whether lifecycle re-ranking is allowed to become the default policy.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

MODES = ("poi", "tier", "gemini")
NEGATIVE_DELTA_MIN = -0.0005
POSITIVE_DELTA_MIN = 0.005


def read_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _mode_delta(artifact: dict, mode: str) -> float:
    item = artifact.get("result_summary", {}).get(mode, {})
    value = item.get("delta_mrr_vs_flat", 0.0)
    return float(value) if isinstance(value, (int, float)) else 0.0


def _collect_deltas(artifact: dict) -> dict:
    return {mode: _mode_delta(artifact, mode) for mode in MODES}


def _negative_modes(deltas: dict, threshold: float) -> list:
    return [
        {"mode": mode, "delta_mrr_vs_flat": delta}
        for mode, delta in deltas.items()
        if delta < threshold
    ]


def build_policy_gate(
    *,
    raw: dict,
    guarded: dict,
    negative_delta_min: float = NEGATIVE_DELTA_MIN,
    positive_delta_min: float = POSITIVE_DELTA_MIN,
) -> dict:
    raw_deltas = _collect_deltas(raw)
    guarded_deltas = _collect_deltas(guarded)
    raw_negative = _negative_modes(raw_deltas, negative_delta_min)
    guarded_negative = _negative_modes(guarded_deltas, negative_delta_min)
    raw_best = max(raw_deltas.values()) if raw_deltas else 0.0

    if raw_negative:
        gate = "block_raw_lifecycle_promotion"
        raw_allowed = False
        recommended = "guarded"
    elif guarded_negative:
        gate = "block_all_lifecycle_promotion"
        raw_allowed = False
        recommended = "flat"
    elif raw_best >= positive_delta_min:
        gate = "raw_lifecycle_candidate"
        raw_allowed = True
        recommended = "raw"
    else:
        gate = "no_measurable_lifecycle_uplift"
        raw_allowed = False
        recommended = "guarded"

    return {
        "version": "1.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "gate": gate,
        "promotion": {
            "raw_lifecycle_allowed": raw_allowed,
            "recommended_default": recommended,
            "positive_delta_min": positive_delta_min,
            "negative_delta_min": negative_delta_min,
        },
        "corpus": {
            "n_memories": raw.get("meta", {}).get("n_memories"),
            "n_impact": raw.get("meta", {}).get("n_impact"),
            "n_tier_nonworking": raw.get("meta", {}).get("n_tier_nonworking"),
        },
        "policies": {
            "raw": raw.get("meta", {}).get("signal_policy", "raw"),
            "guarded": guarded.get("meta", {}).get("signal_policy", "guarded"),
        },
        "deltas": {
            "raw": raw_deltas,
            "guarded": guarded_deltas,
        },
        "evidence": {
            "raw_negative_modes": raw_negative,
            "guarded_negative_modes": guarded_negative,
            "raw_best_delta_mrr_vs_flat": raw_best,
        },
    }


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, help="raw eval_recall artifact")
    ap.add_argument("--guarded", required=True, help="guarded eval_recall artifact")
    ap.add_argument("--out", help="optional output JSON path")
    ap.add_argument("--negative-delta-min", type=float, default=NEGATIVE_DELTA_MIN)
    ap.add_argument("--positive-delta-min", type=float, default=POSITIVE_DELTA_MIN)
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    gate = build_policy_gate(
        raw=read_json(Path(args.raw)),
        guarded=read_json(Path(args.guarded)),
        negative_delta_min=args.negative_delta_min,
        positive_delta_min=args.positive_delta_min,
    )

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(gate, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(gate, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
