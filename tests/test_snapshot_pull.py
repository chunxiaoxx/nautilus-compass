"""TDD for ops/snapshot_pull.py — T4 pulls PoI credit snapshot (Phase 0 Task 3)."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ops"))

import snapshot_pull as SP  # noqa: E402


def test_pull_builds_scp_command(tmp_path):
    calls = []
    # runner returns nonzero so no os.replace happens — we only inspect the command
    SP.pull_snapshot("ubuntu@cpu", "/var/lib/compass/poi/poi_credit_snapshot.json",
                     str(tmp_path / "local_snap.json"),
                     runner=lambda c: calls.append(c) or 1)
    cmd = calls[0]
    assert cmd[0] == "scp"
    joined = " ".join(cmd)
    assert "ubuntu@cpu:/var/lib/compass/poi/poi_credit_snapshot.json" in joined
    # atomic: scp lands on a .tmp sibling, not the live path
    assert joined.rstrip().endswith(".tmp")


def test_pull_atomic_replace_on_success(tmp_path):
    live = tmp_path / "snap.json"
    live.write_text('{"old": 1}', encoding="utf-8")

    def runner(cmd):
        # simulate scp writing the .tmp destination
        dst = cmd[-1]
        with open(dst, "w", encoding="utf-8") as f:
            f.write('{"new_key": 0.5}')
        return 0

    rc = SP.pull_snapshot("ubuntu@cpu", "/remote/snap.json", str(live), runner=runner)
    assert rc == 0
    assert json.loads(live.read_text(encoding="utf-8")) == {"new_key": 0.5}
    assert not (tmp_path / "snap.json.tmp").exists()  # tmp cleaned up


def test_pull_keeps_old_on_failure(tmp_path):
    live = tmp_path / "snap.json"
    live.write_text('{"old": 1}', encoding="utf-8")
    rc = SP.pull_snapshot("ubuntu@cpu", "/remote/snap.json", str(live),
                          runner=lambda c: 1)  # scp fails
    assert rc != 0
    assert json.loads(live.read_text(encoding="utf-8")) == {"old": 1}  # untouched


def test_boost_can_load_pulled_snapshot(tmp_path):
    """Round-trip: a pulled snapshot is valid JSON the v14 boost can read."""
    live = tmp_path / "snap.json"

    def runner(cmd):
        with open(cmd[-1], "w", encoding="utf-8") as f:
            f.write('{"proj/mem-a.md": 1.5, "proj/mem-b.md": -0.5}')
        return 0

    SP.pull_snapshot("ubuntu@cpu", "/remote/snap.json", str(live), runner=runner)
    credits = SP.load_snapshot(str(live))
    assert credits["proj/mem-a.md"] == 1.5


def test_load_missing_returns_empty(tmp_path):
    assert SP.load_snapshot(str(tmp_path / "nope.json")) == {}
