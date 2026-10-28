"""Test check_docstring_preserve · closes handoff Gap 1 part 2 (docstring guard).

Module-level docstring (AST first string expression) byte-diff reject
unless task contains one of 9 escape keywords (5 EN + 4 中文).
"""
from pathlib import Path

from engine.checks import check_docstring_preserve


def _py(path: Path, docstring, body: str = "x = 1") -> None:
    """Write a .py file with module docstring and body."""
    if docstring is not None:
        path.write_text(f'"""{docstring}"""\n{body}\n', encoding="utf-8")
    else:
        path.write_text(f"{body}\n", encoding="utf-8")


def test_docstring_reject_rewrite(tmp_path):
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    _py(orig, "Original module description.")
    _py(new, "Rewritten module description.")
    r = check_docstring_preserve(str(orig), str(new), task="add helper to module")
    assert not r.passed, "docstring rewrite without keyword must reject"
    assert "docstring" in r.message.lower()


def test_docstring_pass_identical(tmp_path):
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    _py(orig, "Same docstring.")
    _py(new, "Same docstring.")
    r = check_docstring_preserve(str(orig), str(new), task="any task")
    assert r.passed, f"identical docstring must pass · {r.message}"


def test_docstring_allow_en_keyword(tmp_path):
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    _py(orig, "Old.")
    _py(new, "New.")
    r = check_docstring_preserve(str(orig), str(new), task="update docstring for clarity")
    assert r.passed, "EN keyword 'update docstring' must escape · pass"
    assert r.skipped


def test_docstring_allow_chinese_keyword(tmp_path):
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    _py(orig, "旧.")
    _py(new, "新.")
    r = check_docstring_preserve(str(orig), str(new), task="改 docstring 让 OSS 用户看懂")
    assert r.passed, "中文 keyword '改 docstring' must escape · pass"
    assert r.skipped


def test_docstring_new_file_skipped(tmp_path):
    new = tmp_path / "new.py"
    _py(new, "Whatever.")
    missing_orig = tmp_path / "does_not_exist.py"
    r = check_docstring_preserve(str(missing_orig), str(new), task="any task")
    assert r.skipped
    assert r.passed


def test_docstring_both_sides_empty_pass(tmp_path):
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    _py(orig, None)  # no docstring
    _py(new, None)
    r = check_docstring_preserve(str(orig), str(new), task="add helper")
    assert r.passed, "neither side has docstring · pass (skipped)"
    assert r.skipped
