"""Test check_line_count · closes handoff Gap 1 part 1 (line count guard).

Bounds:
    shrink_floor = 0.85 * orig (always strict)
    growth_ceiling = 2.0 * orig default · 4.0 when allow_additions=True
"""
from pathlib import Path

from engine.checks import check_line_count


def _write(path: Path, n_lines: int) -> None:
    """Write a .py file with n_lines content lines."""
    path.write_text("\n".join(f"x = {i}" for i in range(n_lines)) + "\n", encoding="utf-8")


def test_line_count_reject_shrink(tmp_path):
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    _write(orig, 200)
    _write(new, 90)  # ratio 0.45
    r = check_line_count(str(orig), str(new))
    assert not r.passed, "shrink ratio 0.45 < 0.85 floor must reject"
    assert "shrink" in r.message.lower() or "0.45" in r.message


def test_line_count_pass_minor_jitter(tmp_path):
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    _write(orig, 100)
    _write(new, 95)  # ratio 0.95 > 0.85 floor
    r = check_line_count(str(orig), str(new))
    assert r.passed, f"minor jitter 0.95 must pass · {r.message}"


def test_line_count_reject_growth_default(tmp_path):
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    _write(orig, 50)
    _write(new, 150)  # ratio 3.0 > 2.0 default ceiling
    r = check_line_count(str(orig), str(new))
    assert not r.passed, "default growth 3.0 > 2.0 ceiling must reject"


def test_line_count_allow_additions_relaxes_growth(tmp_path):
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    _write(orig, 50)
    _write(new, 150)  # ratio 3.0 < 4.0 allow_add ceiling
    r = check_line_count(str(orig), str(new), allow_additions=True)
    assert r.passed, f"allow_additions ceiling 4.0 must pass ratio 3.0 · {r.message}"


def test_line_count_allow_additions_still_blocks_shrink(tmp_path):
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    _write(orig, 100)
    _write(new, 60)  # ratio 0.60 < 0.85 floor
    r = check_line_count(str(orig), str(new), allow_additions=True)
    assert not r.passed, "shrink 0.60 < 0.85 floor must reject even with allow_additions"


def test_line_count_new_file_skipped(tmp_path):
    new = tmp_path / "new.py"
    _write(new, 50)
    missing_orig = tmp_path / "does_not_exist.py"
    r = check_line_count(str(missing_orig), str(new))
    assert r.skipped, "no original on disk → skipped"
    assert r.passed, "skipped implies passed=True"
