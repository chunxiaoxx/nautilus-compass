"""TDD tests for engine.checks.check_runtime · cycle 6 subprocess runtime smoke.

LIMIT documented: runtime check invokes `python <file>` with NO args. It catches
import-time errors and top-level runtime errors, but NOT bugs that only manifest
when `main()` is called with specific arguments (e.g. cycle 5 buggy __main__.py
that exits cleanly with "Usage" message and only crashes when a task arg is passed).
"""
from pathlib import Path

import pytest

from engine.checks import check_runtime, run_pipeline


def test_runtime_passes_clean_file(tmp_path: Path):
    f = tmp_path / "clean.py"
    f.write_text("x = 1\ny = x + 2\n")
    res = check_runtime(str(f))
    assert res.passed is True
    assert res.skipped is False


def test_runtime_passes_file_with_main_guard_and_no_args(tmp_path: Path):
    """__main__.py-style file that exits 1 with Usage when no args · still 'passes'
    runtime check because no traceback was emitted."""
    f = tmp_path / "entry.py"
    f.write_text(
        "import sys\n"
        "def main():\n"
        "    if len(sys.argv) < 2:\n"
        "        print('Usage: ...', file=sys.stderr)\n"
        "        return 1\n"
        "    return 0\n"
        "if __name__ == '__main__':\n"
        "    sys.exit(main())\n"
    )
    res = check_runtime(str(f))
    assert res.passed is True  # exit 1 without traceback is OK


def test_runtime_fails_on_top_level_traceback(tmp_path: Path):
    f = tmp_path / "boom.py"
    f.write_text(
        "x = 1 / 0\n"  # ZeroDivisionError at import time
    )
    res = check_runtime(str(f))
    assert res.passed is False
    assert "ZeroDivisionError" in res.message or "Traceback" in res.message


def test_runtime_fails_on_import_error(tmp_path: Path):
    f = tmp_path / "bad_import.py"
    f.write_text("import this_module_definitely_does_not_exist_xyz999\n")
    res = check_runtime(str(f))
    assert res.passed is False
    assert "ModuleNotFoundError" in res.message or "this_module_definitely_does_not_exist_xyz999" in res.message


def test_runtime_skips_non_python(tmp_path: Path):
    f = tmp_path / "doc.md"
    f.write_text("# hi\n")
    res = check_runtime(str(f))
    assert res.skipped is True
    assert res.passed is True


def test_runtime_respects_timeout(tmp_path: Path):
    f = tmp_path / "spin.py"
    f.write_text(
        "import time\n"
        "time.sleep(30)\n"  # exceeds 2s timeout
    )
    res = check_runtime(str(f), timeout=2)
    assert res.passed is False
    assert "timeout" in res.message.lower()


# ---------- documented LIMIT ----------

def test_runtime_does_NOT_catch_main_only_bug(tmp_path: Path):
    """Regression-as-documentation · cycle 5 bug class · runtime can't catch
    bugs gated behind argv parsing when called without args."""
    f = tmp_path / "cycle5_repro.py"
    f.write_text(
        "import sys\n"
        "def main():\n"
        "    if len(sys.argv) < 2:\n"
        "        return 1\n"
        "    # Bug: undefined name - would crash when args provided\n"
        "    return undefined_name + 1\n"
        "if __name__ == '__main__':\n"
        "    sys.exit(main())\n"
    )
    res = check_runtime(str(f))
    # check_runtime invokes with NO args · main() exits cleanly with 1
    # The undefined_name reference is NEVER evaluated · runtime cannot see it
    assert res.passed is True  # this is the documented limit


# ---------- pipeline integration ----------

def test_run_pipeline_excludes_runtime_by_default(tmp_path: Path):
    f = tmp_path / "x.py"
    f.write_text("x = 1\n")
    result = run_pipeline([str(f)])
    names = {c["name"] for c in result["checks"]}
    assert "runtime" not in names  # opt-in only


def test_run_pipeline_includes_runtime_when_enabled(tmp_path: Path):
    f = tmp_path / "x.py"
    f.write_text("x = 1\n")
    result = run_pipeline([str(f)], run_runtime=True)
    names = {c["name"] for c in result["checks"]}
    assert "runtime" in names


def test_run_pipeline_runtime_failure_propagates(tmp_path: Path):
    f = tmp_path / "boom.py"
    f.write_text("raise RuntimeError('intentional')\n")
    result = run_pipeline([str(f)], run_runtime=True)
    assert result["passed"] is False
    runtime_check = next(c for c in result["checks"] if c["name"] == "runtime")
    assert runtime_check["passed"] is False
