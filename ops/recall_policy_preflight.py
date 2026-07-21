#!/usr/bin/env python3
"""Preflight check for recall lifecycle default policy.

Use this with a recent `recall_policy_gate.json` before changing defaults or
cutting a release. It rejects raw lifecycle defaults when the benchmark gate
does not allow raw promotion.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from recall_pkg.lifecycle_policy import get_recall_signal_policy


def read_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_preflight(*, policy_gate: dict, target_policy: str) -> dict:
    target = (target_policy or "guarded").strip().lower()
    raw_allowed = bool(policy_gate.get("promotion", {}).get("raw_lifecycle_allowed", False))
    recommended = policy_gate.get("promotion", {}).get("recommended_default", "guarded")

    if target == "raw" and not raw_allowed:
        status = "reject"
        reason = "raw_lifecycle_not_allowed_by_policy_gate"
    elif target not in ("raw", "guarded"):
        status = "reject"
        reason = "unknown_target_policy"
    else:
        status = "accept"
        reason = "policy_allowed"

    return {
        "version": "1.0",
        "status": status,
        "reason": reason,
        "target_policy": target,
        "recommended_default": recommended,
        "raw_lifecycle_allowed": raw_allowed,
        "gate": policy_gate.get("gate"),
        "deltas": policy_gate.get("deltas", {}),
    }


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy-gate", required=True, help="path to recall_policy_gate.json")
    ap.add_argument(
        "--target-policy",
        default=None,
        help="raw or guarded; defaults to COMPASS_RECALL_SIGNAL_POLICY or runtime default",
    )
    ap.add_argument("--out", help="optional output JSON path")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    target_policy = args.target_policy or get_recall_signal_policy()
    out = build_preflight(policy_gate=read_json(Path(args.policy_gate)), target_policy=target_policy)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["status"] == "accept" else 2


if __name__ == "__main__":
    raise SystemExit(main())
