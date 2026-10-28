"""Tests for engine.text_utils · D1 cycle 17 regression coverage."""
from engine.text_utils import truncate


def test_truncate_no_change_when_short():
    assert truncate("hi", max_len=10) == "hi"


def test_truncate_basic():
    assert truncate("hello world", max_len=8) == "hello..."


def test_truncate_max_len_equals_ellipsis_len():
    assert truncate("hello", max_len=3) == "..."


def test_truncate_max_len_less_than_ellipsis_len_regression():
    result = truncate("hello", max_len=2)
    assert len(result) <= 2, f"expected len<=2, got {len(result)}: {result!r}"
    assert result == ".."


def test_truncate_max_len_zero_regression():
    result = truncate("hello", max_len=0)
    assert len(result) == 0, f"expected empty, got {len(result)}: {result!r}"


def test_truncate_max_len_one_regression():
    result = truncate("hello", max_len=1)
    assert len(result) <= 1
    assert result == "."


def test_truncate_custom_ellipsis():
    assert truncate("hello world", max_len=8, ellipsis="…") == "hello w…"


def test_truncate_equal_to_max_len():
    assert truncate("hello", max_len=5) == "hello"
