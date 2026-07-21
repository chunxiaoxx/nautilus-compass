#!/usr/bin/env python3
"""TDD · release/default-policy preflight from recall policy gate."""
from __future__ import annotations

import json
import subprocess
import sys

from ops.recall_policy_preflight import build_preflight


def _gate(raw_allowed: bool, recommended: str = "guarded") -> dict:
    return {
        "gate": "block_raw_lifecycle_promotion" if not raw_allowed else "raw_lifecycle_candidate",
        "promotion": {
            "raw_lifecycle_allowed": raw_allowed,
            "recommended_default": recommended,
        },
        "deltas": {
            "raw": {"poi": -0.001 if not raw_allowed else 0.006, "tier": 0.0, "gemini": 0.0},
            "guarded": {"poi": 0.0, "tier": 0.0, "gemini": 0.0},
        },
    }


def test_preflight_blocks_raw_default_when_policy_gate_disallows_raw():
    out = build_preflight(policy_gate=_gate(raw_allowed=False), target_policy="raw")
    assert out["status"] == "reject"
    assert out["target_policy"] == "raw"
    assert out["reason"] == "raw_lifecycle_not_allowed_by_policy_gate"


def test_preflight_allows_guarded_default_when_raw_is_blocked():
    out = build_preflight(policy_gate=_gate(raw_allowed=False), target_policy="guarded")
    assert out["status"] == "accept"
    assert out["target_policy"] == "guarded"


def test_preflight_allows_raw_only_when_policy_gate_allows_raw():
    out = build_preflight(policy_gate=_gate(raw_allowed=True, recommended="raw"), target_policy="raw")
    assert out["status"] == "accept"
    assert out["target_policy"] == "raw"


def test_preflight_cli_runs_from_repo_root(tmp_path):
    gate_path = tmp_path / "gate.json"
    out_path = tmp_path / "preflight.json"
    gate_path.write_text(json.dumps(_gate(raw_allowed=False)), encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            "ops/recall_policy_preflight.py",
            "--policy-gate",
            str(gate_path),
            "--target-policy",
            "guarded",
            "--out",
            str(out_path),
        ],
        text=True,
        capture_output=True,
    )

    assert proc.returncode == 0, proc.stderr
    assert json.loads(out_path.read_text(encoding="utf-8"))["status"] == "accept"
