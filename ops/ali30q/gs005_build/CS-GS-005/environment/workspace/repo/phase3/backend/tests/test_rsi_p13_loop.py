"""纯逻辑单测 — scripts.rsi_p13_loop（fast1 判据/选优/记忆抽取）。"""
import sys, os
_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BACKEND)
sys.path.insert(0, os.path.join(_BACKEND, "scripts"))
from rsi_p13_loop import fast1_speedup, raw_speedup, select_best, build_memory, rsi_above_noise


def test_rsi_within_noise_not_proven():
    assert rsi_above_noise(180.0, 180.98) is False   # 0.54% < 1% 门 = 假阳性挡住


def test_rsi_above_noise_proven():
    assert rsi_above_noise(1.0, 1.5) is True          # 50% > 门


def test_rsi_none_not_proven():
    assert rsi_above_noise(None, 180.0) is False
    assert rsi_above_noise(180.0, None) is False


def _ok(su):
    return {"speedup_vs_eager": su, "eval": {"correctness": True},
            "strict_recheck": {"correctness": True}, "ref_time": {"mean": 200.0}}


def test_fast1_in_window():
    assert fast1_speedup(_ok(1.03)) == 1.03


def test_fast1_rejects_slow():
    assert fast1_speedup(_ok(0.73)) is None  # su<=1 非 fast1


def test_fast1_rejects_gated_too_fast():
    assert fast1_speedup(_ok(2.5)) is None  # >2x G2 洗门


def test_fast1_rejects_incorrect():
    r = _ok(1.03); r["eval"]["correctness"] = False
    assert fast1_speedup(r) is None


def test_fast1_rejects_strict_fail():
    r = _ok(1.03); r["strict_recheck"]["correctness"] = False
    assert fast1_speedup(r) is None


def test_fast1_rejects_error():
    assert fast1_speedup({"error": "scp_fail"}) is None


def test_raw_keeps_slow_correct():
    assert raw_speedup(_ok(0.40)) == 0.40   # correct-but-slow 保留(改进梯度起点)


def test_raw_keeps_uncapped_fast():
    assert raw_speedup(_ok(182.7)) == 182.7  # >2× 不 cap(去 fast1 窗口)


def test_raw_rejects_incorrect():
    r = _ok(50.0); r["eval"]["correctness"] = False
    assert raw_speedup(r) is None


def test_select_best_raw_reward():
    recs = [{"idx": 0, "code": "a", "result": _ok(0.40)},
            {"idx": 1, "code": "b", "result": _ok(1.80)}]
    assert select_best(recs, raw_speedup)["idx"] == 1


def test_select_best_picks_max_fast1():
    recs = [{"idx": 0, "code": "a", "result": _ok(1.02)},
            {"idx": 1, "code": "b", "result": _ok(1.05)},
            {"idx": 2, "code": "c", "result": _ok(0.7)}]
    best = select_best(recs)
    assert best["idx"] == 1


def test_select_best_none_when_no_fast1():
    recs = [{"idx": 0, "code": "a", "result": _ok(0.7)},
            {"idx": 1, "code": "b", "result": {"error": "x"}}]
    assert select_best(recs) is None


def test_build_memory_is_grounded():
    best = {"idx": 0, "code": "import torch  # ModelNew", "result": _ok(1.0309)}
    mem = build_memory(best)
    assert "1.0309" in mem           # 实测 speedup
    assert "200 ms" in mem           # ref 时间事实
    assert "ModelNew" in mem         # 源码 exemplar
    assert "strict 1e-3" in mem      # correctness 门


def test_build_memory_improve_vs_reproduce():
    best = {"idx": 0, "code": "x  # ModelNew", "result": _ok(1.0309)}
    improve = build_memory(best, reproduce=False)
    repro = build_memory(best, reproduce=True)
    assert "higher speedup" in improve         # 改进框架
    assert "Reproduce this verified kernel" in repro  # 复现框架
    assert "Correctness is paramount" in repro
