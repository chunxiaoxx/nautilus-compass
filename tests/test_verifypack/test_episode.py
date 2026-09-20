"""episode check kind(轨迹验证 · SPEC v0.3 §E)测试。

契约:帧数组 + 逐转移不变量(声明式,零新表达式语法)——
recomputed = {"transitions": N, "violations": {不变量名: 违规数}}。
"""
import json

import pytest

from tools.verifypack import checks, spec


@pytest.fixture()
def pack_dir(tmp_path):
    d = tmp_path / "pack"
    d.mkdir()
    (d / "pack.json").write_text('{"pack": "p1"}', encoding="utf-8")
    return d


def _write_frames(pack_dir, frames):
    p = pack_dir / "payload"
    p.mkdir(exist_ok=True)
    (p / "frames.json").write_text(json.dumps({"frames": frames}), encoding="utf-8")
    return "payload/frames.json#frames"


def _claim(value):
    return {"id": "E1", "level": "L1", "value": value,
            "checks": {"kind": "episode", "from": None}}


GOOD = [
    {"episode_id": "a", "t": 0.0, "x": 0.0, "held": True},
    {"episode_id": "a", "t": 1.0, "x": 0.1, "held": True},
    {"episode_id": "a", "t": 2.0, "x": 0.2, "held": True},
    {"episode_id": "b", "t": 0.0, "x": 5.0, "held": False},
    {"episode_id": "b", "t": 1.0, "x": 5.1, "held": False},
]

INV = [
    {"name": "dt_eq_1", "field": "t", "op": "incr_eq", "rhs": 1.0},
    {"name": "no_jump_x", "field": "x", "op": "abs_delta_le", "rhs": 0.15},
    {"name": "held_same_within", "field": "held", "op": "same"},
]


def test_episode_grouped_all_invariants_ok(pack_dir):
    ref = _write_frames(pack_dir, GOOD)
    chk = {"kind": "episode", "from": ref, "episode_by": "episode_id", "invariants": INV}
    r = checks.run_check({"pack": "p1"}, _claim({"transitions": 3, "violations": {"dt_eq_1": 0, "no_jump_x": 0, "held_same_within": 0}}), chk, pack_dir)
    assert r["ok"], r
    assert r["recomputed"] == {"transitions": 3,
                               "violations": {"dt_eq_1": 0, "no_jump_x": 0, "held_same_within": 0}}


def test_episode_jump_violates(pack_dir):
    frames = [dict(GOOD[0]), dict(GOOD[1]), dict(GOOD[2]), dict(GOOD[3]), dict(GOOD[4])]
    frames[2]["x"] = 9.9  # a 组内跳跃
    ref = _write_frames(pack_dir, frames)
    chk = {"kind": "episode", "from": ref, "episode_by": "episode_id", "invariants": INV}
    r = checks.run_check({"pack": "p1"},
                         _claim({"transitions": 3, "violations": {"dt_eq_1": 0, "no_jump_x": 1, "held_same_within": 0}}),
                         chk, pack_dir)
    assert not r["ok"]
    assert r["recomputed"]["violations"]["no_jump_x"] == 1


def test_episode_ungrouped_transitions_span_all(pack_dir):
    ref = _write_frames(pack_dir, GOOD)
    chk = {"kind": "episode", "from": ref, "invariants": [INV[0]]}
    # 不分组:t 连续跨 episode(a→b 处 t=2→0 回退)= 违规;转移数 4
    r = checks.run_check({"pack": "p1"},
                         _claim({"transitions": 4, "violations": {"dt_eq_1": 1}}), chk, pack_dir)
    assert not r["ok"]
    assert r["recomputed"]["transitions"] == 4


def test_episode_frame_level_const_op(pack_dir):
    frames = [dict(GOOD[0]), dict(GOOD[1]), dict(GOOD[2])]
    frames[1]["t"] = -1.0  # 帧级:t >= 0
    ref = _write_frames(pack_dir, frames)
    chk = {"kind": "episode", "from": ref,
           "invariants": [{"name": "t_nonneg", "field": "t", "op": "ge_const", "rhs": 0.0}]}
    r = checks.run_check({"pack": "p1"},
                         _claim({"transitions": 2, "violations": {"t_nonneg": 1}}), chk, pack_dir)
    assert not r["ok"]
    assert r["recomputed"]["violations"] == {"t_nonneg": 1}


def test_episode_missing_field_raises(pack_dir):
    frames = [{"episode_id": "a", "t": 0.0}, {"episode_id": "a", "t": 1.0}]  # 无 x
    ref = _write_frames(pack_dir, frames)
    chk = {"kind": "episode", "from": ref, "invariants": [INV[1]]}
    with pytest.raises(checks.CheckError):
        checks.run_check({"pack": "p1"}, _claim({"transitions": 1, "violations": {"no_jump_x": 0}}), chk, pack_dir)


def test_episode_single_frame_zero_transitions(pack_dir):
    ref = _write_frames(pack_dir, [GOOD[0]])
    chk = {"kind": "episode", "from": ref, "invariants": [INV[0]]}
    r = checks.run_check({"pack": "p1"},
                         _claim({"transitions": 0, "violations": {"dt_eq_1": 0}}), chk, pack_dir)
    assert r["ok"]


# ── spec 校验 ──

def test_spec_episode_validation():
    spec.validate_check({"kind": "episode", "from": "x#y",
                         "invariants": [{"field": "t", "op": "incr_ge", "rhs": 0}]})
    with pytest.raises(spec.SpecError):
        spec.validate_check({"kind": "episode", "from": "x#y", "invariants": []})
    with pytest.raises(spec.SpecError):
        spec.validate_check({"kind": "episode", "from": "x#y",
                             "invariants": [{"field": "t", "op": "teleport"}]})


def test_spec_episode_incr_needs_rhs():
    with pytest.raises(spec.SpecError):
        spec.validate_check({"kind": "episode", "from": "x#y",
                             "invariants": [{"field": "t", "op": "incr_eq"}]})
