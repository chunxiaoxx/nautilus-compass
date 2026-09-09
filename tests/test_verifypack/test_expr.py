"""受限表达式求值器与路径工具测试。"""
import pytest

from tools.verifypack import expr


ROWS = [
    {"name": "a", "frames_written": 100, "frames_decoded": 100, "rc": 0, "ratio": 0.99},
    {"name": "b", "frames_written": 50, "frames_decoded": 100, "rc": 0, "ratio": 0.99},
    {"name": "c", "frames_written": 30, "frames_decoded": 100, "rc": 1, "ratio": 0.5},
]


def test_sum_division():
    assert expr.eval_expr("sum(frames_written)", ROWS) == 180
    assert expr.eval_expr("sum(frames_written) / sum(frames_decoded)", ROWS) == pytest.approx(0.6)


def test_count_and_len():
    assert expr.eval_expr("count()", ROWS) == 3
    assert expr.eval_expr("len(name)", ROWS) == 3


def test_count_predicate():
    assert expr.eval_expr("count(rc == 0)", ROWS) == 2
    assert expr.eval_expr("count(ratio >= 0.9)", ROWS) == 2
    assert expr.eval_expr("count(name != 'a')", ROWS) == 2
    assert expr.eval_expr("count(rc == 0) / count()", ROWS) == pytest.approx(2 / 3)


def test_count_predicate_rejects_complex():
    with pytest.raises(expr.ExprError):
        expr.eval_expr("count(rc == 0 and ratio > 0)", ROWS)  # 链式比较拒绝
    with pytest.raises(expr.ExprError):
        expr.eval_expr("count(nosuch == 1)", ROWS)


def test_arithmetic_and_unary_minus():
    assert expr.eval_expr("sum(frames_written) * 2 - 20", ROWS) == 340
    assert expr.eval_expr("-sum(ratio)", ROWS) == pytest.approx(-2.48)


def test_round_min_max():
    assert expr.eval_expr("round(sum(ratio) / 3, 2)", ROWS) == 0.83
    assert expr.eval_expr("min(ratio)", ROWS) == 0.5
    assert expr.eval_expr("max(ratio)", ROWS) == 0.99


@pytest.mark.parametrize("bad", [
    "__import__('os').system('x')",
    "rows[0]",
    "obj.attr",
    "lambda: 1",
    "sum(frames_written) if True else 0",
    "open('x')",
    "sum(frames_written) + eval('1')",
    "",
    "1 +",
])
def test_rejects_non_whitelisted(bad):
    with pytest.raises(expr.ExprError):
        expr.eval_expr(bad, ROWS)


def test_unknown_field_rejected():
    with pytest.raises(expr.ExprError):
        expr.eval_expr("sum(no_such_field)", ROWS)


def test_empty_rows_rejected():
    with pytest.raises(expr.ExprError):
        expr.eval_expr("sum(x)", [])


def test_get_path():
    doc = {"a": {"b": {"c": [1, 2]}}}
    assert expr.get_path(doc, "a.b.c") == [1, 2]
    with pytest.raises(KeyError):
        expr.get_path(doc, "a.b.x")


def test_rows_to_map():
    m = expr.rows_to_map(ROWS, "name", "frames_written")
    assert m == {"a": 100, "b": 50, "c": 30}
    with pytest.raises(KeyError):
        expr.rows_to_map(ROWS, "nope", "ratio")
