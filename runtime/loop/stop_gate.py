#!/usr/bin/env python3
"""Shared read-only stop gate for Compass loop entry points.

The gate must run before a loop reads a queue, calls a model, writes a state
file, or sends through a channel. It only reads STOP and the known round state
files. A blocked gate returns a structured result and never mutates state.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


HARD_STOP_ROUND = 200


def inspect_stop_gate(root: Path | None = None) -> dict[str, Any]:
    """Return the shared loop decision without changing any file."""
    repo = (root or Path(__file__).resolve().parents[2]).resolve()
    loop_dir = repo / "runtime" / "loop"
    stop_file = loop_dir / "STOP"
    reasons: list[str] = []
    states: list[dict[str, Any]] = []

    if stop_file.exists():
        reasons.append("runtime/loop/STOP exists")

    state_paths = (
        ("canonical", loop_dir / "state.json"),
        ("local", loop_dir / "local_state.json"),
        ("production", repo / "runtime" / "production_loop" / "state.json"),
    )
    for name, path in state_paths:
        record: dict[str, Any] = {"name": name, "path": str(path), "exists": path.exists()}
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                round_value = int(payload.get("round", 0))
                record["round"] = round_value
                if round_value > HARD_STOP_ROUND:
                    reasons.append(f"{name} round {round_value} > {HARD_STOP_ROUND}")
            except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
                record["error"] = f"{type(exc).__name__}: {exc}"
                reasons.append(f"{name} state unreadable")
        states.append(record)

    return {
        "blocked": bool(reasons),
        "hard_stop_round": HARD_STOP_ROUND,
        "stop_file": str(stop_file),
        "reasons": reasons,
        "states": states,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read Compass loop stop state")
    parser.add_argument("--check", action="store_true", help="return success only when the gate is clear")
    parser.add_argument("--json", action="store_true", help="print the structured decision")
    args = parser.parse_args()
    decision = inspect_stop_gate()
    if args.json or not args.check:
        print(json.dumps(decision, ensure_ascii=False, indent=2))
    if args.check:
        return 10 if decision["blocked"] else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
