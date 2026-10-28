"""Tests for engine.pytest_runner."""
from pathlib import Path

from engine.pytest_runner import _resolve_test_paths, run_pytest_for_changed


def _make_pkg_with_passing_test(tmp_path: Path) -> Path:
    """Create pkg/foo.py · pkg/tests/test_foo.py (passing) at tmp_path."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "foo.py").write_text("def add(a, b): return a + b\n")
    tests_dir = pkg / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_foo.py").write_text(
        "import sys\nsys.path.insert(0, '.')\n"
        "from pkg.foo import add\n"
        "def test_add(): assert add(1, 2) == 3\n"
    )
    return tmp_path


def _make_pkg_with_failing_test(tmp_path: Path) -> Path:
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "foo.py").write_text("def add(a, b): return a + b\n")
    tests_dir = pkg / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_foo.py").write_text(
        "import sys\nsys.path.insert(0, '.')\n"
        "from pkg.foo import add\n"
        "def test_wrong(): assert add(1, 2) == 99\n"
    )
    return tmp_path


def test_run_pytest_pass(tmp_path):
    base = _make_pkg_with_passing_test(tmp_path)
    assert run_pytest_for_changed(base, ["pkg/foo.py"]) is True


def test_run_pytest_fail(tmp_path):
    base = _make_pkg_with_failing_test(tmp_path)
    assert run_pytest_for_changed(base, ["pkg/foo.py"]) is False


def test_run_pytest_no_test_file_returns_none(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "foo.py").write_text("def add(a, b): return a + b\n")
    # no tests/ dir → signal unavailable
    assert run_pytest_for_changed(tmp_path, ["pkg/foo.py"]) is None


def test_resolve_skips_path_escape(tmp_path):
    # Caller-supplied path that escapes base → silently skipped (not in tests list)
    assert _resolve_test_paths(tmp_path, ["../../../etc/passwd"]) == []


def test_run_pytest_empty_paths_returns_none(tmp_path):
    assert run_pytest_for_changed(tmp_path, []) is None
