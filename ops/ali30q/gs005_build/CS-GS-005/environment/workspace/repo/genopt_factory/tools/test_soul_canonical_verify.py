"""soul_canonical_verify 第二刀 · 防橡皮图章语义测试。

核心契约:轨迹无完整解 = 拒;sha 不符 = 拒;复现分数不匹配 = 拒;
只有独立重跑 verifier 复现一致才允许 PATCH external-verify。
"""
from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from soul_canonical_verify import (  # noqa: E402
    NotReproducible,
    load_best_solution,
    verify,
)

# 一个超过 MIN_FULL_SOURCE_LEN(500)的"完整解"。
FULL_CODE = (
    "def solve_instance(instance):\n"
    "    return {'starts': [[0] * len(j) for j in instance['jobs']]}\n"
    + "# padding line to exceed the truncation-guard threshold\n" * 12
)

FAKE_EVALUATE = '''\
import argparse, json, os
ap = argparse.ArgumentParser()
ap.add_argument("--benchmark-dir", required=True)
ap.add_argument("--candidate", required=True)
ap.add_argument("--baseline")
a = ap.parse_args()
with open(os.path.join(a.benchmark_dir, "data", "fixed_score.txt"), encoding="utf-8") as f:
    s = float(f.read().strip())
with open("metrics.json", "w", encoding="utf-8") as f:
    json.dump({"combined_score": s, "valid": 1}, f)
'''


def make_task_dir(tmp_path, fixed_score):
    task = tmp_path / "task"
    (task / "verification").mkdir(parents=True)
    (task / "baseline").mkdir()
    (task / "data").mkdir()
    (task / "verification" / "evaluate.py").write_text(FAKE_EVALUATE, encoding="utf-8")
    (task / "baseline" / "init.py").write_text("# dummy baseline\n", encoding="utf-8")
    (task / "data" / "fixed_score.txt").write_text(str(fixed_score), encoding="utf-8")
    return str(task)


def make_traj(best_score=93.1034, best_round_source=None, best_solution_sha256=None,
              rounds=None):
    return {
        "model": "gpt-5.5",
        "n": 3,
        "seed_score": 24.6755,
        "best_score": best_score,
        "best_round_source": best_round_source,
        "best_solution_sha256": best_solution_sha256,
        "rounds": rounds or [],
    }


def test_preview_only_trajectory_rejected():
    """160 字符 docstring 预览(H800 旧轨迹)必须被拒——绝不 fallback 到 preview。"""
    traj = make_traj(
        best_round_source='"""Deterministic heuristic Job-Shop solver."""'[:160],
        rounds=[{"round": 1, "metrics": {"combined_score": 93.1034, "valid": 1},
                 "source_preview": "x" * 160}],
    )
    with pytest.raises(NotReproducible):
        load_best_solution(traj)


def test_full_source_reproduced_match(tmp_path):
    task_dir = make_task_dir(tmp_path, 93.1034)
    traj = make_traj(best_round_source=FULL_CODE)
    result = verify(task_dir, traj, tolerance=0.01)
    assert result["status"] == "MATCH"
    assert abs(result["reproduced"] - 93.1034) < 1e-9
    assert result["claimed"] == 93.1034


def test_score_mismatch_rejected(tmp_path):
    """复现分数偏离 claimed 超容差 → MISMATCH,不允许 PATCH。"""
    task_dir = make_task_dir(tmp_path, 88.0)
    traj = make_traj(best_round_source=FULL_CODE, best_score=93.1034)
    result = verify(task_dir, traj, tolerance=0.01)
    assert result["status"] == "MISMATCH"


def test_sha256_mismatch_rejected():
    traj = make_traj(best_round_source=FULL_CODE, best_solution_sha256="0" * 64)
    with pytest.raises(NotReproducible):
        load_best_solution(traj)


def test_gapclosed_format_candidate_code_supported():
    """gapclosed_runner.py 格式:rounds[].candidate_code + rounds[].score。"""
    traj = {
        "model": "gpt-5.5",
        "best_score": 93.1034,
        "rounds": [
            {"round": 1, "score": 60.0, "candidate_code": "short"},
            {"round": 2, "score": 93.1034, "candidate_code": FULL_CODE},
        ],
    }
    code, claimed = load_best_solution(traj)
    assert code == FULL_CODE
    assert claimed == 93.1034
