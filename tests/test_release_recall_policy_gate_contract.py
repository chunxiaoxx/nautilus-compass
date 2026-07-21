#!/usr/bin/env python3
"""Release contract for lifecycle recall default policy.

The heavy recall benchmark runs on the developer machine because it needs local
memory and model cache. Release CI consumes the resulting policy-gate evidence
and verifies that the default policy remains allowed.
"""
from __future__ import annotations

import json
from pathlib import Path

from ops.recall_policy_preflight import build_preflight


ROOT = Path(__file__).resolve().parent.parent
POLICY_GATE = ROOT / "docs" / "evidence" / "recall_policy_gate_current.json"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"


def test_current_policy_gate_evidence_allows_flat_and_blocks_lifecycle_defaults():
    gate = json.loads(POLICY_GATE.read_text(encoding="utf-8"))

    flat = build_preflight(policy_gate=gate, target_policy="flat")
    guarded = build_preflight(policy_gate=gate, target_policy="guarded")
    raw = build_preflight(policy_gate=gate, target_policy="raw")

    assert gate["source"]["profile_dir"] == ".cache/bench-profile-20260721-080758-(default in daemon.py)"
    assert gate["source"]["commit"] == "fb1321a"
    assert flat["status"] == "accept"
    assert guarded["status"] == "reject"
    assert raw["status"] == "reject"
    assert raw["reason"] == "raw_lifecycle_not_allowed_by_policy_gate"


def test_release_workflow_runs_recall_policy_preflight():
    text = RELEASE_WORKFLOW.read_text(encoding="utf-8")
    assert "Recall lifecycle policy preflight" in text
    assert "ops/recall_policy_preflight.py" in text
    assert "docs/evidence/recall_policy_gate_current.json" in text
    assert "--target-policy flat" in text

