"""auto-verify planner 纯函数语义:只挑有产物、未终态、未超试的 verdict。"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.fde_auto_verify_runner import plan_jobs  # noqa: E402


def _mk(tmp_path, task_dir="taskA", traj="traj.json"):
    d = tmp_path / task_dir
    d.mkdir(exist_ok=True)
    (d / traj).write_text("{}", encoding="utf-8")
    return str(tmp_path)


def test_plan_selects_only_runnable(tmp_path):
    base = _mk(tmp_path)
    rows = [
        {"verdict_id": "v-ok", "artifacts": {"task_dir": "taskA",
                                             "trajectory_path": "traj.json"}},
        {"verdict_id": "v-no-artifacts", "artifacts": {}},                    # 无指针
        {"verdict_id": "v-missing-file", "artifacts": {"task_dir": "nope",
                                                       "trajectory_path": "x.json"}},
        {"verdict_id": "v-terminal", "artifacts": {"task_dir": "taskA",
                                                   "trajectory_path": "traj.json"}},
        {"verdict_id": "v-exhausted", "artifacts": {"task_dir": "taskA",
                                                    "trajectory_path": "traj.json"}},
    ]
    state = {
        "v-terminal": {"attempts": 1, "last_status": "NOT_REPRODUCIBLE"},
        "v-exhausted": {"attempts": 2, "last_status": "ERROR"},
    }
    jobs = plan_jobs(rows, base, state)
    assert [j["verdict_id"] for j in jobs] == ["v-ok"]
    assert jobs[0]["trajectory"] == "traj.json"
    assert jobs[0]["task_dir"].endswith("taskA")


def test_genopt_family_rejected_freeze_semantics(tmp_path, monkeypatch):
    """2026-08-23 冻结选项a: genopt-* task_uid 不再进 verify 队列。"""
    from services.fde_auto_verify_runner import plan_jobs
    task_dir = tmp_path / "t"; task_dir.mkdir()
    (task_dir / "traj.json").write_text("{}", encoding="utf-8")
    rows = [{
        "verdict_id": "v1", "task_uid": "genopt-bin-v3-x",
        "artifacts": {"task_dir": "t", "trajectory_path": "traj.json"},
    }, {
        "verdict_id": "v2", "task_uid": "g2b1:abc123",
        "artifacts": {"task_dir": "t", "trajectory_path": "traj.json"},
    }]
    jobs = plan_jobs(rows, str(tmp_path), {})
    assert [j["verdict_id"] for j in jobs] == ["v2"]
