"""纯逻辑单测 — services.swe_verify(path B correctness-binary verifier 核)。"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.swe_verify import (
    parse_pytest_summary, extract_failed_tests, swe_reward, rsi_improved, build_swe_memory,
    extract_failures_section)


_OUT_TRACEBACK = """\
.F
=========================== FAILURES ===========================
___________________ test_mathematica ___________________

    for e in d:
>       assert parse_mathematica(e) == sympify(d[e])
E       AssertionError: assert Cos*x/2 == Cos(x/2)
E        +  where Cos*x/2 = parse_mathematica('Cos(1/2 * x)')

sympy/parsing/tests/test_mathematica.py:74: AssertionError
=========================== warnings summary ===========================
some warning
=========================== short test summary info ===========================
FAILED sympy/parsing/tests/test_mathematica.py::test_mathematica - AssertionError
1 failed, 1 passed in 0.4s
"""


_OUT = """\
tests/test_a.py::test_one PASSED
tests/test_a.py::test_two FAILED
========== 3 passed, 2 failed, 1 error in 2.31s ==========
FAILED tests/test_a.py::test_two - AssertionError: expected 5 got 4
ERROR tests/test_b.py::test_setup - ImportError: no module named foo
"""


def test_parse_summary():
    s = parse_pytest_summary(_OUT)
    assert s == {"passed": 3, "failed": 2, "errored": 1, "parsed": True}


def test_parse_no_summary():
    s = parse_pytest_summary("Traceback... SyntaxError")
    assert s["parsed"] is False and s["passed"] == 0


def test_extract_failed():
    fails = extract_failed_tests(_OUT)
    names = [f["test"] for f in fails]
    assert "tests/test_a.py::test_two" in names
    assert "tests/test_b.py::test_setup" in names
    assert any("AssertionError" in f["reason"] for f in fails)


def test_reward_is_passed():
    assert swe_reward(parse_pytest_summary(_OUT)) == 3


def test_reward_none_when_unparsed():
    assert swe_reward(parse_pytest_summary("compile crash")) is None


def test_rsi_improved_discrete():
    assert rsi_improved(3, 5) is True      # 更多通过=改进(无噪声门)
    assert rsi_improved(5, 5) is False     # 持平不算
    assert rsi_improved(5, 3) is False     # 退步
    assert rsi_improved(None, 5) is False  # 无 baseline


def test_build_memory_grounded():
    mem = build_swe_memory("--- a/x.py\n+++ b/x.py", parse_pytest_summary(_OUT),
                           extract_failed_tests(_OUT))
    assert "passed: 3" in mem                       # 真实结果
    assert "tests/test_a.py::test_two" in mem        # 具体失败测试
    assert "AssertionError" in mem                   # 报错 grounded
    assert "improved patch" in mem                   # 改进指令


def test_extract_failures_section():
    # 抓 = FAILURES = 到 short test summary 之间的实际 traceback(去 warnings 尾）
    sec = extract_failures_section(_OUT_TRACEBACK)
    assert "test_mathematica" in sec
    assert "assert Cos*x/2 == Cos(x/2)" in sec        # 真实断言 expected vs got
    assert "parse_mathematica('Cos(1/2 * x)')" in sec  # 触发输入 grounded
    assert "warnings summary" not in sec               # warnings 尾被剔
    assert "short test summary" not in sec


def test_extract_failures_section_none_when_absent():
    assert extract_failures_section("1 passed in 0.1s") == ""


def test_build_memory_includes_traceback():
    mem = build_swe_memory("--- a/x.py\n+++ b/x.py", parse_pytest_summary(_OUT_TRACEBACK),
                           extract_failed_tests(_OUT_TRACEBACK),
                           traceback_text=extract_failures_section(_OUT_TRACEBACK))
    assert "assert Cos*x/2 == Cos(x/2)" in mem         # traceback 进了记忆
