"""TDD for ale_bench/ale_eval.py · 注入 fake session·无需 live ale_bench。

live 标定(真 public_eval 出分 + rejected 哨兵)走 T4·见 docs/plans Phase1 Task1。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ale_bench"))
import ale_eval  # noqa: E402


class _FakeResult:
    def __init__(self, score):
        self.overall_absolute_score = score


class _FakeSession:
    def __init__(self, score):
        self._score = score
        self.closed = False
        self.eval_calls = 0

    def public_eval(self, code, language, **kw):
        self.eval_calls += 1
        self.last_judge_version = kw.get("judge_version")
        return _FakeResult(self._score)

    def close(self):
        self.closed = True


def _start_returning(score, sink=None):
    def _start(problem_id, **kw):
        s = _FakeSession(score)
        if sink is not None:
            sink.append(s)
        return s

    return _start


def test_eval_fn_valid_score_maps_to_reward():
    out = eval_fn_out = ale_eval.eval_fn("code", "ahc001", start_fn=_start_returning(123456.0))
    assert eval_fn_out["reward"] == 123456.0
    assert "123456" in out["feedback"]
    assert "ahc001" in out["feedback"]


def test_eval_fn_rejected_zero_score():
    out = ale_eval.eval_fn("bad", "ahc001", start_fn=_start_returning(0.0))
    assert out["reward"] == ale_eval.REJECTED_REWARD == 0.0
    assert "rejected" in out["feedback"].lower()


def test_eval_fn_negative_score_is_rejected():
    out = ale_eval.eval_fn("re", "ahc003", start_fn=_start_returning(-1.0))
    assert out["reward"] == 0.0
    assert "rejected" in out["feedback"].lower()


def test_deterministic_same_code_same_reward():
    f = _start_returning(999.0)
    a = ale_eval.eval_fn("c", "ahc002", start_fn=f)
    b = ale_eval.eval_fn("c", "ahc002", start_fn=f)
    assert a == b


def test_higher_score_higher_reward():
    lo = ale_eval.eval_fn("c", "ahc001", start_fn=_start_returning(100.0))["reward"]
    hi = ale_eval.eval_fn("c", "ahc001", start_fn=_start_returning(500.0))["reward"]
    assert hi > lo


def test_session_always_closed():
    sink = []
    ale_eval.eval_fn("c", "ahc001", start_fn=_start_returning(50.0, sink=sink))
    assert sink and sink[0].closed is True


def test_score_solution_returns_raw():
    r = ale_eval.score_solution("c", "ahc001", start_fn=_start_returning(42.0))
    assert r["score"] == 42.0
    assert r["rejected"] is False
    assert r["raw"].overall_absolute_score == 42.0


def test_task_family():
    assert ale_eval.task_family("ahc001") == "ale_ahc_ahc001"
    assert ale_eval.task_family("ahc007") == "ale_ahc_ahc007"


def test_judge_version_defaults_to_built_image():
    # live bug guard: public_eval default judge_version=202301 → pulls nonexistent
    # ale-bench:cpp23-202301. Must pass 202510 (the built image).
    sink = []
    ale_eval.eval_fn("c", "ahc001", start_fn=_start_returning(50.0, sink=sink))
    assert sink[0].last_judge_version == "202510"
    assert ale_eval.DEFAULT_JUDGE_VERSION == "202510"
